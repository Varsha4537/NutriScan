from datetime import datetime
from models.database import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120)) # Full Name
    password_hash = db.Column(db.String(120), nullable=False)
    dietary_profile = db.Column(db.JSON, default=list) # e.g. ["vegan", "gluten-free"]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scans = db.relationship('FoodScan', backref='user', lazy=True)

class FoodScan(db.Model):
    __tablename__ = 'food_scans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.JSON) # The full AI analysis result

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }
