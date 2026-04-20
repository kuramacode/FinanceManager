from . import db

class Categories(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True) # Визначення стовпця id як цілого числа, який є первинним ключем
    name = db.Column(db.String(100), nullable=False) # Визначення стовпця name як рядка с ограничением уникальности и не допускающего null
    desc = db.Column(db.String(255))
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id') ,nullable=False)
    emoji = db.Column(db.String(8), default='📦')
    built_in = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(20), nullable=False) # 'income' або 'expense'
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name'),
    )
