from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

@app.route("/search")
def search():
    email = request.args.get("mail")

    if not email:
        return jsonify({
            "error": "Missing mail parameter"
        }), 400

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
        "Referer": "https://databreach.com/"
    }

    try:
        r = requests.post(
            "https://databreach.com/_telefunc",
            headers=headers,
            data=json.dumps(payload, separators=(",", ":")),
            timeout=30
        )

        return jsonify(r.json())

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)