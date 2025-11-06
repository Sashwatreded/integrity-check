from flask import Flask, request, jsonify, g, send_from_directory, make_response
import sqlite3
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'integrity_logs.sqlite')
DASHBOARD_DIR = os.path.join(os.path.dirname(BASE_DIR), 'dashboard')

app = Flask(__name__, static_folder=None)

# --- Database helpers ---

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            path TEXT NOT NULL,
            old_hash TEXT,
            new_hash TEXT
        )
    ''')
    db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Simple CORS helper
def add_cors_headers(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return resp


@app.route('/log', methods=['POST', 'OPTIONS'])
def post_log():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response('', 204))
    data = request.get_json(silent=True)
    if not data:
        return add_cors_headers(jsonify({'error': 'Invalid JSON'})), 400

    # expected fields: timestamp, event_type, path, old_hash, new_hash
    ts = data.get('timestamp') or datetime.utcnow().isoformat() + 'Z'
    ev = data.get('event_type')
    path = data.get('path')
    old_hash = data.get('old_hash')
    new_hash = data.get('new_hash')

    if not ev or not path:
        return add_cors_headers(jsonify({'error': 'Missing fields event_type or path'})), 400

    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO logs (timestamp, event_type, path, old_hash, new_hash) VALUES (?, ?, ?, ?, ?)',
                (ts, ev, path, old_hash, new_hash))
    db.commit()
    return add_cors_headers(jsonify({'status': 'ok'})), 201


@app.route('/logs', methods=['GET'])
def get_logs():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, timestamp, event_type, path, old_hash, new_hash FROM logs ORDER BY id DESC')
    rows = cur.fetchall()
    out = [dict(r) for r in rows]
    return add_cors_headers(jsonify(out))


# Serve dashboard static files
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_dashboard(path):
    # Path is relative to the /dashboard folder in repository root
    root_dir = os.path.normpath(os.path.join(BASE_DIR, '..', 'dashboard'))
    full = os.path.join(root_dir, path)
    if os.path.isfile(full):
        return send_from_directory(root_dir, path)
    # fallback to index
    return send_from_directory(root_dir, 'index.html')


if __name__ == '__main__':
    # ensure db exists and table is created
    Path(DB_PATH).touch(exist_ok=True)
    with app.app_context():
        init_db()
    # Run on 0.0.0.0:5000 by default so agent can connect from same machine
    app.run(host='0.0.0.0', port=5000, debug=True)
