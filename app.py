import os
import secrets
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from markupsafe import escape
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Import our modular components
from models.database import db
from models.user import User, FoodScan
from repositories.user_repository import UserRepository
from services.orchestrator import OrchestratorService

load_dotenv()

app = Flask(__name__, 
            static_folder='public', 
            static_url_path='', 
            template_folder='public')

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "postgresql://localhost/nutriscan")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# --- Auth Middleware ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

# --- API Endpoints ---
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.json
    print(f"DEBUG: Register request data: {data}")
    email = data.get('email', '')
    name = data.get('name', '')
    password = data.get('password', '')
    dietary_profile = data.get('dietary_profile', [])
    
    if len(email) < 3 or len(password) < 6:
        return jsonify({"error": "Valid email and password (6+ chars) required"}), 400
        
    if UserRepository.get_by_username(email):
        return jsonify({"error": "User with this email already exists"}), 400
    
    UserRepository.create_user(email, generate_password_hash(password, method='pbkdf2:sha256'), 
                               dietary_profile, name)
    return jsonify({"success": True})

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.json
    print(f"DEBUG: Login request data: {data}")
    email = data.get('email')
    user = UserRepository.get_by_username(email)
    if user and check_password_hash(user.password_hash, data.get('password')):
        session['user_id'] = user.id
        return jsonify({"success": True})
    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/api/auth/logout')
def api_logout():
    session.pop('user_id', None)
    return jsonify({"success": True})

@app.route('/api/user/me')
@login_required
def api_user_me():
    user = UserRepository.get_by_id(session['user_id'])
    return jsonify({
        "username": user.username,
        "name": user.name or user.username,
        "dietary_profile": user.dietary_profile
    })

@app.route('/api/user/profile', methods=['POST'])
@login_required
def api_save_profile():
    profile = request.json.get('profile', [])
    if not isinstance(profile, list):
        return jsonify({"error": "Invalid profile format"}), 400
    if UserRepository.save_dietary_profile(session['user_id'], profile):
        return jsonify({"success": True})
    return jsonify({"error": "Failed to update profile"}), 500

@app.route('/api/food/scan', methods=['POST'])
@login_required
def api_food_scan():
    user = UserRepository.get_by_id(session['user_id'])
    result = None
    filename = "Manual Entry"
    save_scan = False

    try:
        # A. Handle Multipart Image Upload
        if 'image' in request.files:
            file = request.files['image']
            filename = file.filename
            
            # Security: Limit file size to 5MB
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            if size > 5 * 1024 * 1024:
                return jsonify({"error": "Image too large (max 5MB)"}), 400
                
            result = OrchestratorService.scan_food_image(file, user.dietary_profile)
            save_scan = True

        # B. Handle JSON Text Input (Manual Entry)
        elif request.is_json:
            data = request.json
            text = data.get('text', '')
            if not text:
                return jsonify({"error": "No text provided"}), 400
                
            result = OrchestratorService.scan_food_text(text, user.dietary_profile)
            save_scan = True
            
        else:
            return jsonify({"error": "No image or text provided"}), 400

        # C. Logic for saving successful (non-partial) scans
        if save_scan and result and not result.get("partial") and "error" not in result:
            new_scan = FoodScan(
                user_id=user.id,
                filename=filename,
                data=result
            )
            db.session.add(new_scan)
            db.session.commit()

        return jsonify(result)

    except Exception as e:
        print(f"CRITICAL API ERROR: {str(e)}")
        return jsonify({"error": "Service temporarily unavailable", "partial": True}), 500

@app.route('/api/scans/history')
@login_required
def api_scans_history():
    user = UserRepository.get_by_id(session['user_id'])
    return jsonify({
        "history": [s.to_dict() for s in user.scans[::-1]]
    })

if __name__ == '__main__':
    app.run(port=3000, debug=True)
