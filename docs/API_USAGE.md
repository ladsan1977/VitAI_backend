# API Usage Guide

This guide provides detailed examples for using the VitAI Backend API with authentication.

## Table of Contents

- [Authentication](#authentication)
- [Session Management](#session-management)
- [Rate Limiting](#rate-limiting)
- [Endpoints Overview](#endpoints-overview)
- [AI Analysis Endpoints](#ai-analysis-endpoints)
- [Analytics Endpoints](#analytics-endpoints)
- [Health & Cache Endpoints](#health--cache-endpoints)
- [API Examples](#api-examples)
- [Error Handling](#error-handling)

## Authentication

### API Key Authentication

All AI analysis endpoints require API key authentication for security and rate limiting.

#### Generating an API Key

```bash
python -c "import secrets; print(f'vitai_sk_prod_{secrets.token_urlsafe(32)}')"
```

#### Setting Up Your API Key

Add the generated key to your `.env` file:

```env
API_KEY=vitai_sk_prod_your_generated_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Session Management

The API uses **anonymous session tracking** via cookies. No user accounts are required.

- A `session_id` cookie (UUID v4) is automatically generated on your first request
- The cookie is `HttpOnly` and `Secure` in production (HTTPS)
- Sessions persist for 1 year
- Session IDs are used to:
  - Track your analysis history
  - Associate AI consumption metrics with your usage
  - Enable the `/analytics/history` endpoint

> **Note**: If you're calling the API from a backend service (not a browser), the `session_id` is returned as a `Set-Cookie` header. You can store and resend it on subsequent requests to maintain session continuity.

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **20 requests per minute** per API key
- **100 requests per hour** per API key

### Rate Limit Response

When limits are exceeded:

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "error": "too_many_requests"
}
```

### Configuring Rate Limits

Adjust limits in your `.env` file:

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100
```

## Endpoints Overview

All endpoints require the `X-API-Key` header unless marked as public.

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | System health check (database + Redis) |
| `/api/v1/ai/analyze` | POST | Yes | Analyze product images with AI |
| `/api/v1/ai/health` | GET | No | AI service status |
| `/api/v1/ai/cache/stats` | GET | Yes | Redis cache statistics |
| `/api/v1/analytics/metrics` | GET | Yes | AI consumption metrics summary |
| `/api/v1/analytics/costs` | GET | Yes | OpenAI cost breakdown |
| `/api/v1/analytics/performance` | GET | Yes | Performance and cache efficiency |
| `/api/v1/analytics/history` | GET | Yes | Analysis history (current session) |
| `/api/v1/analytics/history/{id}` | GET | Yes | Full analysis details by ID |

---

## AI Analysis Endpoints

### `POST /api/v1/ai/analyze`

Analyze one or more product images using AI. Results are automatically deduplicated and persisted to the database using image hashing. If the same image is analyzed again, the cached result is returned instantly.

#### Parameters (multipart/form-data)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `images` | File(s) | Yes | - | Product images (JPEG, PNG, or WebP). Max 10MB each |
| `analysis_type` | string | No | `complete` | Type of analysis: `nutrition`, `ingredients`, or `complete` |
| `content_language` | string | No | `es` | Language for AI-generated content: `es` (Spanish) or `en` (English) |
| `user_profile` | string (JSON) | No | - | User health profile as JSON string |
| `dietary_preferences` | string | No | - | Comma-separated: `vegetarian`, `vegan`, `gluten-free`, etc. |
| `health_conditions` | string | No | - | Comma-separated health conditions for personalized recommendations |

#### Response Headers

| Header | Description |
|--------|-------------|
| `X-Response-Time` | Request processing time (e.g., `1234ms`) |
| `Set-Cookie` | Session ID cookie for tracking |

#### Response Body

Returns an `AIAnalysisResponse` object with product analysis, nutritional information, ingredient analysis, and health scoring.

---

## Analytics Endpoints

### `GET /api/v1/analytics/metrics`

Get a comprehensive AI consumption metrics summary for a time period.

#### Query Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `days` | integer | No | `7` | 1-90 | Number of days to analyze |

#### Response Example

```json
{
  "period_days": 7,
  "start_date": "2026-01-31T12:00:00",
  "end_date": "2026-02-07T12:00:00",
  "cache_hit_rate": 0.35,
  "cache_hit_percentage": 35.0,
  "total_requests": 142,
  "total_openai_cost_usd": 1.284,
  "average_response_time_ms": 2340.5,
  "token_usage": {
    "total_tokens": 125000,
    "prompt_tokens": 95000,
    "completion_tokens": 30000
  }
}
```

### `GET /api/v1/analytics/costs`

Get detailed OpenAI API cost analysis with projections.

#### Query Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `days` | integer | No | `30` | 1-365 | Number of days to analyze |

#### Response Example

```json
{
  "period_days": 30,
  "start_date": "2026-01-08T12:00:00",
  "end_date": "2026-02-07T12:00:00",
  "total_cost_usd": 5.42,
  "total_requests": 580,
  "cost_per_request_usd": 0.009345,
  "daily_average_cost_usd": 0.1807,
  "projected_monthly_cost_usd": 5.42,
  "token_usage": {
    "total_tokens": 540000,
    "prompt_tokens": 410000,
    "completion_tokens": 130000
  }
}
```

### `GET /api/v1/analytics/performance`

Get performance-focused metrics including response times and cache efficiency.

#### Query Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `days` | integer | No | `7` | 1-90 | Number of days to analyze |

#### Response Example

```json
{
  "period_days": 7,
  "start_date": "2026-01-31T12:00:00",
  "end_date": "2026-02-07T12:00:00",
  "average_response_time_ms": 2340.5,
  "cache_hit_rate": 0.35,
  "cache_hit_percentage": 35.0,
  "total_requests": 142,
  "estimated_time_saved_ms": 49700,
  "estimated_time_saved_hours": 0.01
}
```

### `GET /api/v1/analytics/history`

Get analysis history for the current session (based on the `session_id` cookie).

#### Query Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `limit` | integer | No | `10` | 1-50 | Maximum results to return |

#### Response Example

```json
{
  "history": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "product_name": "Cereal Integral",
      "analysis_type": "complete",
      "created_at": "2026-02-07T14:30:00"
    }
  ]
}
```

### `GET /api/v1/analytics/history/{analysis_id}`

Get full details of a specific analysis by its UUID.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `analysis_id` | string (UUID) | The analysis UUID from history |

#### Response Example

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "session_id": "f0e1d2c3-b4a5-6789-0fed-cba987654321",
  "product_name": "Cereal Integral",
  "analysis_type": "complete",
  "analysis_result": { "...full AI analysis..." },
  "created_at": "2026-02-07T14:30:00",
  "updated_at": "2026-02-07T14:30:00"
}
```

---

## Health & Cache Endpoints

### `GET /health`

System-wide health check. No authentication required.

```json
{
  "status": "ok",
  "env": "development",
  "version": "0.1.0",
  "services": {
    "redis": "healthy",
    "database": "healthy"
  }
}
```

### `GET /api/v1/ai/health`

AI service status. No authentication required.

```json
{
  "status": "ok",
  "service": "AI Analysis",
  "model": "gpt-5.1-chat-latest",
  "api": "responses",
  "features": ["nutrition_extraction", "ingredient_analysis", "health_scoring"]
}
```

### `GET /api/v1/ai/cache/stats`

Redis cache statistics. Requires API key.

---

## API Examples

### Using cURL

#### Basic Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze" \
  -H "X-API-Key: vitai_sk_prod_your_key_here" \
  -F "images=@product.jpg" \
  -F "analysis_type=complete"
```

#### Analysis in English

```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze" \
  -H "X-API-Key: vitai_sk_prod_your_key_here" \
  -F "images=@product.jpg" \
  -F "analysis_type=complete" \
  -F "content_language=en"
```

#### Multiple Images with Preferences

```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze" \
  -H "X-API-Key: vitai_sk_prod_your_key_here" \
  -F "images=@nutrition_facts.jpg" \
  -F "images=@ingredients.jpg" \
  -F "analysis_type=complete" \
  -F "content_language=es" \
  -F "dietary_preferences=vegetarian,gluten-free" \
  -F "health_conditions=diabetes,hypertension"
```

#### Get Metrics Summary (Last 7 Days)

```bash
curl "http://localhost:8000/api/v1/analytics/metrics?days=7" \
  -H "X-API-Key: vitai_sk_prod_your_key_here"
```

#### Get Cost Breakdown (Last 30 Days)

```bash
curl "http://localhost:8000/api/v1/analytics/costs?days=30" \
  -H "X-API-Key: vitai_sk_prod_your_key_here"
```

#### Get Performance Metrics

```bash
curl "http://localhost:8000/api/v1/analytics/performance?days=7" \
  -H "X-API-Key: vitai_sk_prod_your_key_here"
```

#### Get Analysis History

```bash
curl "http://localhost:8000/api/v1/analytics/history?limit=10" \
  -H "X-API-Key: vitai_sk_prod_your_key_here"
```

#### Get Analysis Details by ID

```bash
curl "http://localhost:8000/api/v1/analytics/history/a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "X-API-Key: vitai_sk_prod_your_key_here"
```

### Using Postman

1. **Method**: `POST`
2. **URL**: `http://localhost:8000/api/v1/ai/analyze`
3. **Headers**:
   - Key: `X-API-Key`
   - Value: `vitai_sk_prod_your_key_here`
4. **Body** (form-data):
   - `images`: [Select file]
   - `analysis_type`: `complete`
   - `content_language`: `es` (or `en` for English)

### Using Python

#### Using requests library

```python
import requests

BASE_URL = "http://localhost:8000"
API_KEY = "vitai_sk_prod_your_key_here"
HEADERS = {"X-API-Key": API_KEY}

# --- AI Analysis ---
files = {"images": open("product.jpg", "rb")}
data = {
    "analysis_type": "complete",
    "content_language": "es"  # "es" for Spanish, "en" for English
}

response = requests.post(
    f"{BASE_URL}/api/v1/ai/analyze",
    headers=HEADERS,
    files=files,
    data=data
)

if response.status_code == 200:
    result = response.json()
    print(f"Product: {result.get('product', {}).get('name')}")
    print(f"Response time: {response.headers.get('X-Response-Time')}")
else:
    print(f"Error: {response.status_code} - {response.json()}")

# --- Analytics: Metrics Summary ---
metrics = requests.get(
    f"{BASE_URL}/api/v1/analytics/metrics",
    headers=HEADERS,
    params={"days": 7}
).json()

print(f"Total requests: {metrics['total_requests']}")
print(f"Cache hit rate: {metrics['cache_hit_percentage']}%")
print(f"Total cost: ${metrics['total_openai_cost_usd']}")

# --- Analytics: Cost Breakdown ---
costs = requests.get(
    f"{BASE_URL}/api/v1/analytics/costs",
    headers=HEADERS,
    params={"days": 30}
).json()

print(f"Projected monthly cost: ${costs['projected_monthly_cost_usd']}")

# --- Analytics: Analysis History ---
history = requests.get(
    f"{BASE_URL}/api/v1/analytics/history",
    headers=HEADERS,
    params={"limit": 5}
).json()

for item in history["history"]:
    print(f"  - {item['product_name']} ({item['analysis_type']}) - {item['created_at']}")
```

#### Using httpx (async)

```python
import httpx
import asyncio

async def main():
    base_url = "http://localhost:8000"
    api_key = "vitai_sk_prod_your_key_here"
    headers = {"X-API-Key": api_key}

    async with httpx.AsyncClient() as client:
        # AI Analysis
        files = {"images": open("product.jpg", "rb")}
        data = {"analysis_type": "complete", "content_language": "es"}

        response = await client.post(
            f"{base_url}/api/v1/ai/analyze",
            headers=headers,
            files=files,
            data=data
        )
        analysis = response.json()
        print(f"Product: {analysis.get('product', {}).get('name')}")

        # Metrics summary
        metrics = await client.get(
            f"{base_url}/api/v1/analytics/metrics",
            headers=headers,
            params={"days": 7}
        )
        print(f"Cache hit rate: {metrics.json()['cache_hit_percentage']}%")

asyncio.run(main())
```

### Using JavaScript/TypeScript

#### Using Fetch API

```javascript
const BASE_URL = 'http://localhost:8000';
const API_KEY = 'vitai_sk_prod_your_key_here';
const headers = { 'X-API-Key': API_KEY };

// --- AI Analysis ---
const formData = new FormData();
formData.append('images', fileInput.files[0]);
formData.append('analysis_type', 'complete');
formData.append('content_language', 'es'); // 'es' for Spanish, 'en' for English

const response = await fetch(`${BASE_URL}/api/v1/ai/analyze`, {
  method: 'POST',
  headers,
  body: formData
});

const analysis = await response.json();
console.log('Product:', analysis.product?.name);
console.log('Response time:', response.headers.get('X-Response-Time'));

// --- Analytics: Metrics ---
const metrics = await fetch(`${BASE_URL}/api/v1/analytics/metrics?days=7`, { headers });
const metricsData = await metrics.json();
console.log(`Cache hit rate: ${metricsData.cache_hit_percentage}%`);
console.log(`Total cost: $${metricsData.total_openai_cost_usd}`);

// --- Analytics: History ---
const history = await fetch(`${BASE_URL}/api/v1/analytics/history?limit=5`, { headers });
const historyData = await history.json();
historyData.history.forEach(item => {
  console.log(`- ${item.product_name} (${item.analysis_type}) - ${item.created_at}`);
});
```

#### Using Axios

```javascript
import axios from 'axios';

const BASE_URL = 'http://localhost:8000';
const API_KEY = 'vitai_sk_prod_your_key_here';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'X-API-Key': API_KEY }
});

// AI Analysis
const formData = new FormData();
formData.append('images', fileInput.files[0]);
formData.append('analysis_type', 'complete');
formData.append('content_language', 'es');

try {
  const { data: analysis } = await api.post('/api/v1/ai/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  console.log(analysis);

  // Analytics
  const { data: metrics } = await api.get('/api/v1/analytics/metrics', { params: { days: 7 } });
  console.log(`Cache hit rate: ${metrics.cache_hit_percentage}%`);

  const { data: costs } = await api.get('/api/v1/analytics/costs', { params: { days: 30 } });
  console.log(`Projected monthly: $${costs.projected_monthly_cost_usd}`);
} catch (error) {
  console.error('Error:', error.response?.data || error.message);
}
```

#### Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const API_KEY = 'vitai_sk_prod_your_key_here';
const BASE_URL = 'http://localhost:8000';

// AI Analysis
const formData = new FormData();
formData.append('images', fs.createReadStream('product.jpg'));
formData.append('analysis_type', 'complete');
formData.append('content_language', 'es');

axios.post(`${BASE_URL}/api/v1/ai/analyze`, formData, {
  headers: { 'X-API-Key': API_KEY, ...formData.getHeaders() }
})
.then(response => console.log(response.data))
.catch(error => console.error(error.response?.data || error.message));

// Analytics
axios.get(`${BASE_URL}/api/v1/analytics/metrics`, {
  headers: { 'X-API-Key': API_KEY },
  params: { days: 7 }
})
.then(response => console.log('Metrics:', response.data))
.catch(error => console.error(error.response?.data || error.message));
```

### Using Go

```go
package main

import (
    "bytes"
    "fmt"
    "io"
    "mime/multipart"
    "net/http"
    "os"
)

const (
    baseURL = "http://localhost:8000"
    apiKey  = "vitai_sk_prod_your_key_here"
)

func main() {
    // --- AI Analysis ---
    body := &bytes.Buffer{}
    writer := multipart.NewWriter(body)

    file, err := os.Open("product.jpg")
    if err != nil {
        panic(err)
    }
    defer file.Close()

    part, err := writer.CreateFormFile("images", "product.jpg")
    if err != nil {
        panic(err)
    }
    io.Copy(part, file)

    writer.WriteField("analysis_type", "complete")
    writer.WriteField("content_language", "es") // "es" for Spanish, "en" for English
    writer.Close()

    req, _ := http.NewRequest("POST", baseURL+"/api/v1/ai/analyze", body)
    req.Header.Set("X-API-Key", apiKey)
    req.Header.Set("Content-Type", writer.FormDataContentType())

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    respBody, _ := io.ReadAll(resp.Body)
    fmt.Println("Analysis:", string(respBody))
    fmt.Println("Response Time:", resp.Header.Get("X-Response-Time"))

    // --- Analytics: Metrics ---
    metricsReq, _ := http.NewRequest("GET", baseURL+"/api/v1/analytics/metrics?days=7", nil)
    metricsReq.Header.Set("X-API-Key", apiKey)

    metricsResp, err := client.Do(metricsReq)
    if err != nil {
        panic(err)
    }
    defer metricsResp.Body.Close()

    metricsBody, _ := io.ReadAll(metricsResp.Body)
    fmt.Println("Metrics:", string(metricsBody))
}
```

## Error Handling

### Missing API Key (403 Forbidden)

```json
{
  "detail": "API key is missing. Please provide an API key in the X-API-Key header."
}
```

**Solution**: Include the `X-API-Key` header in your request.

### Invalid API Key (403 Forbidden)

```json
{
  "detail": "Invalid API key. Please check your credentials."
}
```

**Solution**: Verify your API key matches the one in your `.env` file.

### No Images Provided (400 Bad Request)

```json
{
  "detail": "At least one image must be provided for analysis"
}
```

**Solution**: Attach at least one image file to the `images` form field.

### Rate Limit Exceeded (429 Too Many Requests)

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "error": "too_many_requests"
}
```

**Solution**: Wait before making additional requests. Implement exponential backoff in your client.

### Analysis Not Found (404 Not Found)

```json
{
  "detail": "Analysis not found"
}
```

**Solution**: Verify the `analysis_id` UUID exists. Use the `/analytics/history` endpoint to list available analyses.

### Validation Error (422 Unprocessable Entity)

```json
{
  "detail": [
    {
      "loc": ["body", "analysis_type"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solution**: Check that all required fields are included in your request.

### AI Service Unavailable (500 Internal Server Error)

```json
{
  "detail": "AI analysis service temporarily unavailable"
}
```

**Solution**: The OpenAI service is temporarily unavailable. Retry the request after a short delay.

## Best Practices

1. **Store API Keys Securely**: Never hardcode API keys in your source code. Use environment variables.

2. **Implement Retry Logic**: Handle rate limits with exponential backoff:
   ```python
   import time
   from requests.exceptions import HTTPError

   def make_request_with_retry(url, headers, files, data, max_retries=3):
       for attempt in range(max_retries):
           try:
               response = requests.post(url, headers=headers, files=files, data=data)
               response.raise_for_status()
               return response.json()
           except HTTPError as e:
               if e.response.status_code == 429 and attempt < max_retries - 1:
                   wait_time = 2 ** attempt
                   time.sleep(wait_time)
               else:
                   raise
   ```

3. **Handle Errors Gracefully**: Always check response status codes and handle errors appropriately.

4. **Close File Handles**: When uploading files, ensure they are properly closed after the request.

5. **Use HTTPS in Production**: Always use HTTPS endpoints in production environments.

6. **Leverage Deduplication**: The API automatically deduplicates analyses based on image content hashing. Sending the same image twice will return the cached result instantly without consuming OpenAI tokens.

7. **Monitor Costs**: Use the `/analytics/costs` endpoint regularly to track OpenAI spending and projected monthly costs.

8. **Set Content Language**: Use the `content_language` parameter (`es` or `en`) to receive AI-generated analysis content in your preferred language. Defaults to Spanish (`es`).

## Interactive API Documentation

For interactive API testing, visit the auto-generated Swagger documentation:

- Local: http://localhost:8000/docs
- Production: https://your-domain.com/docs

The Swagger UI allows you to:
- Test endpoints directly in the browser
- See request/response schemas
- Try different parameters
- View authentication requirements
