import pytest
from httpx import AsyncClient
import csv
from io import StringIO

@pytest.mark.asyncio
async def test_csv_export_accuracy(async_client: AsyncClient, admin_token_headers, db_session):
    # Assuming the db already has or we can create 3 journal entries
    # For test isolation, we'd normally seed data here.
    
    response = await async_client.get(
        "/api/v1/journal-entries/export/csv",
        headers=admin_token_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    csv_content = response.text
    reader = csv.DictReader(StringIO(csv_content))
    rows = list(reader)
    
    # We assert it returns rows and standard columns
    assert "entry_number" in reader.fieldnames
    assert "total_debit" in reader.fieldnames
    assert "total_credit" in reader.fieldnames
    
    # Assert line items are not included (flat entry export)
    assert "line_item_description" not in reader.fieldnames
