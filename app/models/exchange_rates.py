from app.models import db

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    base_code = db.Column(db.String(3), nullable=False, default='UAH')   # UAH
    target_code = db.Column(db.String(3), nullable=False) # USD
    rate = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(32))  # 'nbu', 'monobank', тощо
    
    __table_args__ = (
        db.UniqueConstraint('base_code', 'target_code', 'date', 'source'),
    )
