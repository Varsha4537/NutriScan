# NutriScan 🥗

NutriScan is a full-fledged, production-ready web application that empowers users to make healthier food choices. By utilizing advanced OCR (Optical Character Recognition) and lightning-fast AI models, NutriScan instantly analyzes the ingredient lists of packaged foods, cross-references them against dietary profiles, and flags harmful additives based on FDA/ISI standards.

## ✨ Features
- **Instant Ingredient Scanning:** Upload an image of an ingredient list or type it in manually.
- **AI-Powered Health Analysis:** Powered by **Groq** (LLaMA-3) to generate comprehensive health scores, consumption advice, and nutritional breakdowns.
- **Dietary Personalization:** Set custom profiles (Vegan, Keto, Gluten-Free, Halal, etc.) to receive tailored warnings and product compatibility.
- **Better Alternatives Engine:** Automatically suggests healthier product alternatives and provides direct Amazon search links.
- **Premium Glassmorphism UI:** A sleek, fully modular frontend built with vanilla HTML/CSS/JS leveraging clean architecture separation.

## 🛠️ Tech Stack
- **Backend:** Python, Flask
- **Database:** PostgreSQL (managed natively via `Flask-SQLAlchemy` ORM)
- **Authentication:** Secure cookie sessions with `bcrypt` password hashing
- **Frontend:** HTML5, pure CSS3 (CSS Variables for theming), Vanilla JavaScript (`ApiService` modularity)
- **External APIs:** 
  - `OCR.space` (text extraction)
  - `Groq` (LLaMA-3 LLM reasoning)

---

## 🚀 Getting Started

### Prerequisites
Before you begin, ensure you have the following installed on your machine:
- **Python 3.9+**
- **PostgreSQL 14+** (can be installed via `brew install postgresql@14` on macOS)

### 1. Database Setup
Ensure your local PostgreSQL server is running and create an empty database named `nutriscan`:
```bash
brew services start postgresql@14
createdb nutriscan
```

### 2. Application Setup
Clone or download the repository, then navigate into the project folder.

**Create a Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Ensure the `.env` file in the root directory contains the following properties:
```env
# API Keys (Replace the Groq API key with your own)
XAI_API_KEY=gsk_your_groq_api_key_here
OCR_SPACE_API_KEY=helloworld

# Flask Settings
SECRET_KEY=your-secure-flask-session-secret
FLASK_ENV=development
DATABASE_URL=postgresql://localhost/nutriscan
```

### 4. Running the App
Once your environment is set up and your keys are entered, simply run the Flask backend. 
(*Note: `db.create_all()` runs automatically on startup to initialize your PostgreSQL tables if they don't exist.*)

```bash
python app.py
```

The server will start locally. Access the magnificent dashboard by visiting:
**http://127.0.0.1:3000**

---

## 🏗️ Clean Code Architecture 
This application was refactored with enterprise-grade **Clean Mapping** principles:
* **Repository Pattern:** Backend state is securely abstracted via a `UserRepository`, separating business logic from raw SQLAlchemy calls.
* **Separation of Concerns:** The Javascript UI cleanly partitions DOM building (`buildScoreCard`, `buildAlternatives`) away from network data polling (`ApiService`), eliminating single "god" functions.
* **Stateless APIs:** Routes in `app.py` delegate heavy logic (like OCR and LLM polling) to explicit modular single-responsibility helper services.
