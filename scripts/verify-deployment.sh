#!/bin/bash
set -e

BACKEND_URL="https://your-backend.onrender.com"
FRONTEND_URL="https://your-app.vercel.app"
SUPABASE_URL="https://your-project.supabase.co"

echo "=== 1. Backend Health ==="
curl -s "$BACKEND_URL/api/v1/health" | jq .
# Expected: {"status": "ok", "db": "connected", ...}

echo "=== 2. Frontend Loads ==="
curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL"
# Expected: 200

echo "=== 3. Supabase Auth Accessible ==="
curl -s -o /dev/null -w "%{http_code}" "$SUPABASE_URL/auth/v1/health"
# Expected: 200

echo "=== 4. Database Migrations Current ==="
cd backend
alembic current
# Expected: 013 (head)

echo "=== 5. CORS Check ==="
curl -s -X OPTIONS "$BACKEND_URL/api/v1/health" \
  -H "Origin: $FRONTEND_URL" \
  -H "Access-Control-Request-Method: GET" \
  -v 2>&1 | grep -i "access-control-allow-origin"
# Expected: Header present with frontend URL
