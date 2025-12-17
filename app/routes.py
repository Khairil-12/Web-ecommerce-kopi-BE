from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import random
import string
from app.models.user import User
from app.models.product import Product
from app.models.stock import Stock
from app.models.cart import Cart, CartItem
from app.models.transaction import Transaction, TransactionItem
from app import db
from app import response

bp = Blueprint('api', __name__)

# === UTILITY FUNCTIONS ===
def generate_transaction_code():
    """Generate unique transaction code"""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TRX-{date_str}-{random_str}"

# === HOME ===
@bp.route('/')
def home():
    return jsonify({
        'status': 'success',
        'message': 'Ecommerce Kopi API',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'database_tables': [
            'users', 'products', 'stocks', 'carts', 
            'cart_items', 'transactions', 'transaction_items'
        ]
    })

# === TEST ENDPOINT ===
@bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'success',
        'message': 'API is working',
        'timestamp': datetime.utcnow().isoformat(),
        'database_connected': True,
        'testing_endpoints': {
            'AUTH': [
                'POST /login - Login user',
                'POST /users - Register new user'
            ],
            'USERS': [
                'GET /users - Get all users (admin)',
                'GET /users/<id> - Get user by ID',
                'POST /users - Create user',
                'PUT /users/<id> - Update user',
                'DELETE /users/<id> - Delete user'
            ],
            'PRODUCTS': [
                'GET /products - Get all products',
                'GET /products/<id> - Get product by ID',
                'POST /products - Create product',
                'PUT /products/<id> - Update product',
                'DELETE /products/<id> - Delete product'
            ],
            'ADMIN': [
                'GET /admin/dashboard - Admin dashboard',
                'GET /admin/users - All users (admin)',
                'POST /admin/products - Create product (admin)',
                'GET /admin/transactions - All transactions (admin)'
            ],
            'CART': [
                'GET /cart - Get user cart',
                'POST /cart/add - Add to cart',
                'PUT /cart/update/<id> - Update cart item',
                'DELETE /cart/remove/<id> - Remove from cart',
                'POST /cart/checkout - Checkout cart'
            ]
        }
    })

# === LOGIN ===
@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone if hasattr(user, 'phone') else '',
                'is_admin': user.is_admin,
                'is_verified': user.is_verified if hasattr(user, 'is_verified') else True,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            
            # Add full_name if exists
            if hasattr(user, 'full_name') and user.full_name:
                user_data['full_name'] = user.full_name
            
            # Add address if exists
            if hasattr(user, 'address') and user.address:
                user_data['address'] = user.address
            
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'data': user_data,
                'token': f'mock-jwt-token-{user.id}'  # Mock token for testing
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Login error: {str(e)}'
        }), 500

