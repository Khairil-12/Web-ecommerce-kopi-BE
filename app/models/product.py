from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    specifications = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stocks = db.relationship('Stock', backref='product', lazy=True, uselist=False)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    transaction_items = db.relationship('TransactionItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'