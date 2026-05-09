-- Phase 3 Migration Verification Script
-- Run this after applying migrations 010-013 to verify schema changes

-- ============================================================================
-- 1. Verify user_role enum exists
-- ============================================================================
SELECT 
    'user_role enum' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'user_role'
        ) THEN '✓ PASS'
        ELSE '✗ FAIL'
    END AS status;

-- Show enum values
SELECT 
    'user_role values' AS check_name,
    enumlabel AS value
FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'user_role')
ORDER BY enumsortorder;

-- ============================================================================
-- 2. Verify users table has role column (not is_admin)
-- ============================================================================
SELECT 
    'users.role column' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
        ) THEN '✓ PASS'
        ELSE '✗ FAIL'
    END AS status;

SELECT 
    'users.is_admin removed' AS check_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_admin'
        ) THEN '✓ PASS'
        ELSE '✗ FAIL - is_admin still exists'
    END AS status;

-- Show user roles distribution
SELECT 
    'User roles distribution' AS info,
    role,
    COUNT(*) AS count
FROM users
GROUP BY role
ORDER BY role;

-- ============================================================================
-- 3. Verify PENDING_REVIEW status in receipt_status enum
-- ============================================================================
SELECT 
    'PENDING_REVIEW status' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'PENDING_REVIEW' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'receipt_status')
        ) THEN '✓ PASS'
        ELSE '✗ FAIL'
    END AS status;

-- Show all receipt statuses
SELECT 
    'receipt_status values' AS check_name,
    enumlabel AS value
FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'receipt_status')
ORDER BY enumsortorder;

-- ============================================================================
-- 4. Verify gnucash_mappings table exists
-- ============================================================================
SELECT 
    'gnucash_mappings table' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'gnucash_mappings'
        ) THEN '✓ PASS'
        ELSE '✗ FAIL'
    END AS status;

-- Show gnucash_mappings columns
SELECT 
    'gnucash_mappings columns' AS info,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'gnucash_mappings'
ORDER BY ordinal_position;

-- Verify unique constraint
SELECT 
    'gnucash_mappings unique constraint' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE table_name = 'gnucash_mappings' 
            AND constraint_type = 'UNIQUE'
            AND constraint_name = 'uq_user_internal_code'
        ) THEN '✓ PASS'
        ELSE '✗ FAIL'
    END AS status;

-- Verify index
SELECT 
    'gnucash_mappings index' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE tablename = 'gnucash_mappings' 
            AND indexname = 'idx_gnucash_mappings_user_id'
        ) THEN '✓ PASS'
        ELSE '✗ FAIL'
    END AS status;

-- ============================================================================
-- 5. Verify review_comments table exists
-- ============================================================================
SELECT 
    'review_comments table' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'review_comments'
        ) THEN '✓ PASS'
        ELSE '✗ FAIL'
    END AS status;

-- Show review_comments columns
SELECT 
    'review_comments columns' AS info,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'review_comments'
ORDER BY ordinal_position;

-- Verify check constraint
SELECT 
    'review_comments check constraint' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE table_name = 'review_comments' 
            AND constraint_type = 'CHECK'
            AND constraint_name = 'check_review_action'
        ) THEN '✓ PASS'
        ELSE '✗ FAIL'
    END AS status;

-- Verify indexes
SELECT 
    'review_comments indexes' AS info,
    indexname
FROM pg_indexes 
WHERE tablename = 'review_comments'
ORDER BY indexname;

-- ============================================================================
-- 6. Verify foreign key relationships
-- ============================================================================
SELECT 
    'Foreign keys' AS info,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('gnucash_mappings', 'review_comments')
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================================
-- 7. Verify alembic version
-- ============================================================================
SELECT 
    'Alembic version' AS check_name,
    version_num,
    CASE 
        WHEN version_num = '013' THEN '✓ PASS - Phase 3 complete'
        WHEN version_num >= '010' THEN '⚠ PARTIAL - Some Phase 3 migrations applied'
        ELSE '✗ FAIL - Phase 3 not applied'
    END AS status
FROM alembic_version;

-- ============================================================================
-- 8. Sample data checks
-- ============================================================================

-- Count receipts by status
SELECT 
    'Receipts by status' AS info,
    status,
    COUNT(*) AS count
FROM receipts
GROUP BY status
ORDER BY status;

-- Count GnuCash mappings
SELECT 
    'GnuCash mappings' AS info,
    COUNT(*) AS total_mappings,
    COUNT(DISTINCT user_id) AS users_with_mappings
FROM gnucash_mappings;

-- Count review comments
SELECT 
    'Review comments' AS info,
    action,
    COUNT(*) AS count
FROM review_comments
GROUP BY action
ORDER BY action;

-- ============================================================================
-- 9. Data integrity checks
-- ============================================================================

-- Check for orphaned review comments (receipt deleted)
SELECT 
    'Orphaned review comments' AS check_name,
    CASE 
        WHEN COUNT(*) = 0 THEN '✓ PASS - No orphans'
        ELSE CONCAT('✗ FAIL - ', COUNT(*), ' orphaned comments')
    END AS status
FROM review_comments rc
LEFT JOIN receipts r ON rc.receipt_id = r.id
WHERE r.id IS NULL;

-- Check for orphaned GnuCash mappings (user deleted)
SELECT 
    'Orphaned GnuCash mappings' AS check_name,
    CASE 
        WHEN COUNT(*) = 0 THEN '✓ PASS - No orphans'
        ELSE CONCAT('✗ FAIL - ', COUNT(*), ' orphaned mappings')
    END AS status
FROM gnucash_mappings gm
LEFT JOIN users u ON gm.user_id = u.id
WHERE u.id IS NULL;

-- ============================================================================
-- 10. Summary
-- ============================================================================
SELECT 
    '========================================' AS summary,
    'Phase 3 Migration Verification Complete' AS message;

SELECT 
    'Next steps:' AS action,
    '1. Review all checks above' AS step_1,
    '2. All should show ✓ PASS' AS step_2,
    '3. If any ✗ FAIL, investigate' AS step_3,
    '4. Run backend tests: pytest tests/test_phase3_basic.py' AS step_4;
