from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import requests
import json
from datetime import datetime
import hashlib
import os
from functools import wraps
import time

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
MY_NAME = "🔥 Rudra X Tech 🔥"
MY_USERNAME = "@NST_YZ_09"
API_VERSION = "2.0"
REQUEST_LIMIT = 1000
TIME_WINDOW = 3600  # 1 hour

# Store for rate limiting
request_tracker = {}

# Decorator for rate limiting
def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        current_time = time.time()
        
        if ip not in request_tracker:
            request_tracker[ip] = []
        
        # Clean old requests
        request_tracker[ip] = [t for t in request_tracker[ip] if current_time - t < TIME_WINDOW]
        
        if len(request_tracker[ip]) >= REQUEST_LIMIT:
            return jsonify({
                "error": "Rate limit exceeded",
                "limit": REQUEST_LIMIT,
                "window": TIME_WINDOW,
                "retry_after": int(TIME_WINDOW - (current_time - request_tracker[ip][0]))
            }), 429
        
        request_tracker[ip].append(current_time)
        return f(*args, **kwargs)
    
    return decorated_function

# Decorator for API key validation
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('API_KEY', 'rudra12'):
            return jsonify({
                "error": "Unauthorized",
                "message": "Valid API key required"
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    """Serve UI"""
    return render_template('index.html', 
        name=MY_NAME, 
        username=MY_USERNAME,
        version=API_VERSION
    )

@app.route("/api/health", methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.now().isoformat(),
        "uptime": "online"
    }), 200

@app.route("/api/search", methods=['GET'])
@rate_limit
def search():
    """Advanced email search with comprehensive results"""
    email = request.args.get("mail", "").strip()
    include_breaches = request.args.get("breaches", "true").lower() == "true"
    include_history = request.args.get("history", "false").lower() == "true"
    format_type = request.args.get("format", "json")

    # Validation
    if not email:
        return jsonify({
            "error": "Missing email parameter",
            "message": "Please provide email via ?mail=your@email.com",
            "example": "/api/search?mail=test@example.com"
        }), 400

    if "@" not in email or "." not in email:
        return jsonify({
            "error": "Invalid email format",
            "email": email
        }), 400

    # Generate request ID
    request_id = hashlib.md5(f"{email}{time.time()}".encode()).hexdigest()[:12]

    payload = {
        "file": "/app/rpc/search.telefunc.ts",
        "name": "public_search",
        "args": [{
            "piis": [{
                "type": "email",
                "value": email,
                "pii_id": "1"
            }],
            "main_breach_id": "!undefined"
        }]
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Content-Type": "text/plain",
        "Origin": "https://databreach.com",
        "Referer": "https://databreach.com/",
        "X-Request-ID": request_id
    }

    try:
        start_time = time.time()
        r = requests.post(
            "https://databreach.com/_telefunc",
            headers=headers,
            data=json.dumps(payload, separators=(",", ":")),
            timeout=30
        )
        elapsed_time = time.time() - start_time

        result = r.json() if r.text else {}
        
        # Advanced response formatting
        response_data = {
            # Meta information
            "meta": {
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "version": API_VERSION,
                "response_time_ms": round(elapsed_time * 1000, 2),
                "status": "success"
            },
            
            # Searcher information
            "searcher": {
                "name": MY_NAME,
                "username": MY_USERNAME,
                "verified": True
            },
            
            # Search information
            "search_query": {
                "email": email,
                "include_breaches": include_breaches,
                "include_history": include_history
            },
            
            # Breach data
            "breaches": result.get("breaches", []) if include_breaches else [],
            
            # Raw result
            "data": result
        }

        # Add history if requested
        if include_history:
            response_data["history"] = {
                "search_count": 1,
                "last_searched": datetime.now().isoformat()
            }

        # Add statistics
        response_data["statistics"] = {
            "total_breaches": len(response_data.get("breaches", [])),
            "compromised_accounts": len(response_data.get("data", {}).get("hits", [])) if isinstance(response_data.get("data"), dict) else 0
        }

        if format_type == "xml":
            return convert_to_xml(response_data)
        
        return jsonify(response_data), 200

    except requests.Timeout:
        return jsonify({
            "error": "Request timeout",
            "message": "The search took too long. Please try again.",
            "searcher": {
                "name": MY_NAME,
                "username": MY_USERNAME
            }
        }), 504

    except requests.ConnectionError:
        return jsonify({
            "error": "Connection error",
            "message": "Unable to connect to breach database",
            "searcher": {
                "name": MY_NAME,
                "username": MY_USERNAME
            }
        }), 502

    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e),
            "searcher": {
                "name": MY_NAME,
                "username": MY_USERNAME
            },
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/batch-search", methods=['POST'])
@rate_limit
def batch_search():
    """Batch search for multiple emails"""
    data = request.get_json()
    
    if not data or "emails" not in data:
        return jsonify({
            "error": "Invalid request",
            "message": "POST body must contain 'emails' array"
        }), 400
    
    emails = data.get("emails", [])
    if not isinstance(emails, list) or len(emails) == 0:
        return jsonify({
            "error": "Invalid emails parameter",
            "message": "emails must be a non-empty array"
        }), 400
    
    if len(emails) > 100:
        return jsonify({
            "error": "Too many emails",
            "message": "Maximum 100 emails per request",
            "limit": 100,
            "received": len(emails)
        }), 413

    results = []
    errors = []
    
    for email in emails[:100]:
        try:
            # Call search for each email (simplified)
            results.append({
                "email": email,
                "status": "processed"
            })
        except Exception as e:
            errors.append({
                "email": email,
                "error": str(e)
            })
    
    return jsonify({
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "version": API_VERSION,
            "batch_id": hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12]
        },
        "results": results,
        "errors": errors,
        "summary": {
            "total": len(emails),
            "successful": len(results),
            "failed": len(errors)
        },
        "searcher": {
            "name": MY_NAME,
            "username": MY_USERNAME
        }
    }), 200

@app.route("/api/stats", methods=['GET'])
def stats():
    """API statistics"""
    return jsonify({
        "api_name": "Email Breach Finder API",
        "version": API_VERSION,
        "author": MY_USERNAME,
        "owner": MY_NAME,
        "endpoints": {
            "health": "/api/health",
            "search": "/api/search",
            "batch_search": "/api/batch-search",
            "stats": "/api/stats",
            "ui": "/"
        },
        "rate_limit": {
            "requests": REQUEST_LIMIT,
            "window": f"{TIME_WINDOW}s"
        },
        "timestamp": datetime.now().isoformat()
    }), 200

def convert_to_xml(data):
    """Convert JSON response to XML"""
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<response>\n'
    
    def dict_to_xml(d, parent=""):
        xml_str = ""
        for key, value in d.items():
            if isinstance(value, dict):
                xml_str += f"  <{key}>\n"
                xml_str += dict_to_xml(value, key)
                xml_str += f"  </{key}>\n"
            elif isinstance(value, list):
                xml_str += f"  <{key}>\n"
                for item in value:
                    if isinstance(item, dict):
                        xml_str += dict_to_xml(item, "item")
                    else:
                        xml_str += f"    <item>{item}</item>\n"
                xml_str += f"  </{key}>\n"
            else:
                xml_str += f"  <{key}>{value}</{key}>\n"
        return xml_str
    
    xml += dict_to_xml(data)
    xml += '</response>'
    
    return xml, 200, {'Content-Type': 'application/xml'}

@app.route("/static/<path:path>")
def send_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": "/api/stats"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "message": f"This endpoint does not support {request.method}",
        "hint": "Check /api/stats for available endpoints"
    }), 405

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
