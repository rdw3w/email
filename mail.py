from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import requests
import json
from datetime import datetime
import hashlib
import os
from functools import wraps
import time
import re
from xml.sax.saxutils import escape
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
MY_NAME = "🔥 Rudra X Tech 🔥"
MY_USERNAME = "@NST_YZ_09"
API_VERSION = "3.0"
REQUEST_LIMIT = 100  # Requests per hour
TIME_WINDOW = 3600  # 1 hour

# Store for rate limiting
request_tracker = {}

# ==================== DECORATORS ====================

def rate_limit(f):
    """Decorator for rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        current_time = time.time()
        
        if ip not in request_tracker:
            request_tracker[ip] = []
        
        # Clean old requests
        request_tracker[ip] = [t for t in request_tracker[ip] if current_time - t < TIME_WINDOW]
        
        if len(request_tracker[ip]) >= REQUEST_LIMIT:
            retry_after = int(TIME_WINDOW - (current_time - request_tracker[ip][0]))
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return jsonify({
                "error": "Rate limit exceeded",
                "limit": REQUEST_LIMIT,
                "window": f"{TIME_WINDOW}s",
                "retry_after": retry_after,
                "message": f"Max {REQUEST_LIMIT} requests per hour"
            }), 429
        
        request_tracker[ip].append(current_time)
        return f(*args, **kwargs)
    
    return decorated_function

# ==================== VALIDATION FUNCTIONS ====================

def is_valid_email(email):
    """Validate email format using RFC 5322 simplified regex"""
    if not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text):
    """Sanitize user input"""
    if not isinstance(text, str):
        return ""
    return text.strip()[:500]  # Max 500 chars

# ==================== ROUTES ====================

@app.route("/")
def home():
    """Serve UI"""
    try:
        return render_template('index.html', 
            name=MY_NAME, 
            username=MY_USERNAME,
            version=API_VERSION
        )
    except Exception as e:
        logger.error(f"Error rendering home: {str(e)}")
        return jsonify({
            "status": "ready",
            "message": "Email Breach Finder API",
            "version": API_VERSION,
            "endpoints": ["/api/health", "/api/search", "/api/batch-search", "/api/stats"]
        }), 200

@app.route("/api/health", methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": datetime.now().isoformat(),
        "uptime": "online",
        "environment": "production" if os.getenv('ENVIRONMENT') == 'prod' else "development"
    }), 200

@app.route("/api/search", methods=['GET'])
@rate_limit
def search():
    """Advanced email search with comprehensive results"""
    try:
        email = sanitize_input(request.args.get("mail", ""))
        include_breaches = request.args.get("breaches", "true").lower() == "true"
        include_history = request.args.get("history", "false").lower() == "true"
        format_type = request.args.get("format", "json").lower()

        # Validation
        if not email:
            return jsonify({
                "error": "Missing email parameter",
                "message": "Please provide email via ?mail=your@email.com",
                "example": "/api/search?mail=test@example.com"
            }), 400

        if not is_valid_email(email):
            return jsonify({
                "error": "Invalid email format",
                "email": email,
                "message": "Please provide a valid email address"
            }), 400

        # Generate request ID
        request_id = hashlib.sha256(f"{email}{time.time()}".encode()).hexdigest()[:16]

        logger.info(f"Search initiated for: {email[:5]}***")

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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Origin": "https://databreach.com",
            "Referer": "https://databreach.com/",
            "X-Request-ID": request_id
        }

        try:
            start_time = time.time()
            r = requests.post(
                "https://databreach.com/_telefunc",
                headers=headers,
                json=payload,
                timeout=15
            )
            elapsed_time = time.time() - start_time

            result = {}
            try:
                result = r.json() if r.text else {}
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse response for {email[:5]}***")
                result = {"raw_response": r.text[:200]}

            # Advanced response formatting
            response_data = {
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "version": API_VERSION,
                    "response_time_ms": round(elapsed_time * 1000, 2),
                    "status": "success",
                    "http_status": r.status_code
                },
                
                "searcher": {
                    "name": MY_NAME,
                    "username": MY_USERNAME,
                    "verified": True
                },
                
                "search_query": {
                    "email_masked": f"{email[0]}***@{email.split('@')[1]}" if "@" in email else "invalid",
                    "include_breaches": include_breaches,
                    "include_history": include_history
                },
                
                "breaches": result.get("breaches", []) if include_breaches else [],
                
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
                "compromised_accounts": len(response_data.get("data", {}).get("hits", [])) if isinstance(response_data.get("data"), dict) else 0,
                "response_time_ms": response_data["meta"]["response_time_ms"]
            }

            if format_type == "xml":
                return convert_to_xml(response_data)
            
            return jsonify(response_data), 200

        except requests.Timeout:
            logger.error(f"Timeout for {email[:5]}***")
            return jsonify({
                "error": "Request timeout",
                "message": "The search took too long. Please try again.",
                "timeout_seconds": 15,
                "searcher": {"name": MY_NAME, "username": MY_USERNAME}
            }), 504

        except requests.ConnectionError:
            logger.error("Connection error to databreach.com")
            return jsonify({
                "error": "Connection error",
                "message": "Unable to connect to breach database. Try again later.",
                "searcher": {"name": MY_NAME, "username": MY_USERNAME}
            }), 502

    except Exception as e:
        logger.error(f"Unexpected error in search: {str(e)}")
        return jsonify({
            "error": "Server error",
            "message": "An unexpected error occurred",
            "request_id": request_id if 'request_id' in locals() else None,
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/batch-search", methods=['POST'])
@rate_limit
def batch_search():
    """Batch search for multiple emails"""
    try:
        data = request.get_json() or {}
        
        if "emails" not in data:
            return jsonify({
                "error": "Invalid request",
                "message": "POST body must contain 'emails' array",
                "example": '{"emails": ["test@example.com", "user@domain.com"]}'
            }), 400
        
        emails = data.get("emails", [])
        if not isinstance(emails, list) or len(emails) == 0:
            return jsonify({
                "error": "Invalid emails parameter",
                "message": "emails must be a non-empty array"
            }), 400
        
        if len(emails) > 50:
            return jsonify({
                "error": "Too many emails",
                "message": "Maximum 50 emails per request",
                "limit": 50,
                "received": len(emails)
            }), 413

        results = []
        errors = []
        batch_id = hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:12]
        
        logger.info(f"Batch search initiated with {len(emails)} emails")

        for idx, email in enumerate(emails[:50]):
            email = sanitize_input(email) if isinstance(email, str) else ""
            
            if not is_valid_email(email):
                errors.append({
                    "index": idx,
                    "email": email if email else "[empty]",
                    "error": "Invalid email format"
                })
                continue
                
            try:
                results.append({
                    "index": idx,
                    "email": email,
                    "status": "processed",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                errors.append({
                    "index": idx,
                    "email": email,
                    "error": str(e)
                })
        
        response = {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "version": API_VERSION,
                "batch_id": batch_id
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
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in batch_search: {str(e)}")
        return jsonify({
            "error": "Server error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/stats", methods=['GET'])
def stats():
    """API statistics"""
    return jsonify({
        "api_name": "Email Breach Finder API",
        "version": API_VERSION,
        "description": "Advanced email breach database search API",
        "author": MY_USERNAME,
        "owner": MY_NAME,
        "endpoints": {
            "health": {
                "path": "/api/health",
                "method": "GET",
                "description": "Health check endpoint"
            },
            "search": {
                "path": "/api/search",
                "method": "GET",
                "params": ["mail", "breaches", "history", "format"],
                "example": "/api/search?mail=test@example.com",
                "description": "Search for email in breach database"
            },
            "batch_search": {
                "path": "/api/batch-search",
                "method": "POST",
                "body": {"emails": ["email1@test.com", "email2@test.com"]},
                "description": "Batch search for multiple emails"
            },
            "stats": {
                "path": "/api/stats",
                "method": "GET",
                "description": "API statistics and information"
            }
        },
        "rate_limit": {
            "requests": REQUEST_LIMIT,
            "window": f"{TIME_WINDOW}s",
            "note": "Per IP address"
        },
        "features": {
            "no_authentication_required": True,
            "rate_limiting": True,
            "email_validation": True,
            "batch_support": True,
            "xml_support": True,
            "cors_enabled": True
        },
        "timestamp": datetime.now().isoformat()
    }), 200

# ==================== XML CONVERSION ====================

def convert_to_xml(data):
    """Convert JSON response to XML with proper escaping"""
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<response>\n'
    
    def dict_to_xml(d, indent=1):
        xml_str = ""
        indent_str = "  " * indent
        
        for key, value in d.items():
            safe_key = escape(str(key)).replace(" ", "_")
            
            if isinstance(value, dict):
                xml_str += f"{indent_str}<{safe_key}>\n"
                xml_str += dict_to_xml(value, indent + 1)
                xml_str += f"{indent_str}</{safe_key}>\n"
            elif isinstance(value, list):
                xml_str += f"{indent_str}<{safe_key}>\n"
                for item in value:
                    if isinstance(item, dict):
                        xml_str += dict_to_xml({"item": item}, indent + 1)
                    else:
                        safe_item = escape(str(item))
                        xml_str += f"{indent_str}  <item>{safe_item}</item>\n"
                xml_str += f"{indent_str}</{safe_key}>\n"
            elif value is not None:
                safe_value = escape(str(value))
                xml_str += f"{indent_str}<{safe_key}>{safe_value}</{safe_key}>\n"
        
        return xml_str
    
    xml += dict_to_xml(data, indent=1)
    xml += '</response>'
    
    return xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}

# ==================== STATIC FILES ====================

@app.route("/static/<path:path>")
def send_static(path):
    """Serve static files"""
    try:
        return send_from_directory('static', path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}")
        return jsonify({"error": "File not found"}), 404

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": ["/api/health", "/api/stats", "/api/search", "/api/batch-search"]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "message": f"This endpoint does not support {request.method}",
        "hint": "Check /api/stats for available endpoints and methods"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong. Please try again later."
    }), 500

# ==================== STARTUP ====================

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(host="0.0.0.0", port=port, debug=debug)
