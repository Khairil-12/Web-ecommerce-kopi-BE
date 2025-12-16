from app import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    transaction_code = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_method = db.Column(db.String(100), nullable=True)
    shipping_address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('TransactionItem', backref='transaction', lazy=True)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_code}>'

class TransactionItem(db.Model):
    __tablename__ = 'transaction_items'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    transaction_id = db.Column(db.BigInteger, db.ForeignKey('transactions.id'), nullable=False)
    product_id = db.Column(db.BigInteger, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TransactionItem {self.id}>'