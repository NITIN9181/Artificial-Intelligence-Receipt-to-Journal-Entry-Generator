import io
from datetime import date as date_type
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from fastapi.responses import StreamingResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.journal import JournalEntry
from app.models.receipt import Receipt

async def generate_pdf_stream(filters: dict, db: AsyncSession, user_id: str):
    
    query = (
        select(JournalEntry)
        .join(Receipt, JournalEntry.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .options(selectinload(JournalEntry.lines))
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
    )
    
    if filters.get("date_from"):
        query = query.where(JournalEntry.entry_date >= filters["date_from"])
    if filters.get("date_to"):
        query = query.where(JournalEntry.entry_date <= filters["date_to"])
    if filters.get("vendor"):
        query = query.where(JournalEntry.reference.ilike(f"%{filters['vendor']}%"))
    if filters.get("status"):
        query = query.where(JournalEntry.status == filters["status"])

    result = await db.execute(query)
    entries = result.scalars().all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    
    elements = []
    
    # Header
    elements.append(Paragraph("Journal Entry Ledger Report", title_style))
    elements.append(Spacer(1, 20))
    
    # Table headers
    for entry in entries:
        elements.append(Paragraph(f"<b>Entry #:</b> {entry.entry_number} | <b>Date:</b> {entry.entry_date} | <b>Ref:</b> {entry.reference or 'N/A'}", styles['Normal']))
        elements.append(Spacer(1, 5))
        
        data = [["Account Code", "Account Name", "Debit", "Credit", "Status"]]
        for line in (entry.lines or []):
            status_str = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
            data.append([
                line.account_code,
                line.account_name,
                f"{line.debit:.2f}" if line.debit else "",
                f"{line.credit:.2f}" if line.credit else "",
                status_str
            ])
            
        # Footer row for totals
        data.append([
            "", "Total:",
            f"{entry.total_debit:.2f}",
            f"{entry.total_credit:.2f}",
            ""
        ])
        
        t = Table(data, colWidths=[80, 200, 80, 80, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'), # Align amounts right
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (3, -1), 'Courier'), # Monospace for amounts
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -2), 1, colors.HexColor('#e5e7eb')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#000000')),
            ('FONTNAME', (1, -1), (3, -1), 'Helvetica-Bold'), # Totals bold
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 20))

    # Page numbering function
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(A4[0] - 30, 15, text)

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.read()]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=journal_ledger.pdf"}
    )
