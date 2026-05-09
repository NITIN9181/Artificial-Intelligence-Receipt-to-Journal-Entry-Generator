"""
GnuCash export service (Phase 3).
Exports journal entries to GnuCash-compatible formats: XML, CSV, SQLite.
"""

import csv
import io
import xml.etree.ElementTree as ET
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gnucash import GnuCashMapping
from app.models.journal import JournalEntry, EntryStatus

ExportFormat = Literal["xml", "csv", "sqlite"]


class GnuCashExporter:
    """Exports journal entries to GnuCash formats."""

    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id

    async def export_entry(self, entry_id: UUID, format: ExportFormat) -> bytes:
        """
        Export a single journal entry to the specified format.
        
        Args:
            entry_id: UUID of the journal entry to export
            format: Export format (xml, csv, or sqlite)
            
        Returns:
            Bytes of the exported file
            
        Raises:
            ValueError: If entry not found or not POSTED
        """
        # Fetch entry with lines
        result = await self.db.execute(
            select(JournalEntry).where(JournalEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        
        if not entry:
            raise ValueError(f"Journal entry {entry_id} not found")
        
        if entry.status != EntryStatus.POSTED:
            raise ValueError("Only POSTED entries can be exported")

        if format == "xml":
            return await self._export_xml(entry)
        elif format == "csv":
            return await self._export_csv(entry)
        elif format == "sqlite":
            return await self._export_sqlite(entry)
        else:
            raise ValueError(f"Unknown format: {format}")

    async def export_multiple_entries(
        self, entry_ids: list[UUID], format: ExportFormat
    ) -> bytes:
        """
        Export multiple journal entries to a single file.
        
        Args:
            entry_ids: List of journal entry UUIDs
            format: Export format (xml, csv, or sqlite)
            
        Returns:
            Bytes of the exported file
        """
        # Fetch all entries
        result = await self.db.execute(
            select(JournalEntry).where(JournalEntry.id.in_(entry_ids))
        )
        entries = result.scalars().all()
        
        # Verify all are POSTED
        non_posted = [e for e in entries if e.status != EntryStatus.POSTED]
        if non_posted:
            raise ValueError(f"All entries must be POSTED. Found {len(non_posted)} non-posted entries")

        if format == "xml":
            return await self._export_multiple_xml(entries)
        elif format == "csv":
            return await self._export_multiple_csv(entries)
        elif format == "sqlite":
            return await self._export_multiple_sqlite(entries)
        else:
            raise ValueError(f"Unknown format: {format}")

    async def _get_mappings(self) -> dict[str, str]:
        """Fetch user's GnuCash account mappings."""
        result = await self.db.execute(
            select(GnuCashMapping).where(GnuCashMapping.user_id == self.user_id)
        )
        mappings = result.scalars().all()
        return {m.internal_account_code: m.gnucash_account_path for m in mappings}

    async def _export_xml(self, entry: JournalEntry) -> bytes:
        """Export single entry to GnuCash XML format with proper namespaces."""
        root = ET.Element("gnc-v2")
        root.set("xmlns:gnc", "http://www.gnucash.org/XML/gnc")
        root.set("xmlns:act", "http://www.gnucash.org/XML/act")
        root.set("xmlns:book", "http://www.gnucash.org/XML/book")
        root.set("xmlns:cd", "http://www.gnucash.org/XML/cd")
        root.set("xmlns:cmdty", "http://www.gnucash.org/XML/cmdty")
        root.set("xmlns:split", "http://www.gnucash.org/XML/split")
        root.set("xmlns:trn", "http://www.gnucash.org/XML/trn")
        root.set("xmlns:ts", "http://www.gnucash.org/XML/ts")
        
        book = ET.SubElement(root, "gnc:book")
        book.set("version", "2.0.0")
        
        # Add count metadata
        count_data = ET.SubElement(book, "gnc:count-data")
        count_data.set("cd:type", "transaction")
        count_data.text = "1"
        
        # Create transaction
        await self._add_transaction_to_xml(book, entry)
        
        # Pretty print
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    async def _export_multiple_xml(self, entries: list[JournalEntry]) -> bytes:
        """Export multiple entries to GnuCash XML format with proper namespaces."""
        root = ET.Element("gnc-v2")
        root.set("xmlns:gnc", "http://www.gnucash.org/XML/gnc")
        root.set("xmlns:act", "http://www.gnucash.org/XML/act")
        root.set("xmlns:book", "http://www.gnucash.org/XML/book")
        root.set("xmlns:cd", "http://www.gnucash.org/XML/cd")
        root.set("xmlns:cmdty", "http://www.gnucash.org/XML/cmdty")
        root.set("xmlns:split", "http://www.gnucash.org/XML/split")
        root.set("xmlns:trn", "http://www.gnucash.org/XML/trn")
        root.set("xmlns:ts", "http://www.gnucash.org/XML/ts")
        
        book = ET.SubElement(root, "gnc:book")
        book.set("version", "2.0.0")
        
        # Add count metadata
        count_data = ET.SubElement(book, "gnc:count-data")
        count_data.set("cd:type", "transaction")
        count_data.text = str(len(entries))
        
        # Add all transactions
        for entry in entries:
            await self._add_transaction_to_xml(book, entry)
        
        # Pretty print
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    async def _add_transaction_to_xml(self, parent: ET.Element, entry: JournalEntry):
        """Add a single transaction to XML tree with proper GnuCash structure."""
        mappings = await self._get_mappings()
        
        txn = ET.SubElement(parent, "gnc:transaction")
        txn.set("version", "2.0.0")
        
        # Transaction ID (GnuCash uses GUIDs without hyphens)
        trn_id = ET.SubElement(txn, "trn:id")
        trn_id.set("type", "guid")
        trn_id.text = str(uuid4()).replace('-', '')
        
        # Dates
        date_posted = ET.SubElement(txn, "trn:date-posted")
        ts_date = ET.SubElement(date_posted, "ts:date")
        ts_date.text = entry.entry_date.isoformat()
        
        date_entered = ET.SubElement(txn, "trn:date-entered")
        ts_date_entered = ET.SubElement(date_entered, "ts:date")
        ts_date_entered.text = entry.created_at.isoformat()
        
        # Description
        description = ET.SubElement(txn, "trn:description")
        description.text = entry.description or f"Journal Entry {entry.entry_number}"
        
        # Entry number
        num = ET.SubElement(txn, "trn:num")
        num.text = str(entry.entry_number)
        
        # Splits (lines)
        splits = ET.SubElement(txn, "trn:splits")
        
        for line in entry.lines:
            split = ET.SubElement(splits, "trn:split")
            
            # Split ID (GnuCash uses GUIDs without hyphens)
            split_id = ET.SubElement(split, "split:id")
            split_id.set("type", "guid")
            split_id.text = str(uuid4()).replace('-', '')
            
            # Reconciled state
            reconciled = ET.SubElement(split, "split:reconciled-state")
            reconciled.text = "n"
            
            # Value (GnuCash uses integer math: 5.00 = 500/100)
            value = ET.SubElement(split, "split:value")
            quantity = ET.SubElement(split, "split:quantity")
            if line.debit > 0:
                amount_cents = int(line.debit * 100)
                value.text = f"{amount_cents}/100"
                quantity.text = f"{amount_cents}/100"
            else:
                amount_cents = int(line.credit * 100)
                value.text = f"-{amount_cents}/100"
                quantity.text = f"-{amount_cents}/100"
            
            # Account path (stored as text for simplicity - real GnuCash uses account GUIDs)
            account = ET.SubElement(split, "split:account")
            gnc_path = mappings.get(line.account_code, f"Unknown:{line.account_code}")
            account.text = gnc_path
            
            # Memo (optional)
            if hasattr(line, 'memo') and line.memo:
                memo = ET.SubElement(split, "split:memo")
                memo.text = line.memo

    async def _export_csv(self, entry: JournalEntry) -> bytes:
        """Export single entry to CSV format."""
        return await self._export_multiple_csv([entry])

    async def _export_multiple_csv(self, entries: list[JournalEntry]) -> bytes:
        """Export multiple entries to CSV format."""
        mappings = await self._get_mappings()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["Date", "Entry Number", "Description", "Account", "Debit", "Credit", "Memo"])
        
        # Rows
        for entry in entries:
            for line in entry.lines:
                gnc_path = mappings.get(line.account_code, line.account_code)
                writer.writerow([
                    entry.entry_date.strftime("%Y-%m-%d"),
                    entry.entry_number,
                    entry.description or "",
                    gnc_path,
                    f"{line.debit:.2f}" if line.debit > 0 else "",
                    f"{line.credit:.2f}" if line.credit > 0 else "",
                    line.memo or ""
                ])
        
        return output.getvalue().encode("utf-8")

    async def _export_sqlite(self, entry: JournalEntry) -> bytes:
        """Export single entry to SQLite SQL dump format."""
        return await self._export_multiple_sqlite([entry])

    async def _export_multiple_sqlite(self, entries: list[JournalEntry]) -> bytes:
        """
        Export multiple entries to SQLite SQL dump format.
        
        Note: Full GnuCash SQLite schema is complex. This generates
        SQL INSERT statements that can be imported into GnuCash SQLite backend.
        """
        mappings = await self._get_mappings()
        
        output = io.StringIO()
        output.write("-- GnuCash SQLite Export\n")
        output.write("-- Generated by Receipt-to-Journal-Entry Generator\n\n")
        output.write("BEGIN TRANSACTION;\n\n")
        
        for entry in entries:
            txn_guid = str(uuid4())
            
            # Insert transaction
            output.write(f"INSERT INTO transactions (guid, post_date, enter_date, description) VALUES ")
            output.write(f"('{txn_guid}', '{entry.entry_date.strftime('%Y-%m-%d')}', ")
            output.write(f"'{entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}', ")
            output.write(f"'{entry.description or f'Journal Entry {entry.entry_number}'}');\n")
            
            # Insert splits
            for line in entry.lines:
                split_guid = str(uuid4())
                gnc_path = mappings.get(line.account_code, line.account_code)
                
                if line.debit > 0:
                    value = int(line.debit * 100)
                else:
                    value = -int(line.credit * 100)
                
                output.write(f"INSERT INTO splits (guid, tx_guid, account_guid, value_num, value_denom, reconcile_state) VALUES ")
                output.write(f"('{split_guid}', '{txn_guid}', ")
                output.write(f"(SELECT guid FROM accounts WHERE name = '{gnc_path}'), ")
                output.write(f"{value}, 100, 'n');\n")
            
            output.write("\n")
        
        output.write("COMMIT;\n")
        return output.getvalue().encode("utf-8")
