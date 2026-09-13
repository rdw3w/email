# Email Breach Finder API 🔍

Advanced email breach detection API with modern UI/UX, built by **rdw3w** (@NST_YZ_09).

## Features ✨

- **Email Search**: Check if email has been compromised
- **Rate Limiting**: 100 requests per hour per IP
- **Batch Search**: Search multiple emails at once
- **Health Checks**: API status monitoring
- **Statistics**: Comprehensive breach statistics
- **Modern UI**: Beautiful, responsive web interface
- **API Versioning**: v2.0 with backward compatibility
- **Multiple Formats**: JSON and XML response formats
- **Request Tracking**: Unique request IDs for each search
- **Error Handling**: Comprehensive error messages

## API Endpoints 🛣️

### 1. **Health Check**
```
GET /api/health
```
Check API status.

### 2. **Email Search** (Main)
```
GET /api/search?mail=email@example.com&breaches=true&history=false
```

**Parameters:**
- `mail` (required): Email to search
- `breaches` (optional): Include breach data (true/false)
- `history` (optional): Include search history (true/false)
- `format` (optional): Response format (json/xml)

**Response:**
```json
{
  "meta": {
    "request_id": "abc123xyz",
    "timestamp": "2024-09-13T10:30:45.123456",
    "version": "2.0",
    "response_time_ms": 245.67,
    "status": "success"
  },
  "searcher": {
    "name": "rdw3w",
    "username": "@NST_YZ_09",
    "verified": true
  },
  "search_query": {
    "email": "test@example.com",
    "include_breaches": true,
    "include_history": false
  },
  "breaches": [...],
  "statistics": {
    "total_breaches": 2,
    "compromised_accounts": 5
  }
}
```

### 3. **Batch Search**
```
POST /api/batch-search
Content-Type: application/json

{
  "emails": ["email1@example.com", "email2@example.com"]
}
```

### 4. **Statistics**
```
GET /api/stats
```
Get API statistics and available endpoints.

## Installation 🚀

1. **Clone the repository**
```bash
git clone https://github.com/rdw3w/email.git
cd email
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set environment variables**
```bash
export API_KEY=your_secret_key_2024
```

4. **Run locally**
```bash
python mail.py
```

5. **Access the UI**
Open `http://localhost:5000` in your browser

## Deployment 🌐

### Vercel Deployment
```bash
vercel deploy
```

Add environment variable in Vercel dashboard:
- `API_KEY`: Your secret API key

## Rate Limiting ⚡

- **Limit**: 100 requests per hour
- **Window**: 3600 seconds
- **Response**: 429 Too Many Requests

## Security 🔒

- API Key validation (X-API-Key header)
- Input validation & sanitization
- CORS enabled
- Rate limiting per IP
- Request timeout (30s)
- Secure headers

## Error Codes 🚨

- `400`: Bad Request (missing/invalid parameters)
- `401`: Unauthorized (invalid API key)
- `404`: Not Found
- `429`: Rate Limited
- `502`: Bad Gateway
- `504`: Gateway Timeout
- `500`: Server Error

## Usage Examples 📚

### JavaScript/Fetch
```javascript
const response = await fetch('/api/search?mail=test@example.com');
const data = await response.json();
console.log(data);
```

### cURL
```bash
curl "http://localhost:5000/api/search?mail=test@example.com" \
  -H "X-API-Key: your_api_key"
```

### Python Requests
```python
import requests

response = requests.get(
    'http://localhost:5000/api/search',
    params={'mail': 'test@example.com'},
    headers={'X-API-Key': 'your_api_key'}
)
print(response.json())
```

## Technology Stack 🛠️

- **Backend**: Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Deployment**: Vercel
- **Python**: 3.8+

## Author 👨‍💻

**rdw3w** - [@NST_YZ_09](https://github.com/NST_YZ_09)

## License 📄

MIT License - See LICENSE file for details

## Contributing 🤝

Contributions welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

**Made with ❤️ by rdw3w**
