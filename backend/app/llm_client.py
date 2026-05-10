"""
Unified LLM client for NVIDIA NIM and local Ollama inference.
Selects provider at runtime based on environment variables.
Implements:
  - asyncio.Semaphore(5) for concurrency control
  - Exponential backoff on HTTP 429 (3s, 9s, 27s)
  - Retry up to 3× on HTTP 5xx / timeout
  - Output parsing: strip whitespace → strip markdown fences → json.loads → json_repair
  - Image encoding: base64 JPEG at 85% quality
Per PRD §13 and §14.
"""

import asyncio
import base64
import io
import json
import logging
import re
from typing import Optional

import httpx
import json_repair
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


class ExtractionParseError(Exception):
    """Raised when LLM output cannot be parsed as valid JSON after all recovery attempts."""

    def __init__(self, raw_output: str, message: str = "Failed to parse LLM output"):
        self.raw_output = raw_output
        super().__init__(message)


# --- System Prompt (verbatim from PRD §13) ---
SYSTEM_PROMPT = """You are a precise accounting data extraction assistant. Your sole task is to \
extract structured financial data from receipt images and return it as valid JSON.

Rules:
1. Return ONLY a JSON object. Do not include markdown code fences, explanations, \
or any text outside the JSON object.
2. Never invent or hallucinate data. If a field cannot be determined from the \
image, set it to null.
3. Never include full payment card numbers in your output. If a card number \
appears on the receipt, extract only the last four digits as a string \
(e.g., "last4": "4321") and omit the rest.
4. All monetary amounts must be numeric values (not strings), rounded to two \
decimal places.
5. Dates must be in ISO 8601 format (YYYY-MM-DD).
6. Currency must be a valid ISO 4217 three-letter code. Default to "USD" if \
the currency cannot be determined.
7. Assign a confidence score (float, 0.0 to 1.0) for each extracted field in \
the confidence_scores object. Use 0.0 for null fields.
8. For payment_method, use exactly one of: "Cash", "Card", "Check", "Split", \
or null if unknown.

Output schema:
{
  "vendor_name": string | null,
  "date": string | null,
  "currency": string,
  "subtotal": number | null,
  "tax_amount": number | null,
  "tip_amount": number | null,
  "total_amount": number | null,
  "payment_method": "Cash" | "Card" | "Check" | "Split" | null,
  "line_items": [
    {
      "description": string,
      "quantity": number,
      "unit_price": number,
      "line_total": number
    }
  ],
  "expense_category": string | null,
  "confidence_scores": {
    "vendor_name": number,
    "date": number,
    "total_amount": number,
    "subtotal": number,
    "tax_amount": number,
    "line_items": number
  }
}"""

USER_PROMPT = """Extract all financial data from the attached receipt image according to the \
schema in your instructions. If this is a handwritten receipt or the image \
quality is poor, set confidence scores accordingly."""

