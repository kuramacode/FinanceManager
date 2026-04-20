from app.models import db

class Accounts(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='active') # active, frozen, closed
    currency_code = db.Column(db.String(20), nullable=False, default='UAH')
    emoji = db.Column(db.String(3), default='💸')
    type = db.Column(db.String(20), default='card')
    subtitle = db.Column(db.String(255))
    note = db.Column(db.String(255))
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
