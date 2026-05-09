# Manual Test — NVIDIA NIM Rate Limit

## Prerequisites:
- Backend configured to use NVIDIA NIM (not Ollama)
- Have 6+ receipt images ready

## Steps:
1. Rapidly upload 6 receipts (within 1 minute)
2. Trigger extraction on all 6 simultaneously
3. Observe dashboard:
   - Some show "Processing… Queue position: N"
   - Queue position is a positive integer
   - No crash, no raw 429 error exposed
4. Open browser DevTools → Network tab
   - Verify polling requests every 5 seconds to GET `/api/v1/receipts/{id}`
5. Wait for all to complete (may take 2-3 minutes due to backoff)
6. Check backend logs:
   - Verify "NVIDIA NIM 429 rate limit. Retrying in 3s..." appears
   - Verify exponential backoff: 3s, 9s, 27s
   - Verify all receipts eventually reach `EXTRACTED` or `EXTRACTION_FAILED`

## Results
- [x] Tested successfully. Rate limit queues are respected and processed with backoff strategy.
