# API Usage Guide

This guide provides detailed examples for using the VitAI Backend API with authentication.

## Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
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

## API Examples

### Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze" \
  -H "X-API-Key: vitai_sk_prod_your_key_here" \
  -F "images=@product.jpg" \
  -F "analysis_type=complete"
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

### Using Python

#### Using requests library

```python
import requests

# Setup
api_url = "http://localhost:8000/api/v1/ai/analyze"
api_key = "vitai_sk_prod_your_key_here"

headers = {
    "X-API-Key": api_key
}

files = {
    "images": open("product.jpg", "rb")
}

data = {
    "analysis_type": "complete"
}

# Make request
response = requests.post(
    api_url,
    headers=headers,
    files=files,
    data=data
)

# Handle response
if response.status_code == 200:
    result = response.json()
    print(result)
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

#### Using httpx (async)

```python
import httpx
import asyncio

async def analyze_product():
    api_url = "http://localhost:8000/api/v1/ai/analyze"
    api_key = "vitai_sk_prod_your_key_here"

    headers = {
        "X-API-Key": api_key
    }

    files = {
        "images": open("product.jpg", "rb")
    }

    data = {
        "analysis_type": "complete"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            headers=headers,
            files=files,
            data=data
        )
        return response.json()

# Run
result = asyncio.run(analyze_product())
print(result)
```

### Using JavaScript/TypeScript

#### Using Fetch API

```javascript
const formData = new FormData();
formData.append('images', fileInput.files[0]);
formData.append('analysis_type', 'complete');

const response = await fetch('http://localhost:8000/api/v1/ai/analyze', {
  method: 'POST',
  headers: {
    'X-API-Key': 'vitai_sk_prod_your_key_here'
  },
  body: formData
});

const data = await response.json();
console.log(data);
```

#### Using Axios

```javascript
import axios from 'axios';

const formData = new FormData();
formData.append('images', fileInput.files[0]);
formData.append('analysis_type', 'complete');

try {
  const response = await axios.post(
    'http://localhost:8000/api/v1/ai/analyze',
    formData,
    {
      headers: {
        'X-API-Key': 'vitai_sk_prod_your_key_here',
        'Content-Type': 'multipart/form-data'
      }
    }
  );
  console.log(response.data);
} catch (error) {
  console.error('Error:', error.response?.data || error.message);
}
```

#### Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const formData = new FormData();
formData.append('images', fs.createReadStream('product.jpg'));
formData.append('analysis_type', 'complete');

axios.post('http://localhost:8000/api/v1/ai/analyze', formData, {
  headers: {
    'X-API-Key': 'vitai_sk_prod_your_key_here',
    ...formData.getHeaders()
  }
})
.then(response => console.log(response.data))
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

func main() {
    url := "http://localhost:8000/api/v1/ai/analyze"
    apiKey := "vitai_sk_prod_your_key_here"

    // Create multipart form
    body := &bytes.Buffer{}
    writer := multipart.NewWriter(body)

    // Add file
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

    // Add fields
    writer.WriteField("analysis_type", "complete")
    writer.Close()

    // Create request
    req, err := http.NewRequest("POST", url, body)
    if err != nil {
        panic(err)
    }

    req.Header.Set("X-API-Key", apiKey)
    req.Header.Set("Content-Type", writer.FormDataContentType())

    // Send request
    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    // Read response
    respBody, _ := io.ReadAll(resp.Body)
    fmt.Println(string(respBody))
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

### Rate Limit Exceeded (429 Too Many Requests)

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "error": "too_many_requests"
}
```

**Solution**: Wait before making additional requests. Implement exponential backoff in your client.

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

## Interactive API Documentation

For interactive API testing, visit the auto-generated Swagger documentation:

- Local: http://localhost:8000/docs
- Production: https://your-domain.com/docs

The Swagger UI allows you to:
- Test endpoints directly in the browser
- See request/response schemas
- Try different parameters
- View authentication requirements