# Regex to strip markdown code fences from LLM output
MARKDOWN_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```")

# Backoff delays for rate limiting (seconds)
BACKOFF_DELAYS = [3, 9, 27]


# Max base64-encoded payload size for NVIDIA NIM inline images (~180KB encoded ≈ 120KB raw)
MAX_IMAGE_BYTES = 120_000


def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Re-encode image to JPEG and return base64 string.
    Progressively reduces quality and resolution to stay under
    NVIDIA NIM's inline base64 size limit (~180KB encoded).
    Handles any image format supported by Pillow.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA to RGB for JPEG compatibility
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    # First try at 85% quality
    for quality in (85, 70, 50, 35):
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        raw = buffer.getvalue()
        if len(raw) <= MAX_IMAGE_BYTES:
            return base64.b64encode(raw).decode("utf-8")

    # Still too large — downscale the image and retry
    max_dim = 1024
    while max_dim >= 256:
        resized = img.copy()
        resized.thumbnail((max_dim, max_dim), Image.LANCZOS)
        for quality in (70, 50, 35):
            buffer = io.BytesIO()
            resized.save(buffer, format="JPEG", quality=quality)
            raw = buffer.getvalue()
            if len(raw) <= MAX_IMAGE_BYTES:
                logger.info(
                    f"Image resized to {resized.size} at quality={quality} "
                    f"({len(raw)} bytes) to fit NIM inline limit"
                )
                return base64.b64encode(raw).decode("utf-8")
        max_dim //= 2

    # Last resort — return whatever we have
    buffer = io.BytesIO()
    img.thumbnail((512, 512), Image.LANCZOS)
    img.save(buffer, format="JPEG", quality=30)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def parse_llm_output(raw_output: str) -> dict:
    """
    Parse raw LLM output to JSON dict using the PRD §13 pipeline:
    1. Strip whitespace
    2. Strip markdown code fences
    3. json.loads()
    4. On fail: json_repair.repair() → retry json.loads()
    5. On second fail: raise ExtractionParseError
    """
    # Step 1: Strip whitespace
    text = raw_output.strip()

    # Step 2: Strip markdown code fences
    fence_match = MARKDOWN_FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Step 3: Try json.loads()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Step 4: Try json_repair
    try:
        repaired = json_repair.repair_json(text, return_objects=False)
        return json.loads(repaired)
    except (json.JSONDecodeError, Exception):
        pass

    # Step 5: Raise error
    raise ExtractionParseError(
        raw_output=raw_output,
        message=f"Failed to parse LLM output after json_repair. Raw length: {len(raw_output)}",
    )


class LLMClient:
    """
    Unified client for NVIDIA NIM and local Ollama inference.
    Selects provider at runtime based on environment variables.
    """

    def __init__(self):
        self.nvidia_key = settings.nvidia_nim_api_key
        self.ollama_host = settings.ollama_host
        self.model = settings.llm_model
        self.ollama_model = settings.ollama_model
        # Cap concurrent in-flight requests to respect free-tier limits
        self._semaphore = asyncio.Semaphore(5)
        self._queue_count = 0

    @property
    def provider(self) -> str:
        return "ollama" if self.ollama_host else "nvidia_nim"

    @property
    def queue_position(self) -> int:
        return self._queue_count

    async def extract(self, image_bytes: bytes) -> dict:
        """
        Extract receipt data from an image.
        Returns parsed JSON dict from LLM output.
        Raises ExtractionParseError if output cannot be parsed.
        """
        self._queue_count += 1
        try:
            async with self._semaphore:
                if self.ollama_host:
                    raw_output = await self._call_ollama(image_bytes)
                else:
                    raw_output = await self._call_nvidia(image_bytes)
                return parse_llm_output(raw_output)
        finally:
            self._queue_count -= 1

    async def extract_raw(self, image_bytes: bytes) -> str:
        """Extract and return raw LLM output string (for debugging)."""
        self._queue_count += 1
        try:
            async with self._semaphore:
                if self.ollama_host:
                    return await self._call_ollama(image_bytes)
                else:
                    return await self._call_nvidia(image_bytes)
        finally:
            self._queue_count -= 1

    async def _call_nvidia(self, image_bytes: bytes) -> str:
        """Call NVIDIA NIM API with exponential backoff on 429."""
        b64 = encode_image_to_base64(image_bytes)
        # Use the simplified string with <img> tag for Phi-4 Multimodal
        # This is more compatible with current NIM vision implementations
        content_string = f"{USER_PROMPT}\n<img src=\"data:image/jpeg;base64,{b64}\" />"
        
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "max_tokens": 2048,
            "top_p": 1.0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content_string},
            ],
        }

        last_error: Optional[Exception] = None

        for attempt in range(len(BACKOFF_DELAYS) + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        json=payload,
                        headers={"Authorization": f"Bearer {self.nvidia_key}"},
                    )

                    if resp.status_code == 429:
                        if attempt < len(BACKOFF_DELAYS):
                            delay = BACKOFF_DELAYS[attempt]
                            logger.warning(
                                f"NVIDIA NIM 429 rate limit. Retrying in {delay}s "
                                f"(attempt {attempt + 1}/{len(BACKOFF_DELAYS)})"
                            )
                            await asyncio.sleep(delay)
                            continue
                        resp.raise_for_status()

                    if resp.status_code >= 500:
                        if attempt < len(BACKOFF_DELAYS):
                            delay = BACKOFF_DELAYS[attempt]
                            logger.warning(
                                f"NVIDIA NIM {resp.status_code} server error. "
                                f"Retrying in {delay}s"
                            )
                            await asyncio.sleep(delay)
                            continue
                        resp.raise_for_status()

                    if resp.status_code == 400:
                        body = resp.text
                        logger.error(
                            f"NVIDIA NIM 400 Bad Request. "
                            f"Model: {self.model}. Response: {body[:500]}"
                        )
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < len(BACKOFF_DELAYS):
                    delay = BACKOFF_DELAYS[attempt]
                    logger.warning(f"NVIDIA NIM timeout. Retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                raise

            except httpx.HTTPStatusError:
                raise

        raise last_error or RuntimeError("NVIDIA NIM call failed after all retries")

    async def _call_ollama(self, image_bytes: bytes) -> str:
        """Call local Ollama instance."""
        b64 = encode_image_to_base64(image_bytes)
        payload = {
            "model": self.ollama_model,
            "prompt": f"{SYSTEM_PROMPT}\n\n{USER_PROMPT}",
            "images": [b64],
            "stream": False,
            "options": {"temperature": 0.0},
        }

        last_error: Optional[Exception] = None

        for attempt in range(len(BACKOFF_DELAYS) + 1):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(
                        f"{self.ollama_host}/api/generate",
                        json=payload,
                    )

                    if resp.status_code >= 500:
                        if attempt < len(BACKOFF_DELAYS):
                            delay = BACKOFF_DELAYS[attempt]
                            logger.warning(
                                f"Ollama {resp.status_code} error. Retrying in {delay}s"
                            )
                            await asyncio.sleep(delay)
                            continue

                    resp.raise_for_status()
                    return resp.json()["response"]

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < len(BACKOFF_DELAYS):
                    delay = BACKOFF_DELAYS[attempt]
                    logger.warning(f"Ollama timeout. Retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                raise

        raise last_error or RuntimeError("Ollama call failed after all retries")

    async def check_health(self) -> bool:
        """Check if the LLM provider is reachable."""
        try:
            if self.ollama_host:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{self.ollama_host}/api/tags")
                    return resp.status_code == 200
            else:
                # NVIDIA NIM doesn't have a free health endpoint,
                # so we just verify the key is configured
                return bool(self.nvidia_key)
        except Exception:
            return False


# Singleton instance
llm_client = LLMClient()
