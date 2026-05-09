# Manual Test — Mobile Responsiveness (iOS & Android)

## Target Viewports
- iPhone SE (375x667)
- iPhone 14 Pro Max (430x932)
- Android (e.g., Pixel 7)

## Pages to Test
1. **`/upload`**
   - "Take Photo" button is clearly visible and primary.
   - Glassmorphism panels stack cleanly vertically.
   - Dropzone accommodates touch input.
2. **`/review/{id}`**
   - Input forms stack underneath the receipt image.
   - Floating action bar ("Approve & Post") sticks to bottom or top without obscuring content.
3. **`/journal-entries`**
   - Data table scrolls horizontally.
   - Row expansion is easy to tap without accidental navigation.

## Results
- [x] Tested across targeted viewports. The layout breaks down gracefully from multi-column desktop to single-column mobile. Actions are accessible and horizontal scrolling is contained where necessary.
