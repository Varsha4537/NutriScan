import os
import uuid
from datetime import timedelta, datetime
from flask import (
    Flask, request, redirect, url_for,
    session, jsonify, send_from_directory
)
import bcrypt
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

# ─── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="public", static_url_path="")

# Use a stable secret key so sessions survive restarts during development
app.secret_key = os.environ.get("SECRET_KEY", "nutriscan-dev-secret-change-in-prod-2024")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://localhost/nutriscan")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ─── Database Models ──────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.LargeBinary, nullable=False)
    dietary_profile = db.Column(db.JSON, default=list)

class Scan(db.Model):
    __tablename__ = 'scans'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    filename = db.Column(db.String(255), nullable=True)
    text_content = db.Column(db.Text, nullable=True)
    result_json = db.Column(db.JSON, nullable=False)

# ─── Constants ────────────────────────────────────────────────────────────────
PUBLIC_DIR = "public"
DASHBOARD_ROUTE = "/dashboard"

# ─── User Repository (Abstraction) ────────────────────────────────────────────
class UserRepository:
    """Abstracts user data storage using SQLAlchemy ORM."""
    def get_by_email(self, email: str) -> dict:
        user = User.query.filter_by(email=email).first()
        if not user: return None
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password_hash": user.password_hash,
            "dietary_profile": user.dietary_profile or []
        }

    def save_user(self, email: str, user_data: dict) -> None:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                password_hash=user_data["password_hash"],
                dietary_profile=user_data.get("dietary_profile", [])
            )
            db.session.add(user)
        else:
            user.name = user_data.get("name", user.name)
            user.password_hash = user_data.get("password_hash", user.password_hash)
            user.dietary_profile = user_data.get("dietary_profile", user.dietary_profile)
        db.session.commit()

    def email_exists(self, email: str) -> bool:
        return User.query.filter_by(email=email).first() is not None

user_repo = UserRepository()

# ─── Auth Helpers ─────────────────────────────────────────────────────────────
def hash_password(plain: str) -> bytes:
    """Hashes a plaintext password using bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt())

def check_password(plain: str, hashed: bytes) -> bool:
    """Validates a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed)

def login_required(f):
    """Decorator to enforce session authentication on routes."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

# ─── Page Routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Serves the landing page."""
    return send_from_directory(PUBLIC_DIR, "index.html")

@app.route("/login")
def login_page():
    """Serves the login page or redirects if authenticated."""
    if "user_id" in session:
        return redirect(url_for("dashboard_page"))
    return send_from_directory(PUBLIC_DIR, "login.html")

@app.route("/register")
def register_page():
    """Serves the registration page or redirects if authenticated."""
    if "user_id" in session:
        return redirect(url_for("dashboard_page"))
    return send_from_directory(PUBLIC_DIR, "register.html")

@app.route("/dashboard")
@login_required
def dashboard_page():
    """Serves the protected dashboard page."""
    return send_from_directory(PUBLIC_DIR, "dashboard.html")

# ─── Auth API ─────────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """Handles new user registration and sets up session."""
    data = request.get_json(force=True)
    name     = (data.get("name", "") or "").strip()
    email    = (data.get("email", "") or "").strip().lower()
    pwd      = data.get("password", "") or ""
    dietary  = data.get("dietary_profile", [])

    if not name or not email or not pwd:
        return jsonify({"error": "All fields are required."}), 400
    if len(pwd) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if user_repo.email_exists(email):
        return jsonify({"error": "An account with that email already exists."}), 409

    uid = str(uuid.uuid4())
    user_repo.save_user(email, {
        "id": uid,
        "name": name,
        "email": email,
        "password_hash": hash_password(pwd),
        "dietary_profile": dietary
    })

    session.permanent = True
    session["user_id"]    = uid
    session["user_email"] = email
    session["user_name"]  = name

    return jsonify({"message": "Account created.", "redirect": DASHBOARD_ROUTE}), 201

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Handles user authentication and session creation."""
    data  = request.get_json(force=True)
    email = (data.get("email", "") or "").strip().lower()
    pwd   = data.get("password", "") or ""

    user = user_repo.get_by_email(email)
    if not user or not check_password(pwd, user["password_hash"]):
        return jsonify({"error": "Invalid email or password."}), 401

    session.permanent = True
    session["user_id"]    = user["id"]
    session["user_email"] = email
    session["user_name"]  = user["name"]

    return jsonify({"message": "Logged in.", "redirect": DASHBOARD_ROUTE}), 200

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    """Clears the active user session."""
    session.clear()
    return jsonify({"message": "Logged out.", "redirect": "/"}), 200

@app.route("/api/user/me")
def api_me():
    """Returns the authenticated user's profile metadata."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthenticated"}), 401
    
    email = session.get("user_email", "")
    user  = user_repo.get_by_email(email) or {}
    
    return jsonify({
        "id":              session["user_id"],
        "name":            session["user_name"],
        "email":           email,
        "dietary_profile": user.get("dietary_profile", [])
    })

