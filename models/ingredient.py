from models.database import db

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    aliases = db.Column(db.JSON, default=list) # e.g. ["E123", "Amaranth"]
    risk_level = db.Column(db.String(50)) # e.g. "Low", "Moderate", "High", "Banned"
    fssai_status = db.Column(db.String(100)) # e.g. "Approved", "Banned", "Regulated"
    description = db.Column(db.Text)
    is_vegan = db.Column(db.Boolean, default=True)
    is_gluten_free = db.Column(db.Boolean, default=True)
    ins_code = db.Column(db.String(50), nullable=True, index=True) # e.g. "INS 123"

    def to_dict(self):
        return {
            "name": self.name,
            "risk_level": self.risk_level,
            "fssai_status": self.fssai_status,
            "description": self.description,
            "is_vegan": self.is_vegan,
            "is_gluten_free": self.is_gluten_free,
            "ins_code": self.ins_code
        }
