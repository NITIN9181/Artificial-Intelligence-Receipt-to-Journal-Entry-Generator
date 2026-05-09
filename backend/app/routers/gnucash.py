"""
GnuCash export router (Phase 3).
Handles account mappings and journal entry exports.
"""

import io
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_preparer, require_admin_role, get_current_user_id
from app.database import get_db
from app.models.gnucash import GnuCashMapping
from app.models.journal import JournalEntry
from app.models.receipt import Receipt
from app.models.user import User, UserRole
from app.schemas.gnucash import (
    GnuCashMappingCreate,
    GnuCashMappingUpdate,
    GnuCashMappingResponse,
    ExportFormat,
    ExportRequest,
)
from app.services.gnucash_exporter import GnuCashExporter

router = APIRouter(prefix="/api/v1/gnucash", tags=["gnucash"])


@router.post("/mappings", response_model=GnuCashMappingResponse, status_code=201)
async def create_mapping(
    data: GnuCashMappingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_preparer)
):
    """
    Create a new GnuCash account mapping.
    Maps an internal account code to a GnuCash account path.
    """
    # Check if mapping already exists
    result = await db.execute(
        select(GnuCashMapping).where(
            GnuCashMapping.user_id == user.id,
            GnuCashMapping.internal_account_code == data.internal_account_code
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Mapping for account code '{data.internal_account_code}' already exists"
        )
    
    mapping = GnuCashMapping(
        user_id=user.id,
        internal_account_code=data.internal_account_code,
        gnucash_account_path=data.gnucash_account_path
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.get("/mappings", response_model=List[GnuCashMappingResponse])
async def list_mappings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_preparer)
):
    """List all GnuCash account mappings for the current user."""
    result = await db.execute(
        select(GnuCashMapping)
        .where(GnuCashMapping.user_id == user.id)
        .order_by(GnuCashMapping.internal_account_code)
    )
    return result.scalars().all()


@router.put("/mappings/{mapping_id}", response_model=GnuCashMappingResponse)
async def update_mapping(
    mapping_id: UUID,
    data: GnuCashMappingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_preparer)
):
    """Update an existing GnuCash account mapping."""
    mapping = await db.get(GnuCashMapping, mapping_id)
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    if mapping.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Can only update your own mappings")
    
    mapping.gnucash_account_path = data.gnucash_account_path
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.delete("/mappings/{mapping_id}", status_code=204)
async def delete_mapping(
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_preparer)
):
    """Delete a GnuCash account mapping."""
    mapping = await db.get(GnuCashMapping, mapping_id)
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    if mapping.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Can only delete your own mappings")
    
    await db.delete(mapping)
    await db.commit()