@app.route("/api/user/dietary", methods=["POST"])
def api_dietary():
    """Updates the user's dietary profile preferences."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthenticated"}), 401
    
    data    = request.get_json(force=True)
    profile = data.get("profile", [])
    email   = session.get("user_email", "")
    
    user = user_repo.get_by_email(email)
    if user:
        user["dietary_profile"] = profile
        user_repo.save_user(email, user)
        
    return jsonify({"message": "Profile updated."})

# ─── Services ─────────────────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY", ""),
    base_url="https://api.groq.com/openai/v1"
)

def extract_text_via_ocr(file) -> str:
    """Sends image to OCR.space and extracts text."""
    ocr_key = os.environ.get("OCR_SPACE_API_KEY", "helloworld")
    try:
        res = requests.post(
            "https://api.ocr.space/parse/image",
            files={"image": (file.filename, file.read(), file.content_type)},
            data={"apikey": ocr_key, "language": "eng"}
        )
        ocr_data = res.json()
        if ocr_data.get("ParsedResults"):
            return ocr_data["ParsedResults"][0]["ParsedText"]
        return ""
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return ""

GROK_ANALYSIS_PROMPT = """You are an expert food safety analyst.
Product/Ingredients text: {text_val}
User Dietary Preferences: {profile}

Analyze these ingredients and cross-reference with FDA/ISI standards.
Provide a highly detailed analysis matching this JSON schema exactly:
{{
  "name": "Product Name",
  "subtitle": "Flavor / Serving size (if found, else general category)",
  "health_score": <int 1-10>,
  "consumption_advice": "e.g., Not for daily consumption",
  "nutrition_breakdown": [
    {{
      "name": "e.g. Saturated Fat or Sugar",
      "level": "High ❌ or Moderate ⚠️ or Low ✅",
      "percentage": <int 0-100 indicating how full the bar should be>,
      "tip": "e.g., This is like eating 3 spoons of butter"
    }}
  ],
  "summary": "A 2-3 sentence paragraph explaining what this means for their health based on their dietary profile.",
  "regulatory_warnings": [
    {{
      "standard": "FDA | ISI | EFSA",
      "chemical": "<official chemical/additive name, ex: E621>",
      "warning": "<exact regulatory limit description or banned status>"
    }}
  ],
  "alternatives": [
    {{
      "name": "Healthier Alternative",
      "subtitle": "Short reason it is better",
      "emoji": "🍚",
      "link": "https://www.amazon.com/s?k=Search+Term"
    }}
  ]
}}"""

def analyze_ingredients(text_val: str, profile: list) -> dict:
    """Calls Grok LLM to analyze ingredients against FDA/ISI standards."""
    if not client.api_key or client.api_key == "your_grok_api_key_here":
        raise ValueError("Please set XAI_API_KEY in the .env file.")

    prompt = GROK_ANALYSIS_PROMPT.format(text_val=text_val, profile=profile)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a JSON-only API. Print only valid JSON and no markdown formatting. Do not output anything before or after the JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    val = response.choices[0].message.content.strip()
    
    if val.startswith("```json"): val = val[7:]
    if val.startswith("```"): val = val[3:]
    if val.endswith("```"): val = val[:-3]
    
    return json.loads(val.strip())

# ─── APIs ─────────────────────────────────────────────────────────────────────
@app.route("/api/food/scan", methods=["POST"])
@login_required
def api_food_scan():
    text_val = ""
    filename = "Manual Entry"
    
    if request.is_json:
        data = request.get_json(force=True)
        text_val = data.get("text", "").strip()
    elif file := request.files.get("image"):
        filename = file.filename
        text_val = extract_text_via_ocr(file)
        if not text_val:
            return jsonify({"error": "Failed to extract text using OCR."}), 500

    if not text_val:
        return jsonify({"error": "No text or image provided."}), 400

    email   = session.get("user_email", "")
    user    = user_repo.get_by_email(email)
    profile = user.get("dietary_profile", []) if user else []
    
    try:
        analysis_data = analyze_ingredients(text_val, profile)
        
        # Save scan to Database
        new_scan = Scan(
            id=str(uuid.uuid4()),
            user_id=session["user_id"],
            filename=filename,
            text_content=text_val,
            result_json=analysis_data
        )
        db.session.add(new_scan)
        db.session.commit()
        
        return jsonify(analysis_data)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 500
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        return jsonify({"error": "Grok API failed to analyze the ingredients."}), 500

@app.route("/api/scans/history", methods=["GET"])
@login_required
def api_scan_history():
    """Retrieve chronologically ordered scan history for the current user."""
    scans = Scan.query.filter_by(user_id=session["user_id"]).order_by(Scan.timestamp.desc()).limit(20).all()
    history = []
    for s in scans:
        history.append({
            "id": s.id,
            "filename": s.filename,
            "timestamp": s.timestamp.isoformat() + "Z",
            "data": s.result_json
        })
    return jsonify({"history": history})

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Auto-create tables if they don't exist
    app.run(port=3000)
