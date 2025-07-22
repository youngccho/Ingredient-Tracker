from flask_cors import CORS
from flask import Flask, jsonify, request, abort
import main

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Food shelf-life tracker"

@app.route('/lookup')
def lookup_item():
    q = request.args.get("query", "").strip()
    if not q:
        abort(400, description="Must provide ?query...")

    matches = main.lookup(q)
    if not matches:
        return jsonify({
            "query": q,
            "matches": [],
            "message": "No matches found"
        }), 404
    
    results =  []
    for idx in matches:
        rec =  main.records[idx]
        shelf = main.extract_shelf_life(rec)
        results.append({
            "name": rec.get("Name"),
            "shelf_life": shelf
        })

    return jsonify({
        "query": q,
        "matches": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)