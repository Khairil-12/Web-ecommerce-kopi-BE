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
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False) 
    original_price = db.Column(db.Float)
    category = db.Column(db.String(100), nullable=False) 
    image_url = db.Column(db.String(500), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ========== TAMBAHAN FIELD BARU UNTUK KOPI ==========
    # 1. Informasi Fisik
    weight = db.Column(db.String(50), nullable=True)  
    weight_options = db.Column(db.Text, nullable=True)  
    type = db.Column(db.String(50), nullable=True)  
    
    # 2. Informasi Asal & Proses
    origin = db.Column(db.String(100), nullable=True)  
    process = db.Column(db.String(50), nullable=True) 
    altitude = db.Column(db.String(50), nullable=True) 
    
    # 3. Karakteristik Roasting
    roast_level = db.Column(db.String(50), nullable=True)  
    flavor_notes = db.Column(db.Text, nullable=True)  
    brewing_methods = db.Column(db.Text, nullable=True)  

    # 4. Spesifikasi & Kualitas
    specifications = db.Column(db.Text, nullable=True)  
    grade = db.Column(db.String(50), nullable=True)  
    certification = db.Column(db.String(100), nullable=True)  
    
    # 5. Fitur & Status
    is_featured = db.Column(db.Boolean, default=False)
    is_discounted = db.Column(db.Boolean, default=False)
    discount_percentage = db.Column(db.Float, default=0)
    sold_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0)
    review_count = db.Column(db.Integer, default=0)
    
    # ========== RELASI ==========
    stocks = db.relationship('Stock', backref='product', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    transaction_items = db.relationship('TransactionItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    # Method untuk menghitung diskon otomatis
    def calculate_discount(self):
        if self.original_price and self.original_price > self.price:
            discount = ((self.original_price - float(self.price)) / self.original_price) * 100
            self.discount_percentage = round(discount, 1)
            self.is_discounted = True
        else:
            self.discount_percentage = 0
            self.is_discounted = False
    
    # Method untuk format JSON
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0,
            'original_price': self.original_price,
            'category': self.category,
            'image_url': self.image_url,
            'is_available': self.is_available,
            'is_featured': self.is_featured,
            'is_discounted': self.is_discounted,
            'discount_percentage': self.discount_percentage,
            'weight': self.weight,
            'type': self.type,
            'origin': self.origin,
            'process': self.process,
            'roast_level': self.roast_level,
            'flavor_notes': self.flavor_notes,
            'brewing_methods': self.brewing_methods,
            'specifications': self.specifications,
            'grade': self.grade,
            'certification': self.certification,
            'sold_count': self.sold_count,
            'rating': self.rating,
            'review_count': self.review_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


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