# === USER ROUTES ===
@bp.route('/users', methods=['POST'])
def create_user():
    """Register new user"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'status': 'error',
                'message': 'Email already registered'
            }), 400
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=data['username']).first()
        if existing_username:
            return jsonify({
                'status': 'error',
                'message': 'Username already taken'
            }), 400
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],  # Assuming you have password hashing in User model
            is_admin=data.get('is_admin', False),  # Default to regular user
            is_verified=True  # Auto-verify for testing
        )
        
        # Add optional fields
        if 'full_name' in data:
            new_user.full_name = data['full_name']
        if 'phone' in data:
            new_user.phone = data['phone']
        if 'address' in data:
            new_user.address = data['address']
        
        db.session.add(new_user)
        db.session.commit()
        
        # Prepare response data (without password)
        user_data = {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'is_admin': new_user.is_admin,
            'is_verified': new_user.is_verified,
            'created_at': new_user.created_at.isoformat() if new_user.created_at else None
        }
        
        if hasattr(new_user, 'full_name') and new_user.full_name:
            user_data['full_name'] = new_user.full_name
        if hasattr(new_user, 'phone') and new_user.phone:
            user_data['phone'] = new_user.phone
        if hasattr(new_user, 'address') and new_user.address:
            user_data['address'] = new_user.address
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': user_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error creating user: {str(e)}'
        }), 500

@bp.route('/users', methods=['GET'])
def get_users():
    """Get all users (admin only)"""
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header is required'
            }), 401
        
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({
                'status': 'error',
                'message': f'User with ID {user_id} not found'
            }), 404
        
        if not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Get all users
        users = User.query.all()
        
        users_data = []
        for u in users:
            user_data = {
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'is_admin': u.is_admin,
                'is_verified': u.is_verified if hasattr(u, 'is_verified') else True,
                'created_at': u.created_at.isoformat() if u.created_at else None
            }
            
            if hasattr(u, 'full_name') and u.full_name:
                user_data['full_name'] = u.full_name
            if hasattr(u, 'phone') and u.phone:
                user_data['phone'] = u.phone
            if hasattr(u, 'address') and u.address:
                user_data['address'] = u.address
            
            users_data.append(user_data)
        
        return jsonify({
            'status': 'success',
            'message': f'Found {len(users_data)} users',
            'data': users_data,
            'count': len(users_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting users: {str(e)}'
        }), 500

@bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    """Get user by ID"""
    try:
        # Check authentication
        requester_id = request.headers.get('X-User-ID')
        if not requester_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        requester = User.query.get(int(requester_id))
        if not requester:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user'
            }), 401
        
        user = User.query.get(id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': f'User with ID {id} not found'
            }), 404
        
        # Check permission (own data or admin)
        if requester.id != user.id and not requester.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Access denied'
            }), 403
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_verified': user.is_verified if hasattr(user, 'is_verified') else True,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        
        if hasattr(user, 'full_name') and user.full_name:
            user_data['full_name'] = user.full_name
        if hasattr(user, 'phone') and user.phone:
            user_data['phone'] = user.phone
        if hasattr(user, 'address') and user.address:
            user_data['address'] = user.address
        
        return jsonify({
            'status': 'success',
            'message': 'User found',
            'data': user_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting user: {str(e)}'
        }), 500

@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    """Update user"""
    try:
        # Check authentication
        requester_id = request.headers.get('X-User-ID')
        if not requester_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        requester = User.query.get(int(requester_id))
        if not requester:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user'
            }), 401
        
        user = User.query.get(id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': f'User with ID {id} not found'
            }), 404
        
        # Check permission (own data or admin)
        if requester.id != user.id and not requester.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Can only update your own profile'
            }), 403
        
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Update fields
        updated = False
        
        # Only admin can change is_admin
        if 'is_admin' in data and requester.is_admin:
            user.is_admin = bool(data['is_admin'])
            updated = True
        
        # Regular fields
        update_fields = ['full_name', 'phone', 'address']
        for field in update_fields:
            if field in data:
                setattr(user, field, data[field])
                updated = True
        
        # Email update (with uniqueness check)
        if 'email' in data and data['email'] != user.email:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user.id:
                return jsonify({
                    'status': 'error',
                    'message': 'Email already in use'
                }), 400
            user.email = data['email']
            updated = True
        
        # Username update (with uniqueness check)
        if 'username' in data and data['username'] != user.username:
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user.id:
                return jsonify({
                    'status': 'error',
                    'message': 'Username already taken'
                }), 400
            user.username = data['username']
            updated = True
        
        # Password update
        if 'password' in data:
            user.password = data['password']  # Assuming password hashing in model
            updated = True
        
        if updated:
            user.updated_at = datetime.utcnow()
            db.session.commit()
        
        # Prepare response
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_verified': user.is_verified if hasattr(user, 'is_verified') else True,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
        
        if hasattr(user, 'full_name') and user.full_name:
            user_data['full_name'] = user.full_name
        if hasattr(user, 'phone') and user.phone:
            user_data['phone'] = user.phone
        if hasattr(user, 'address') and user.address:
            user_data['address'] = user.address
        
        return jsonify({
            'status': 'success',
            'message': 'User updated successfully' if updated else 'No changes made',
            'data': user_data,
            'updated': updated
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error updating user: {str(e)}'
        }), 500

@bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    """Delete user (admin only)"""
    try:
        # Check admin access
        admin_id = request.headers.get('X-User-ID')
        if not admin_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        admin = User.query.get(int(admin_id))
        if not admin or not admin.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        user = User.query.get(id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': f'User with ID {id} not found'
            }), 404
        
        # Prevent self-deletion
        if user.id == admin.id:
            return jsonify({
                'status': 'error',
                'message': 'Cannot delete yourself'
            }), 400
        
        # Get user data before deletion
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'User {user.username} deleted successfully',
            'data': user_data
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error deleting user: {str(e)}'
        }), 500

# === PRODUCT ROUTES ===
@bp.route('/products', methods=['GET'])
def get_products():
    """Get all products"""
    try:
        products = Product.query.filter_by(is_active=True).all()
        
        products_data = []
        for product in products:
            # Get stock information
            stock = Stock.query.filter_by(product_id=product.id).first()
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price) if product.price else 0,
                'category': product.category or 'Uncategorized',
                'image_url': product.image_url or '/static/images/default-product.jpg',
                'stock': stock.quantity if stock else 0,
                'is_active': product.is_active,
                'created_at': product.created_at.isoformat() if product.created_at else None
            }
            
            # Add optional fields
            if hasattr(product, 'original_price') and product.original_price:
                product_data['original_price'] = float(product.original_price)
                product_data['is_discounted'] = product.original_price > product.price
                if product_data['is_discounted']:
                    discount = ((product.original_price - product.price) / product.original_price) * 100
                    product_data['discount_percentage'] = round(discount, 1)
            
            if hasattr(product, 'weight'):
                product_data['weight'] = product.weight
            if hasattr(product, 'origin'):
                product_data['origin'] = product.origin
            if hasattr(product, 'sold_count'):
                product_data['sold_count'] = product.sold_count
            
            products_data.append(product_data)
        
        return jsonify({
            'status': 'success',
            'message': f'Found {len(products_data)} products',
            'data': products_data,
            'count': len(products_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting products: {str(e)}'
        }), 500

@bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    """Get single product by ID"""
    try:
        product = Product.query.get(id)
        
        if not product or not product.is_active:
            return jsonify({
                'status': 'error',
                'message': f'Product with ID {id} not found'
            }), 404
        
        # Get stock
        stock = Stock.query.filter_by(product_id=product.id).first()
        
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price) if product.price else 0,
            'category': product.category or 'Uncategorized',
            'image_url': product.image_url or '/static/images/default-product.jpg',
            'stock': stock.quantity if stock else 0,
            'min_stock': stock.min_stock if stock else 10,
            'is_active': product.is_active,
            'created_at': product.created_at.isoformat() if product.created_at else None
        }
        
        # Add all available attributes
        optional_fields = [
            'original_price', 'weight', 'origin', 'roast_level', 
            'flavor_notes', 'brewing_methods', 'sold_count', 'rating',
            'review_count', 'is_featured', 'long_description'
        ]
        
        for field in optional_fields:
            if hasattr(product, field) and getattr(product, field):
                value = getattr(product, field)
                if field == 'original_price':
                    product_data[field] = float(value)
                    product_data['is_discounted'] = value > product.price
                    if product_data['is_discounted']:
                        discount = ((value - product.price) / value) * 100
                        product_data['discount_percentage'] = round(discount, 1)
                else:
                    product_data[field] = value
        
        return jsonify({
            'status': 'success',
            'message': 'Product found',
            'data': product_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting product: {str(e)}'
        }), 500

@bp.route('/products', methods=['POST'])
def create_product():
    """Create new product (admin only)"""
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'{field.title()} is required'
                }), 400
        
        # Create product
        new_product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=float(data['price']),
            category=data.get('category', 'Uncategorized'),
            image_url=data.get('image_url', '/static/images/default-product.jpg'),
            is_active=True
        )
        
        # Add optional fields
        optional_fields = [
            'original_price', 'weight', 'origin', 'roast_level',
            'flavor_notes', 'brewing_methods', 'long_description', 'is_featured'
        ]
        
        for field in optional_fields:
            if field in data:
                if field == 'original_price' and data[field]:
                    setattr(new_product, field, float(data[field]))
                else:
                    setattr(new_product, field, data[field])
        
        db.session.add(new_product)
        db.session.flush()  # Get product ID without committing
        
        # Create stock entry
        stock_quantity = data.get('stock', 0)
        stock = Stock(
            product_id=new_product.id,
            quantity=stock_quantity,
            min_stock=data.get('min_stock', 10)
        )
        db.session.add(stock)
        
        db.session.commit()
        
        # Prepare response
        product_data = {
            'id': new_product.id,
            'name': new_product.name,
            'description': new_product.description,
            'price': float(new_product.price),
            'category': new_product.category,
            'image_url': new_product.image_url,
            'stock': stock_quantity,
            'min_stock': stock.min_stock,
            'is_active': new_product.is_active,
            'created_at': new_product.created_at.isoformat() if new_product.created_at else None
        }
        
        for field in optional_fields:
            if hasattr(new_product, field) and getattr(new_product, field):
                product_data[field] = getattr(new_product, field)
        
        return jsonify({
            'status': 'success',
            'message': 'Product created successfully',
            'data': product_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error creating product: {str(e)}'
        }), 500

@bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    """Update product (admin only)"""
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        product = Product.query.get(id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': f'Product with ID {id} not found'
            }), 404
        
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Update product fields
        updated = False
        product_fields = ['name', 'description', 'price', 'category', 'image_url',
                         'original_price', 'weight', 'origin', 'roast_level',
                         'flavor_notes', 'brewing_methods', 'long_description',
                         'is_featured', 'is_active']
        
        for field in product_fields:
            if field in data:
                if field == 'price' and data[field] is not None:
                    setattr(product, field, float(data[field]))
                elif field == 'original_price' and data[field] is not None:
                    setattr(product, field, float(data[field]))
                else:
                    setattr(product, field, data[field])
                updated = True
        
        # Update stock if provided
        stock = Stock.query.filter_by(product_id=id).first()
        if stock and 'stock' in data:
            stock.quantity = data['stock']
            updated = True
        
        if 'min_stock' in data and stock:
            stock.min_stock = data['min_stock']
            updated = True
        
        if updated:
            product.updated_at = datetime.utcnow()
            db.session.commit()
        
        # Get updated stock info
        stock = Stock.query.filter_by(product_id=id).first()
        
        # Prepare response
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price) if product.price else 0,
            'category': product.category,
            'image_url': product.image_url,
            'stock': stock.quantity if stock else 0,
            'min_stock': stock.min_stock if stock else 10,
            'is_active': product.is_active,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None
        }
        
        if hasattr(product, 'original_price') and product.original_price:
            product_data['original_price'] = float(product.original_price)
            product_data['is_discounted'] = product.original_price > product.price
            if product_data['is_discounted']:
                discount = ((product.original_price - product.price) / product.original_price) * 100
                product_data['discount_percentage'] = round(discount, 1)
        
        return jsonify({
            'status': 'success',
            'message': 'Product updated successfully' if updated else 'No changes made',
            'data': product_data,
            'updated': updated
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error updating product: {str(e)}'
        }), 500

@bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    """Delete product (admin only - soft delete)"""
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        product = Product.query.get(id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': f'Product with ID {id} not found'
            }), 404
        
        # Soft delete (set is_active to False)
        if product.is_active:
            product.is_active = False
            product.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'Product "{product.name}" has been deactivated',
                'data': {
                    'id': product.id,
                    'name': product.name,
                    'is_active': False,
                    'deactivated_at': product.updated_at.isoformat()
                }
            })
        else:
            return jsonify({
                'status': 'info',
                'message': 'Product is already deactivated',
                'data': {
                    'id': product.id,
                    'name': product.name,
                    'is_active': False
                }
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error deleting product: {str(e)}'
        }), 500

# === ADMIN DASHBOARD ===
@bp.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Get statistics
        total_users = User.query.count()
        total_products = Product.query.filter_by(is_active=True).count()
        total_transactions = Transaction.query.count()
        
        # Today's transactions
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        today_transactions = Transaction.query.filter(
            Transaction.created_at >= today_start
        ).count()
        
        # Low stock products
        low_stocks = Stock.query.filter(Stock.quantity <= Stock.min_stock).count()
        
        # Recent transactions
        recent_transactions = Transaction.query.order_by(
            Transaction.created_at.desc()
        ).limit(5).all()
        
        recent_transactions_data = []
        for transaction in recent_transactions:
            recent_transactions_data.append({
                'id': transaction.id,
                'transaction_code': transaction.transaction_code,
                'user_id': transaction.user_id,
                'total_amount': float(transaction.total_amount) if transaction.total_amount else 0,
                'status': transaction.status,
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None
            })
        
        # Total revenue
        total_revenue_result = db.session.query(db.func.sum(Transaction.total_amount)).scalar()
        total_revenue = float(total_revenue_result) if total_revenue_result else 0
        
        stats = {
            'total_users': total_users,
            'total_products': total_products,
            'total_transactions': total_transactions,
            'today_transactions': today_transactions,
            'low_stock_products': low_stocks,
            'total_revenue': total_revenue,
            'admin': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'dashboard_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Admin dashboard data',
            'data': {
                'stats': stats,
                'recent_transactions': recent_transactions_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Dashboard error: {str(e)}'
        }), 500

# === ADMIN SPECIFIC ENDPOINTS ===
@bp.route('/admin/users', methods=['GET'])
def admin_get_users():
    """Get all users (admin only) - same as /users but for admin panel"""
    return get_users()

@bp.route('/admin/products', methods=['POST'])
def admin_create_product():
    """Create product (admin only) - same as /products"""
    return create_product()

@bp.route('/admin/transactions', methods=['GET'])
def admin_get_transactions():
    """Get all transactions (admin only)"""
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Get all transactions
        transactions = Transaction.query.order_by(
            Transaction.created_at.desc()
        ).all()
        
        transactions_data = []
        for transaction in transactions:
            # Get user info
            user = User.query.get(transaction.user_id)
            
            transaction_data = {
                'id': transaction.id,
                'transaction_code': transaction.transaction_code,
                'user_id': transaction.user_id,
                'username': user.username if user else 'Unknown',
                'total_amount': float(transaction.total_amount) if transaction.total_amount else 0,
                'status': transaction.status,
                'payment_method': transaction.payment_method,
                'shipping_address': transaction.shipping_address,
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None
            }
            
            transactions_data.append(transaction_data)
        
        return jsonify({
            'status': 'success',
            'message': f'Found {len(transactions_data)} transactions',
            'data': transactions_data,
            'count': len(transactions_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting transactions: {str(e)}'
        }), 500

# === CART ROUTES (keep as is from your original code) ===
# [All your existing cart routes remain the same]
# Just change response format to match new structure

@bp.route('/cart', methods=['GET'])
def get_cart():
    try:
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        
        # Get user ID from header
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        cart = Cart.query.filter_by(user_id=int(user_id)).first()
        if not cart:
            return jsonify({
                'status': 'success',
                'message': 'Cart is empty',
                'data': {
                    'cart_id': None,
                    'items': [],
                    'total': 0,
                    'item_count': 0
                }
            })
        
        items = CartItem.query.filter_by(cart_id=cart.id).all()
        cart_data = []
        total = 0
        
        for item in items:
            product = Product.query.get(item.product_id)
            if product and product.is_active:
                item_total = float(product.price) * item.quantity
                total += item_total
                cart_data.append({
                    'cart_item_id': item.id,
                    'product_id': product.id,
                    'product_name': product.name,
                    'price': float(product.price),
                    'quantity': item.quantity,
                    'subtotal': item_total,
                    'image_url': product.image_url
                })
        
        return jsonify({
            'status': 'success',
            'message': 'Cart retrieved',
            'data': {
                'cart_id': cart.id,
                'user_id': cart.user_id,
                'items': cart_data,
                'total': total,
                'item_count': len(cart_data)
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Get cart error: {str(e)}'
        }), 500

# [Keep all other cart routes with similar response format updates]

# === SEED DATA FOR TESTING ===
@bp.route('/seed', methods=['POST'])
def seed_data():
    """Seed database with test data"""
    try:
        # Check if already seeded
        if User.query.count() > 0:
            return jsonify({
                'status': 'info',
                'message': 'Database already has data'
            })
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@kopi.com',
            password='admin123',  # Should be hashed in production
            full_name='Admin Kopi',
            phone='081234567890',
            address='Jl. Kopi No. 123, Jakarta',
            is_admin=True,
            is_verified=True
        )
        
        # Create regular user
        customer = User(
            username='customer',
            email='customer@email.com',
            password='customer123',
            full_name='Budi Santoso',
            phone='081298765432',
            address='Jl. Merdeka No. 45, Bandung',
            is_admin=False,
            is_verified=True
        )
        
        db.session.add(admin)
        db.session.add(customer)
        db.session.flush()
        
        # Create products
        products = [
            Product(
                name='Kopi Arabica Gayo',
                description='Kopi premium dari Gayo, Aceh dengan aroma floral',
                price=125000,
                original_price=150000,
                category='Arabica',
                image_url='https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=300&fit=crop',
                weight='250g',
                origin='Gayo, Aceh',
                roast_level='Medium',
                flavor_notes='Floral, Chocolate, Citrus',
                is_featured=True,
                is_active=True
            ),
            Product(
                name='Kopi Robusta Lampung',
                description='Kopi kuat dengan cita rasa earthy dan crema yang tebal',
                price=85000,
                category='Robusta',
                image_url='https://images.unsplash.com/photo-1511537190424-bbbab87ac5eb?w=400&h=300&fit=crop',
                weight='250g',
                origin='Lampung',
                roast_level='Dark',
                flavor_notes='Earthy, Nutty, Dark Chocolate',
                is_active=True
            )
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.flush()
        
        # Create stocks
        for i, product in enumerate(products):
            stock = Stock(
                product_id=product.id,
                quantity=[50, 100][i],  # Different quantities
                min_stock=10
            )
            db.session.add(stock)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Database seeded with test data',
            'data': {
                'users_created': 2,
                'products_created': 2,
                'admin_credentials': {
                    'email': 'admin@kopi.com',
                    'password': 'admin123'
                },
                'customer_credentials': {
                    'email': 'customer@email.com',
                    'password': 'customer123'
                }
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error seeding database: {str(e)}'
        }), 500

# === RESET DATABASE ===
@bp.route('/reset', methods=['DELETE'])
def reset_database():
    """Reset database (for testing only)"""
    try:
        # Clear all tables (in correct order to avoid foreign key constraints)
        CartItem.query.delete()
        Cart.query.delete()
        TransactionItem.query.delete()
        Transaction.query.delete()
        Stock.query.delete()
        Product.query.delete()
        User.query.delete()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Database reset successfully',
            'data': {
                'tables_cleared': [
                    'users', 'products', 'stocks', 'transactions',
                    'transaction_items', 'carts', 'cart_items'
                ]
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error resetting database: {str(e)}'
        }), 500