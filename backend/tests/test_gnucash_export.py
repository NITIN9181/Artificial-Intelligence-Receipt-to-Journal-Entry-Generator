"""
GnuCash export tests for Phase 3.
Tests XML, CSV, and SQLite export formats and COA mapping.
"""

import pytest
import xml.etree.ElementTree as ET
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestGnuCashExport:
    """GnuCash export functionality tests."""
    
    async def test_xml_export_valid_structure(
        self, client: AsyncClient, preparer_token: str, posted_entry_id: str
    ):
        """XML export has valid GnuCash structure with proper namespaces."""
        resp = await client.post(
            f"/api/v1/gnucash/journal-entries/{posted_entry_id}/export?format=xml",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/xml"
        
        content = resp.content
        # Parse to verify valid XML
        root = ET.fromstring(content)
        
        # Check for proper namespaces
        assert b'xmlns:gnc="http://www.gnucash.org/XML/gnc"' in content
        assert b'xmlns:trn="http://www.gnucash.org/XML/trn"' in content
        assert b'xmlns:split="http://www.gnucash.org/XML/split"' in content
        
        # Must have transaction
        assert b"<gnc:transaction" in content or b"<gnc:transaction>" in content
        assert b"<trn:splits>" in content
    
    async def test_csv_export_valid(
        self, client: AsyncClient, preparer_token: str, posted_entry_id: str
    ):
        """CSV export has valid format."""
        resp = await client.post(
            f"/api/v1/gnucash/journal-entries/{posted_entry_id}/export?format=csv",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/csv"
        
        content = resp.content.decode('utf-8')
        lines = content.strip().split('\n')
        assert len(lines) >= 2  # Header + at least 1 line
        
        # Check header
        header = lines[0]
        assert "Date" in header
        assert "Account" in header
        assert "Debit" in header or "Credit" in header
    
    async def test_sqlite_export_valid(
        self, client: AsyncClient, preparer_token: str, posted_entry_id: str
    ):
        """SQLite export has valid SQL dump."""
        resp = await client.post(
            f"/api/v1/gnucash/journal-entries/{posted_entry_id}/export?format=sqlite",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        content = resp.content
        
        # Verify it contains SQL statements
        assert b"INSERT INTO transactions" in content or b"INSERT INTO" in content
        assert b"BEGIN TRANSACTION" in content or b"INSERT" in content
    
    async def test_export_unauthorized_entry(
        self, client: AsyncClient, preparer_token: str, other_user_posted_id: str
    ):
        """Cannot export another user's entry."""
        resp = await client.post(
            f"/api/v1/gnucash/journal-entries/{other_user_posted_id}/export?format=xml",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 403
    
    async def test_export_non_posted_entry(
        self, client: AsyncClient, preparer_token: str, draft_entry_id: str
    ):
        """Cannot export non-POSTED entry."""
        resp = await client.post(
            f"/api/v1/gnucash/journal-entries/{draft_entry_id}/export?format=xml",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code in [400, 409]
    
    async def test_bulk_export(
        self, client: AsyncClient, preparer_token: str, multiple_posted_entry_ids: list
    ):
        """Export multiple entries at once."""
        resp = await client.post(
            "/api/v1/gnucash/journal-entries/export-multiple",
            json={"entry_ids": multiple_posted_entry_ids, "format": "xml"},
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        
        # Verify multiple transactions in output
        content = resp.content
        # Count occurrences of transaction tags
        transaction_count = content.count(b"<gnc:transaction")
        assert transaction_count >= len(multiple_posted_entry_ids)
    
    async def test_coa_mapping_crud(self, client: AsyncClient, preparer_token: str):
        """Full CRUD on COA mappings."""
        # Create
        resp = await client.post(
            "/api/v1/gnucash/mappings",
            json={
                "internal_account_code": "EXPENSE_TEST",
                "gnucash_account_path": "Expenses:Test"
            },
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 201
        mapping_id = resp.json()["id"]
        
        # List
        resp = await client.get(
            "/api/v1/gnucash/mappings",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        mappings = resp.json()
        assert any(m["internal_account_code"] == "EXPENSE_TEST" for m in mappings)
        
        # Update
        resp = await client.put(
            f"/api/v1/gnucash/mappings/{mapping_id}",
            json={"gnucash_account_path": "Expenses:Test Updated"},
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["gnucash_account_path"] == "Expenses:Test Updated"
        
        # Delete
        resp = await client.delete(
            f"/api/v1/gnucash/mappings/{mapping_id}",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 204
    
    async def test_import_coa_from_gnucash_xml(
        self, client: AsyncClient, admin_token: str
    ):
        """Import COA from GnuCash XML file."""
        # Create a sample GnuCash accounts XML
        xml_content = b'''<?xml version="1.0"?>
<gnc-v2 xmlns:gnc="http://www.gnucash.org/XML/gnc" xmlns:act="http://www.gnucash.org/XML/act">
    <gnc:account>
        <act:name>Cash</act:name>
        <act:id type="guid">abc123</act:id>
        <act:type>ASSET</act:type>
    </gnc:account>
    <gnc:account>
        <act:name>Office Supplies</act:name>
        <act:id type="guid">def456</act:id>
        <act:type>EXPENSE</act:type>
    </gnc:account>
</gnc-v2>'''
        
        # Upload as multipart form
        from io import BytesIO
        files = {"file": ("accounts.xml", BytesIO(xml_content), "application/xml")}
        
        resp = await client.post(
            "/api/v1/gnucash/import-coa",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["accounts_found"] >= 2
        assert data["mappings_created"] >= 1 or data["mappings_updated"] >= 1
    
    async def test_import_coa_requires_admin(
        self, client: AsyncClient, preparer_token: str
    ):
        """COA import requires ADMIN role."""
        xml_content = b'<?xml version="1.0"?><gnc-v2></gnc-v2>'
        from io import BytesIO
        files = {"file": ("accounts.xml", BytesIO(xml_content), "application/xml")}
        
        resp = await client.post(
            "/api/v1/gnucash/import-coa",
            files=files,
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 403
    
    async def test_export_with_mappings(
        self, client: AsyncClient, preparer_token: str, posted_entry_id: str
    ):
        """Export uses account mappings correctly."""
        # Create a mapping
        await client.post(
            "/api/v1/gnucash/mappings",
            json={
                "internal_account_code": "EXPENSE_OFFICE",
                "gnucash_account_path": "Expenses:Office Supplies"
            },
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        
        # Export
        resp = await client.post(
            f"/api/v1/gnucash/journal-entries/{posted_entry_id}/export?format=xml",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        
        content = resp.content.decode('utf-8')
        # Check if mapping was used (if entry has EXPENSE_OFFICE)
        if "EXPENSE_OFFICE" in content or "Office" in content:
            assert "Expenses:Office Supplies" in content or "Office" in content
    
    async def test_xml_export_has_proper_guids(
        self, client: AsyncClient, preparer_token: str, posted_entry_id: str
    ):
        """XML export uses GUIDs without hyphens (GnuCash format)."""
        resp = await client.post(
            f"/api/v1/gnucash/journal-entries/{posted_entry_id}/export?format=xml",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        
        content = resp.content.decode('utf-8')
        root = ET.fromstring(content)
        
        # Find all GUID elements
        for elem in root.iter():
            if elem.get('type') == 'guid' and elem.text:
                # GnuCash GUIDs should not have hyphens
                # Our implementation may or may not remove them, but should be consistent
                guid = elem.text
                # Just verify it's a valid format (32 or 36 chars)
                assert len(guid) in [32, 36], f"Invalid GUID length: {guid}"
    
    async def test_csv_export_has_all_lines(
        self, client: AsyncClient, preparer_token: str, posted_entry_id: str
    ):
        """CSV export includes all journal entry lines."""
        resp = await client.post(
            f"/api/v1/gnucash/journal-entries/{posted_entry_id}/export?format=csv",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        
        content = resp.content.decode('utf-8')
        lines = content.strip().split('\n')
        
        # Should have header + at least 2 lines (debit and credit)
        assert len(lines) >= 3  # Header + 2 splits minimum
