from app.models import db

class Currency(db.Model):
    __tablename__ = 'currencies'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)
    name = db.Column(db.String(20), unique=True, nullable=False)
    flag = db.Column(db.String(3), unique=True, nullable=False)
    
