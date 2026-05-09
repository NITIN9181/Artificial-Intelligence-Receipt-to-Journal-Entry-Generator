# Manual Test — Handwritten Receipt

## Prerequisites:
- Have a blurry or handwritten receipt image ready.

## Steps:
1. Upload the handwritten receipt via `/upload`
2. Trigger extraction
3. Wait for `EXTRACTED` status (may take 15-30 seconds)
4. Open `/review/{id}`
5. Verify:
   - Confidence scores for `vendor_name`, `date`, `total_amount` are <0.80
   - Yellow (0.60-0.79), orange (0.40-0.59), or red (<0.40) left borders visible on low-confidence fields
   - "Approve & Post" is available after correction
6. Correct the fields manually
7. Post the entry
8. Verify journal entry is balanced (debits = credits)

## Results
- [x] Tested successfully on handwritten receipt image. Low confidence styles appeared appropriately and the manual correction workflow functioned as expected.
