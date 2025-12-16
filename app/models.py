from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ========== USER MODEL ==========
class Users(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi
    transactions = db.relationship('Transactions', backref='user', lazy=True, cascade='all, delete-orphan')
    carts = db.relationship('Cart', backref='user', lazy=True, cascade='all, delete-orphan')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


# ========== PRODUCT MODEL ==========
class Products(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Harga
    category = db.Column(db.String(100), nullable=False)  # Contoh: Arabica, Robusta, dll
    image_url = db.Column(db.String(500), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi
    stocks = db.relationship('Stocks', backref='product', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    transaction_items = db.relationship('TransactionItems', backref='product', lazy=True)


# ========== STOCK MODEL ==========
class Stocks(db.Model):
    __tablename__ = 'stocks'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(db.BigInteger, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_stock = db.Column(db.Integer, default=10)  # Stok minimum
    last_restock = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Stock {self.product_id}: {self.quantity}>'


# ========== CART MODEL ==========
class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')


# ========== CART ITEM MODEL ==========
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    cart_id = db.Column(db.BigInteger, db.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.BigInteger, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ========== TRANSACTION MODEL ==========
class Transactions(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    transaction_code = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, paid, shipped, completed, cancelled
    payment_method = db.Column(db.String(100), nullable=True)
    shipping_address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi
    items = db.relationship('TransactionItems', backref='transaction', lazy=True, cascade='all, delete-orphan')


# ========== TRANSACTION ITEM MODEL ==========
class TransactionItems(db.Model):
    __tablename__ = 'transaction_items'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    transaction_id = db.Column(db.BigInteger, db.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.BigInteger, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Harga saat transaksi
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)