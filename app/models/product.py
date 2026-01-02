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
    # Additional fields used by controllers and frontend
    original_price = db.Column(db.Numeric(10, 2), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_discounted = db.Column(db.Boolean, default=False)
    discount_percentage = db.Column(db.Float, default=0)
    rating = db.Column(db.Float, nullable=True)
    specifications = db.Column(db.Text, nullable=True)
    weight = db.Column(db.String(100), nullable=True)
    type = db.Column(db.String(100), nullable=True)
    origin = db.Column(db.String(200), nullable=True)
    process = db.Column(db.String(200), nullable=True)
    roast_level = db.Column(db.String(100), nullable=True)
    flavor_notes = db.Column(db.Text, nullable=True)
    brewing_methods = db.Column(db.Text, nullable=True)
    grade = db.Column(db.String(100), nullable=True)
    certification = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stocks = db.relationship('Stock', backref='product', lazy=True, uselist=False)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    transaction_items = db.relationship('TransactionItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'

    def calculate_discount(self):
        try:
            if self.original_price and float(self.original_price) > float(self.price):
                discount = ((float(self.original_price) - float(self.price)) / float(self.original_price)) * 100
                self.discount_percentage = round(discount, 1)
                self.is_discounted = True
            else:
                self.discount_percentage = 0
                self.is_discounted = False
        except Exception:
            self.discount_percentage = 0
            self.is_discounted = False