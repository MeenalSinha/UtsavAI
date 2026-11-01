# UtsavAI Production Smoke Tests

## 1. Automated Smoke Verification Suite
Execute these tests immediately after any deployment to staging or production:

```bash
API_URL="https://api.utsavai.com"
WEB_URL="https://app.utsavai.com"

# 1. Liveness check
curl -f -s "$API_URL/api/v1/health" | grep '"status":"ok"' || exit 1

# 2. Readiness check (Database connectivity & role verification)
curl -f -s "$API_URL/api/v1/health/ready" | grep '"status":"ready"' || exit 1

# 3. Security headers check
curl -s -I "$WEB_URL" | grep -i "content-security-policy" || exit 1
curl -s -I "$WEB_URL" | grep -i "strict-transport-security" || exit 1

# 4. Public legal disclosures reachable
curl -f -s "$WEB_URL/privacy" > /dev/null || exit 1
curl -f -s "$WEB_URL/terms" > /dev/null || exit 1
curl -f -s "$WEB_URL/ai-disclosure" > /dev/null || exit 1

echo "All production smoke tests PASSED."
```
