import time
from datetime import datetime, timedelta
import io
import sys

import httpx
from jose import jwt
from PIL import Image

# Import settings to use real keys
from app.config import settings

# 1. Configuration
BASE_URL = "http://localhost:8000/api/v1"
USER_ID = "00000000-0000-0000-0000-000000000001"

print("==================================================")
print("  AI Receipt to Journal Entry - Backend API Test  ")
print("==================================================")

if settings.supabase_url == "http://localhost:8000":
    print("❌ ERROR: Your SUPABASE_URL in docker-compose.yml is still set to the dummy 'http://localhost:8000'.")
    print("   The file upload requires a real Supabase project.")
    print("   Please create a Supabase project and update SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in docker-compose.yml.")
    sys.exit(1)

# 2. Generate a valid mock JWT using your real Supabase Service Key or Anon Key
payload = {
    "sub": USER_ID,
    "aud": "authenticated",
    "exp": int((datetime.utcnow() + timedelta(days=1)).timestamp())
}

try:
    # Use the first part of the service role key as the JWT secret if it's standard Supabase
    jwt_secret = settings.supabase_service_role_key.split(".")[0] if "." in settings.supabase_service_role_key else settings.supabase_anon_key
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
except Exception:
    token = jwt.encode(payload, settings.supabase_anon_key, algorithm="HS256")

headers = {"Authorization": f"Bearer {token}"}
print(f"✅ Generated Mock JWT for User: {USER_ID}")

# 3. Create a dummy receipt image in memory
img = Image.new('RGB', (400, 600), color=(255, 255, 255))
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)
print("✅ Generated dummy receipt image")

# 4. UPLOAD Endpoint
print("\n---> 1. Testing POST /receipts/upload")
files = {'file': ('dummy_receipt.jpg', img_bytes, 'image/jpeg')}
try:
    resp = httpx.post(f"{BASE_URL}/receipts/upload", headers=headers, files=files, timeout=30.0)
    resp.raise_for_status()
    upload_data = resp.json()
    receipt_id = upload_data["id"]
    print(f"✅ Upload successful! Receipt ID: {receipt_id}")
    print(f"   Status: {upload_data['status']}")
except Exception as e:
    print(f"❌ Upload Failed: {e}")
    sys.exit(1)

# 5. EXTRACTION Endpoint
print(f"\n---> 2. Testing POST /receipts/{receipt_id}/extract (NVIDIA NIM Llama 4 Maverick)")
try:
    resp = httpx.post(f"{BASE_URL}/receipts/{receipt_id}/extract", headers=headers)
    resp.raise_for_status()
    print("✅ Extraction triggered. This will run async in the background.")
except Exception as e:
    print(f"❌ Trigger Extraction Failed: {e}")
    sys.exit(1)

# 6. GET RECEIPT (Poll until done)
print(f"\n---> 3. Polling GET /receipts/{receipt_id} for extraction results...")
max_attempts = 15
extracted_data = None
for i in range(max_attempts):
    resp = httpx.get(f"{BASE_URL}/receipts/{receipt_id}", headers=headers)
    data = resp.json()
    status = data["status"]
    print(f"   [Attempt {i+1}] Status: {status}")
    
    if status == "EXTRACTED":
        extracted_data = data["extracted_data"]
        print("\n✅ Extraction Complete!")
        print("   Extracted Data:")
        for k, v in extracted_data.items():
            print(f"     - {k}: {v}")
        break
    elif status == "EXTRACTION_FAILED":
        print(f"\n❌ Extraction Failed! Error: {data.get('extraction_error')}")
        break
        
    time.sleep(2)

# 7. CORRECT (Simulate manual human review)
if extracted_data:
    print(f"\n---> 4. Testing PUT /receipts/{receipt_id}/correct (Simulate User Review)")
    corrections = {
        "vendor_name": "Test Vendor LLC",
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "currency": "USD",
        "subtotal": 100.00,
        "tax_amount": 5.00,
        "tip_amount": 0.00,
        "total_amount": 105.00,
        "payment_method": "Card",
        "line_items": []
    }
    resp = httpx.put(f"{BASE_URL}/receipts/{receipt_id}/correct", headers=headers, json=corrections)
    if resp.status_code == 422:
        print(f"❌ 422 Validation Error: {resp.text}")
    resp.raise_for_status()
    print("✅ Corrections saved! Status is now REVIEWED.")

    # 8. JOURNALIZE
    print(f"\n---> 5. Testing POST /receipts/{receipt_id}/journalize (Bookkeeping Engine)")
    resp = httpx.post(f"{BASE_URL}/receipts/{receipt_id}/journalize", headers=headers, json={})
    
    if resp.status_code == 201:
        journal_data = resp.json()
        print("\n✅ Bookkeeping Engine Success! Journal Entry created.")
        print(f"   Entry Number: {journal_data['entry_number']}")
        print(f"   Total Debit:  ${journal_data['total_debit']}")
        print(f"   Total Credit: ${journal_data['total_credit']}")
        journal_entry_id = journal_data['journal_entry_id']

        # 9. GET JOURNAL ENTRIES LIST
        print(f"\n---> 6. Testing GET /journal-entries (Pagination & Filters)")
        resp = httpx.get(f"{BASE_URL}/journal-entries", headers=headers, params={"per_page": 5})
        resp.raise_for_status()
        list_data = resp.json()
        print(f"✅ Fetched list successfully. Total items: {list_data['pagination']['total']}")

        # 10. REVERSE JOURNAL ENTRY
        print(f"\n---> 7. Testing DELETE /journal-entries/{journal_entry_id}/reverse")
        resp = httpx.request(
            "DELETE", 
            f"{BASE_URL}/journal-entries/{journal_entry_id}/reverse", 
            headers=headers, 
            json={"reason": "Testing reversal process"}
        )
        if resp.status_code == 201:
            reversal_data = resp.json()
            print("✅ Reversal successful! Mirror entry created.")
            print(f"   Reversal Entry Number: {reversal_data['entry_number']}")
            print(f"   Status: {reversal_data['status']}")
        else:
            print(f"❌ Reversal failed: {resp.status_code} - {resp.text}")

    else:
        print(f"\n❌ Journalize failed: {resp.status_code} - {resp.text}")

print("\n==================================================")
print("  Test script finished.  ")
print("==================================================")
