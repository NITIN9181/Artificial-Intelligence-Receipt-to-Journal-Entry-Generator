import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Phase 3 Approval Workflow', () => {
  test('Preparer submits to reviewer, reviewer rejects, preparer fixes, reviewer approves', async ({ browser }) => {
    // We need two browser contexts for the two users
    const preparerContext = await browser.newContext();
    const reviewerContext = await browser.newContext();

    const preparerPage = await preparerContext.newPage();
    const reviewerPage = await reviewerContext.newPage();

    // 1. Preparer logs in, uploads receipt, triggers extraction, waits for EXTRACTED
    await preparerPage.goto('/login');
    await preparerPage.getByPlaceholder(/email/i).fill('preparer@example.com');
    await preparerPage.getByPlaceholder(/password/i).fill('password123');
    await preparerPage.getByRole('button', { name: /login|sign in/i }).click();
    await preparerPage.waitForURL('**/dashboard');

    await preparerPage.getByRole('link', { name: /upload/i }).click();
    const fileChooserPromise = preparerPage.waitForEvent('filechooser');
    await preparerPage.locator('input[type="file"]').click({ force: true }).catch(async () => {
       await preparerPage.getByText(/drag.*drop|click.*upload/i).click();
    });
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(path.join(__dirname, '../fixtures/sample-receipt.jpg'));

    await preparerPage.waitForURL('**/dashboard');
    await expect(preparerPage.getByText(/UPLOADED/i).first()).toBeVisible({ timeout: 15000 });
    await preparerPage.getByRole('button', { name: /extract/i }).first().click();
    await expect(preparerPage.getByText(/EXTRACTED/i, { exact: true }).first()).toBeVisible({ timeout: 90000 });

    // 2. Preparer navigates to /review/{id}, clicks "Approve" (not "Approve & Post" — just approve review)
    await preparerPage.getByRole('button', { name: /review/i }).first().click();
    await preparerPage.waitForURL(/.*\/review\/.+/);
    
    // Look for a secondary approve button, perhaps just 'Approve' without 'Post' or via a dropdown
    // For now assume there's a "Save" or "Approve Review" button
    await preparerPage.getByRole('button', { name: /^approve$/i }).first().click();

    // 3. Preparer navigates to /submissions, clicks "Submit for Review" on the receipt
    await preparerPage.goto('/submissions');
    await preparerPage.waitForLoadState('networkidle');
    await preparerPage.getByRole('button', { name: /submit for review/i }).first().click();

    // 4. Assert receipt status changes to "PENDING_REVIEW"
    await expect(preparerPage.getByText(/PENDING_REVIEW/i).first()).toBeVisible();

    // 5. Reviewer logs in (new browser context)
    await reviewerPage.goto('/login');
    await reviewerPage.getByPlaceholder(/email/i).fill('reviewer@example.com');
    await reviewerPage.getByPlaceholder(/password/i).fill('password123');
    await reviewerPage.getByRole('button', { name: /login|sign in/i }).click();
    await reviewerPage.waitForURL('**/dashboard');

    // 6. Reviewer navigates to /approval-queue
    await reviewerPage.getByRole('link', { name: /approval queue/i }).click();
    await reviewerPage.waitForURL('**/approval-queue');

    // 7. Assert the receipt appears in the queue with approve/reject buttons
    const queueRow = reviewerPage.locator('tbody tr').first();
    await expect(queueRow).toBeVisible();
    await expect(queueRow.getByRole('button', { name: /reject/i })).toBeVisible();
    await expect(queueRow.getByRole('button', { name: /approve/i })).toBeVisible();

    // 8. Reviewer clicks "Reject", enters comment "Please fix the date", submits
    await queueRow.getByRole('button', { name: /reject/i }).click();
    // Assuming a modal opens
    await reviewerPage.getByPlaceholder(/comment/i).fill('Please fix the date');
    await reviewerPage.getByRole('button', { name: /submit|confirm/i }).click();

    // 9. Assert status changes to "REJECTED", comment is visible
    await expect(reviewerPage.getByText(/REJECTED/i).first()).toBeVisible();
    
    // 10. Preparer (original context) refreshes /submissions, sees reviewer comment
    await preparerPage.reload();
    await expect(preparerPage.getByText(/Please fix the date/i)).toBeVisible();

    // 11. Preparer corrects the date, re-submits for review
    await preparerPage.getByRole('button', { name: /edit|fix/i }).first().click();
    // They edit the date (mocking by just saving again or resubmitting)
    const dateInput = preparerPage.getByLabel(/date/i);
    await dateInput.fill('2026-05-09');
    await dateInput.blur();
    await preparerPage.getByRole('button', { name: /save|update/i }).first().click();
    
    await preparerPage.goto('/submissions');
    await preparerPage.getByRole('button', { name: /submit for review/i }).first().click();

    // 12. Reviewer approves the receipt
    await reviewerPage.reload();
    const newQueueRow = reviewerPage.locator('tbody tr').first();
    await newQueueRow.getByRole('button', { name: /approve/i }).click();
    // Assuming confirmation modal
    await reviewerPage.getByRole('button', { name: /submit|confirm/i }).click();

    // 13. Assert status changes to "REVIEWED"
    await expect(reviewerPage.getByText(/REVIEWED/i).first()).toBeVisible();

    // 14. Preparer clicks "Journalize" → "Approve & Post"
    await preparerPage.reload();
    await preparerPage.getByRole('button', { name: /journalize|post/i }).first().click();

    // 15. Assert status becomes "POSTED"
    await expect(preparerPage.getByText(/POSTED/i).first()).toBeVisible();
  });
});
