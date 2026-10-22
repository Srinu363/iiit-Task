#!/bin/bash
# Smoke test for the deployed application.
# Run against a running docker-compose stack.

set -e

BASE_URL="${1:-http://localhost:3000}"
API_URL="${2:-http://localhost:8000}"

echo "=== Smoke Test ==="
echo "Frontend: $BASE_URL"
echo "Backend:  $API_URL"
echo ""

# 1. Health check
echo "1. Health check..."
HEALTH=$(curl -s "$API_URL/health")
echo "   $HEALTH"
echo "$HEALTH" | python -c "import sys,json; d=json.load(sys.stdin); assert d['status'] in ('healthy','degraded'), 'Health check failed'"
echo "   ✓ Health check passed"

# 2. Model info
echo "2. Model info..."
INFO=$(curl -s "$API_URL/api/v1/model-info")
echo "   Model version: $(echo $INFO | python -c 'import sys,json; print(json.load(sys.stdin).get("model_version","N/A"))')"
echo "   ✓ Model info passed"

# 3. Analyze an image
echo "3. Analyze image..."
# Create a small test image
python -c "
import cv2, numpy as np
img = np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8)
cv2.imwrite('test_smoke.png', img)
"

RESULT=$(curl -s -X POST "$API_URL/api/v1/analyze" \
  -F "file=@test_smoke.png" \
  -w "\n%{http_code}")
rm -f test_smoke.png
HTTP_CODE=$(echo "$RESULT" | tail -1)
BODY=$(echo "$RESULT" | head -n -1)

if [ "$HTTP_CODE" = "201" ]; then
    echo "   Score: $(echo $BODY | python -c 'import sys,json; print(json.load(sys.stdin)["quality_score"])')"
    echo "   Label: $(echo $BODY | python -c 'import sys,json; print(json.load(sys.stdin)["quality_label"])')"
    ANALYSIS_ID=$(echo $BODY | python -c 'import sys,json; print(json.load(sys.stdin)["id"])')
    echo "   ✓ Analysis passed (ID: $ANALYSIS_ID)"
else
    echo "   ✗ Analysis failed with HTTP $HTTP_CODE"
    echo "   $BODY"
    exit 1
fi

# 4. Get analysis by ID
echo "4. Get analysis by ID..."
curl -s "$API_URL/api/v1/analyses/$ANALYSIS_ID" | python -c "import sys,json; d=json.load(sys.stdin); print(f'   Score: {d[\"quality_score\"]}, Issues: {len(d[\"issues\"])}')"
echo "   ✓ Get analysis passed"

# 5. List analyses
echo "5. List analyses..."
LIST=$(curl -s "$API_URL/api/v1/analyses?page=1&page_size=5")
echo "   Total: $(echo $LIST | python -c 'import sys,json; print(json.load(sys.stdin)["total"])')"
echo "   ✓ List analyses passed"

# 6. Frontend loads
echo "6. Frontend check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ Frontend loads (HTTP $HTTP_CODE)"
else
    echo "   ✗ Frontend failed (HTTP $HTTP_CODE)"
fi

# 7. Delete analysis
echo "7. Delete analysis..."
curl -s -X DELETE "$API_URL/api/v1/analyses/$ANALYSIS_ID" -o /dev/null -w "   HTTP %{http_code}\n"
echo "   ✓ Delete passed"

echo ""
echo "=== All smoke tests passed ==="
