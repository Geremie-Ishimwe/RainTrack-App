from flask import Flask, request, jsonify, send_from_directory, g
import os, sqlite3, re
from werkzeug.utils import secure_filename # Required for Phase 6

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "raintrack.sqlite")
UPLOAD_DIR = os.path.join(INSTANCE_DIR, "uploads") # New folder for images

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}
MAX_BYTES = 3 * 1024 * 1024  # 3MB limit

def ensure_dirs():
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    if "db" not in g:
        ensure_dirs()
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # ADDED photo_filename to the table
    db.execute('''
      CREATE TABLE IF NOT EXISTS rainfall (
        date TEXT PRIMARY KEY,
        rainfall_mm REAL NOT NULL CHECK(rainfall_mm >= 0),
        photo_filename TEXT
      )
    ''')
    db.commit()

@app.before_request
def _before():
    init_db()

# ---- Static ----
@app.get("/")
def home():
    return send_from_directory(STATIC_DIR, "index.html")

@app.get("/chart")
def chart_page():
    return send_from_directory(STATIC_DIR, "chart.html")

@app.get("/static/<path:name>")
def static_files(name):
    return send_from_directory(STATIC_DIR, name)

# ---- Helpers ----
def bad_request(msg, fields=None):
    return jsonify({"error": msg, "fields": fields}), 400

def validate_date_iso(date: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", date or ""))

def allowed_filename(name: str) -> bool:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return ext in ALLOWED_EXT

def validate_record(payload):
    fields = {}
    date = payload.get("date")
    rainfall = payload.get("rainfall_mm")
    
    if rainfall is None:
        rainfall = payload.get("rainfall")

    if not date:
        fields["date"] = "Date is required."
        
    try:
        rainfall = float(rainfall)
        if rainfall < 0:
            fields["rainfall_mm"] = "Rainfall cannot be negative."
    except (TypeError, ValueError):
        fields["rainfall_mm"] = "Rainfall must be a valid number."

    if fields:
        return False, fields
    return True, {"date": date, "rainfall_mm": rainfall}

# --- API ----
@app.get("/api/health")
def health():
    return jsonify({"ok": True})

@app.post("/api/rainfall")
@app.post("/api/rain")
def upsert_rainfall():
    payload = request.get_json()
    if not payload:
        return bad_request("No data provided.")
        
    is_valid, result = validate_record(payload)
    if not is_valid:
        return bad_request("Validation failed", result)
        
    db = get_db()
    try:
        db.execute('''
            INSERT INTO rainfall (date, rainfall_mm) 
            VALUES (?, ?) 
            ON CONFLICT(date) DO UPDATE SET rainfall_mm=excluded.rainfall_mm
        ''', (result["date"], result["rainfall_mm"]))
        db.commit()
        return jsonify({"ok": True, "message": "Saved successfully!"})
    except Exception as e:
        return bad_request("Database error")

@app.get("/api/rainfall")
@app.get("/api/rain")
def list_rainfall():
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return bad_request("Missing dates.")
        
    db = get_db()
    rows = db.execute('''
        SELECT date, rainfall_mm 
        FROM rainfall 
        WHERE date >= ? AND date <= ? 
        ORDER BY date ASC
    ''', (start, end)).fetchall()
    
    data_list = [{"date": r["date"], "rainfall_mm": r["rainfall_mm"]} for r in rows]
    return jsonify(data_list)

# NEW: Upload Photo Route
@app.post("/api/rainfall/<date>/photo")
def upload_photo(date):
    if not validate_date_iso(date):
        return bad_request("Invalid date format.")

    cl = request.content_length
    if cl is not None and cl > MAX_BYTES:
        return bad_request("File too large (max 3MB).")

    if "file" not in request.files:
        return bad_request("No file uploaded.")

    f = request.files["file"]
    if not f.filename:
        return bad_request("No file selected.")

    filename = secure_filename(f.filename)
    if not allowed_filename(filename):
        return bad_request("Unsupported file type (png/jpg/jpeg/webp).")

    ensure_dirs()
    ext = filename.rsplit(".", 1)[-1].lower()
    stored = f"{date}.{ext}" # Renames file to the date (e.g., 2026-05-04.jpg)
    path = os.path.join(UPLOAD_DIR, stored)
    f.save(path)

    db = get_db()
    db.execute('''
        INSERT INTO rainfall (date, rainfall_mm, photo_filename) 
        VALUES (?, 0.0, ?) 
        ON CONFLICT(date) DO UPDATE SET photo_filename=excluded.photo_filename
    ''', (date, stored))
    db.commit()

    return jsonify({"ok": True, "data": {"date": date, "photo_filename": stored}})

# NEW: View Photo Route
@app.get("/media/<name>")
def media(name):
    return send_from_directory(UPLOAD_DIR, name)

# NEW: Get specific day data
@app.get("/api/rainfall/<date>")
def get_rainfall(date):
    if not validate_date_iso(date):
        return bad_request("Invalid date format.")

    db = get_db()
    row = db.execute("""
      SELECT date, rainfall_mm, photo_filename
      FROM rainfall
      WHERE date = ?
    """, (date,)).fetchone()

    if row is None:
        return jsonify({"ok": True, "data": None})

    data = {
        "date": row["date"],
        "rainfall_mm": row["rainfall_mm"],
        "photo_filename": row["photo_filename"]
    }
    return jsonify({"ok": True, "data": data})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)