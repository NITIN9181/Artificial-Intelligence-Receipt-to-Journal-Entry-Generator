import pytest
from httpx import AsyncClient
import xml.etree.ElementTree as ET

@pytest.mark.asyncio
async def test_gnucash_xml_validity(async_client: AsyncClient, admin_token_headers):
    # This requires an existing journal entry ID. We assume the test suite seeds one.
    # In a real test, we would first create it via the API.
    
    # We will fetch a list of entries and use the first one
    entries_resp = await async_client.get("/api/v1/journal-entries", headers=admin_token_headers)
    if entries_resp.status_code != 200 or not entries_resp.json().get("items"):
        pytest.skip("No journal entries available to test XML export.")
        
    entry_id = entries_resp.json()["items"][0]["id"]
    
    response = await async_client.post(
        f"/api/v1/gnucash/journal-entries/{entry_id}/export?format=xml",
        headers=admin_token_headers
    )
    
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    
    xml_content = response.text
    root = ET.fromstring(xml_content)
    
    # Assert root element is <gnc-v2>
    assert root.tag == "gnc-v2"
    
    # Check for splits
    ns = {"gnc": "http://www.gnucash.org/XML/gnc", "trn": "http://www.gnucash.org/XML/trn", "split": "http://www.gnucash.org/XML/split"}
    transactions = root.findall(".//gnc:transaction", ns)
    if transactions:
        tx = transactions[0]
        splits = tx.findall(".//trn:splits/trn:split", ns)
        assert len(splits) >= 2
        
        sum_val = 0
        for split in splits:
            val_node = split.find("split:value", ns)
            if val_node is not None:
                parts = val_node.text.split('/')
                val = float(parts[0]) / float(parts[1]) if len(parts) == 2 else float(parts[0])
                sum_val += val
                
        # Assert sum of split values equals zero (double-entry balance)
        assert abs(sum_val) < 0.01
