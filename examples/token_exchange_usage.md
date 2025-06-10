# Token Exchange Usage Examples

## CLI Command Usage

### 1. Using with provided subject token (for testing):

```bash
dnastack auth token-exchange \
  --token-endpoint "http://localhost:8081/oauth/token" \
  --resource "http://localhost:8081" \
  --subject-token "eyJhbGciOiJSUzI1NiIsImtpZCI6ImJiNDM0Njk1OTQ0NTE4MjAxNDhiMzM5YzU4OGFlZGUzMDUxMDM5MTkiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJodHRwOi8vbG9jYWxob3N0OjgwODEiLCJhenAiOiIxMDA0ODMyODc2MTI2MjMxNDIxMTYiLCJlbWFpbCI6IjIxNzcwNjk0NzQ5NS1jb21wdXRlQGRldmVsb3Blci5nc2VydmljZWFjY291bnQuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImV4cCI6MTc0OTU3NjgyMCwiZ29vZ2xlIjp7ImNvbXB1dGVfZW5naW5lIjp7Imluc3RhbmNlX2NyZWF0aW9uX3RpbWVzdGFtcCI6MTczMTQyNTg2NCwiaW5zdGFuY2VfaWQiOiIzMDQ3OTM0MDUwMjEwNTk3MDMzIiwiaW5zdGFuY2VfbmFtZSI6ImZlZG1sLXNlcnZlciIsInByb2plY3RfaWQiOiJzdHJpa2luZy1lZmZvcnQtODE3IiwicHJvamVjdF9udW1iZXIiOjIxNzcwNjk0NzQ5NSwiem9uZSI6InVzLWNlbnRyYWwxLWMifX0sImlhdCI6MTc0OTU3MzIyMCwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tIiwic3ViIjoiMTAwNDgzMjg3NjEyNjIzMTQyMTE2In0.nIelSUaIvXTottGbkcrSjiJkPdorkTjMAsrspOkOWLbPmmGADdQTjXwvd_l1-WIfM2DYbFsWwWeohF54SPD4qXizIEGGtoOIpclN61EY6fOj5qrNTjxZFlR4yfgrVDAD9FmVKnYFsq5JEu_yYsxzYTq5uvxTIn6jch6Z1AJ7O-7TZlm-Wm-uX2xYYJzjMZvVp9tgzL8cWavJf3wVLXzkfKYO5qNcseBtcazqIcueSTsLz6JA4q3iIm9Vpf5WbLOzaEDvzvxIFTi-JPrlTbhOM4EKPMuPnKdR9KtpMZ6rRe7ZVPG5BCVimmfmcNUCupO9I-ZEf8Vb4CWXQQQ3c5VMjA"
```

### 2. Using with automatic GCP metadata token fetch (when running on GCP VM):

```bash
# This will automatically fetch the ID token from GCP metadata service
dnastack auth token-exchange \
  --token-endpoint "http://localhost:8081/oauth/token" \
  --resource "http://localhost:8185" \
  --audience "https://workbench.beta.dnastack.com"
```

### 3. Using with production endpoints:

```bash
dnastack auth token-exchange \
  --token-endpoint "https://wallet.viral.ai/oauth/token" \
  --resource "https://collection-service.viral.ai/" \
  --audience "https://workbench.beta.dnastack.com"
```

## Programmatic Usage

### Setting up an endpoint with token exchange authentication:

```bash
# Add endpoint
dnastack config endpoints add wallet-exchange -t oauth2

# Configure for token exchange
dnastack config endpoints set wallet-exchange url "http://localhost:8081"
dnastack config endpoints set wallet-exchange authentication.grant_type "urn:ietf:params:oauth:grant-type:token-exchange"
dnastack config endpoints set wallet-exchange authentication.token_endpoint "http://localhost:8081/oauth/token"
dnastack config endpoints set wallet-exchange authentication.resource_url "http://localhost:8185"
dnastack config endpoints set wallet-exchange authentication.subject_token_type "urn:ietf:params:oauth:token-type:jwt"

# Optional: provide a subject token
dnastack config endpoints set wallet-exchange authentication.subject_token "YOUR_ID_TOKEN_HERE"

# Login using the configured endpoint
dnastack auth login --endpoint-id wallet-exchange
```

## Direct CURL equivalent

The token exchange command performs the equivalent of:

```bash
curl --request POST \
  --url http://localhost:8081/oauth/token \
  --header 'Authorization: Basic ZG5hc3RhY2stY2xpZW50OmRldi1zZWNyZXQtbmV2ZXItdXNlLWluLXByb2Q=' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data grant_type=urn:ietf:params:oauth:grant-type:token-exchange \
  --data subject_token_type=urn:ietf:params:oauth:token-type:jwt \
  --data subject_token=YOUR_ID_TOKEN \
  --data resource=http://localhost:8185
```

## Notes

- The adapter automatically uses the explorer public client credentials (dnastack-client/dev-secret-never-use-in-prod)
- If no subject token is provided, it attempts to fetch from GCP metadata service
- The audience parameter is used when fetching from GCP metadata (defaults to resource URL)