@router.post("/journal-entries/{entry_id}/export")
async def export_journal_entry(
    entry_id: UUID,
    format: ExportFormat = "xml",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_preparer)
):
    """
    Export a single journal entry to GnuCash format.
    
    Supported formats:
    - xml: GnuCash XML format (native)
    - csv: CSV format (simple import)
    - sqlite: SQLite SQL dump
    """
    # Fetch entry
    entry = await db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    # Verify user owns the receipt (or is admin)
    receipt = await db.get(Receipt, entry.receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    if receipt.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Can only export your own entries")
    
    # Export
    try:
        exporter = GnuCashExporter(db, user.id)
        content = await exporter.export_entry(entry_id, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Determine filename and media type
    filename = f"JE_{entry.entry_number}.{format}"
    media_types = {
        "xml": "application/xml",
        "sqlite": "application/octet-stream",
        "csv": "text/csv"
    }
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_types[format],
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/journal-entries/export-multiple")
async def export_multiple_entries(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_preparer)
):
    """
    Export multiple journal entries to a single GnuCash file.
    
    Request body:
    {
        "entry_ids": ["uuid1", "uuid2", ...],
        "format": "xml"  // or "csv", "sqlite"
    }
    """
    # Verify all entries exist and user has access
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id.in_(request.entry_ids))
    )
    entries = result.scalars().all()
    
    if len(entries) != len(request.entry_ids):
        raise HTTPException(
            status_code=404,
            detail=f"Found {len(entries)} entries, expected {len(request.entry_ids)}"
        )
    
    # Verify ownership
    for entry in entries:
        receipt = await db.get(Receipt, entry.receipt_id)
        if receipt.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail=f"Cannot export entry {entry.id}: not your receipt"
            )
    
    # Export
    try:
        exporter = GnuCashExporter(db, user.id)
        content = await exporter.export_multiple_entries(request.entry_ids, request.format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Determine filename and media type
    filename = f"journal_entries_export.{request.format}"
    media_types = {
        "xml": "application/xml",
        "sqlite": "application/octet-stream",
        "csv": "text/csv"
    }
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_types[request.format],
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/import-coa", status_code=200)
async def import_coa_from_gnucash(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_role)
):
    """
    Import chart of accounts from GnuCash XML export.
    Creates mappings automatically based on account structure.
    
    Admin only - requires careful review of imported mappings.
    """
    import xml.etree.ElementTree as ET
    
    if not file.filename.endswith('.xml'):
        raise HTTPException(400, "File must be XML")
    
    content = await file.read()
    
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise HTTPException(400, f"Invalid XML: {str(e)}")
    
    # GnuCash account XML namespaces
    ns = {
        'gnc': 'http://www.gnucash.org/XML/gnc',
        'act': 'http://www.gnucash.org/XML/act'
    }
    
    # Find all accounts
    accounts = []
    for account in root.findall('.//gnc:account', ns):
        name_elem = account.find('act:name', ns)
        type_elem = account.find('act:type', ns)
        parent_elem = account.find('act:parent', ns)
        id_elem = account.find('act:id', ns)
        
        if name_elem is not None and type_elem is not None:
            accounts.append({
                'name': name_elem.text,
                'type': type_elem.text,
                'parent': parent_elem.text if parent_elem is not None else None,
                'guid': id_elem.text if id_elem is not None else None
            })
    
    if not accounts:
        raise HTTPException(400, "No accounts found in XML file")
    
    # Build full paths (GnuCash uses hierarchical paths like "Expenses:Office Supplies")
    guid_to_account = {a['guid']: a for a in accounts if a['guid']}
    path_map = {}
    
    def build_path(account_guid, visited=None):
        if visited is None:
            visited = set()
        if account_guid in visited or account_guid not in guid_to_account:
            return guid_to_account.get(account_guid, {}).get('name', '')
        
        visited.add(account_guid)
        account = guid_to_account[account_guid]
        parent_path = build_path(account['parent'], visited) if account['parent'] else ''
        
        if parent_path:
            return f"{parent_path}:{account['name']}"
        return account['name']
    
    for acc in accounts:
        if acc['guid']:
            path_map[acc['guid']] = build_path(acc['guid'])
    
    # Create mappings for each account
    created = 0
    updated = 0
    skipped = 0
    
    for acc in accounts:
        if not acc['guid']:
            skipped += 1
            continue
        
        full_path = path_map.get(acc['guid'], acc['name'])
        
        # Map GnuCash account types to internal codes
        internal_code = _map_gnucash_type_to_internal(acc['type'], full_path)
        if not internal_code:
            skipped += 1
            continue  # Skip unmapped types
        
        # Check if mapping exists
        existing = await db.execute(
            select(GnuCashMapping).where(
                GnuCashMapping.user_id == user.id,
                GnuCashMapping.internal_account_code == internal_code
            )
        )
        existing_mapping = existing.scalar_one_or_none()
        
        if existing_mapping:
            existing_mapping.gnucash_account_path = full_path
            updated += 1
        else:
            mapping = GnuCashMapping(
                user_id=user.id,
                internal_account_code=internal_code,
                gnucash_account_path=full_path
            )
            db.add(mapping)
            created += 1
    
    await db.commit()
    
    return {
        "message": f"Imported {created} new mappings, updated {updated} existing, skipped {skipped}",
        "accounts_found": len(accounts),
        "mappings_created": created,
        "mappings_updated": updated,
        "skipped": skipped
    }


def _map_gnucash_type_to_internal(gnc_type: str, gnc_path: str) -> str | None:
    """Map GnuCash account type/path to internal account code."""
    # Simple heuristic: use path to guess
    path_lower = gnc_path.lower()
    
    if 'cash' in path_lower:
        return 'ASSET_CASH'
    elif 'receivable' in path_lower or 'ar' in path_lower or 'a/r' in path_lower:
        return 'ASSET_AR'
    elif 'inventory' in path_lower:
        return 'ASSET_INVENTORY'
    elif 'payable' in path_lower or 'ap' in path_lower or 'a/p' in path_lower:
        return 'LIABILITY_AP'
    elif 'short' in path_lower and 'term' in path_lower:
        return 'LIABILITY_ST'
    elif 'long' in path_lower and 'term' in path_lower:
        return 'LIABILITY_LT'
    elif 'owner' in path_lower or 'capital' in path_lower:
        return 'EQUITY_OWNER'
    elif 'retained' in path_lower or 'earning' in path_lower:
        return 'EQUITY_RETAINED'
    elif 'office' in path_lower or 'supply' in path_lower or 'supplies' in path_lower:
        return 'EXPENSE_OFFICE'
    elif 'meal' in path_lower or 'food' in path_lower or 'dining' in path_lower:
        return 'EXPENSE_MEALS'
    elif 'travel' in path_lower:
        return 'EXPENSE_TRAVEL'
    elif 'utility' in path_lower or 'utilities' in path_lower:
        return 'EXPENSE_UTILITIES'
    elif 'sales' in path_lower and gnc_type in ['INCOME', 'REVENUE']:
        return 'REVENUE_SALES'
    elif 'service' in path_lower and gnc_type in ['INCOME', 'REVENUE']:
        return 'REVENUE_SERVICES'
    
    # Fallback: return None (user will map manually)
    return None
