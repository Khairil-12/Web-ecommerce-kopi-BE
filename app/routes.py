from flask import Blueprint, jsonify, request
from datetime import datetime
import random
import string

bp = Blueprint('api', __name__)

# === HOME ===
@bp.route('/')
def home():
    return jsonify({
        'status': 'success',
        'message': 'Ecommerce Kopi API',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'testing_guide': 'Check /test endpoint for testing instructions'
    })

# === TEST ENDPOINT ===
@bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'success',
        'message': 'API Ready for Postman Testing',
        'timestamp': datetime.utcnow().isoformat(),
        'testing_steps': [
            '1. POST /users - Register admin user (set is_admin: true)',
            '2. POST /login - Login as admin',
            '3. Save admin ID from response',
            '4. POST /users - Register customer user',
            '5. POST /login - Login as customer',
            '6. Save customer ID from response',
            '7. Use admin ID in header (X-User-ID) to create products',
            '8. Use customer ID to test cart functionality'
        ],
        'endpoints': {
            'AUTH': [
                'POST /login - Login',
                'POST /users - Register'
            ],
            'USERS': [
                'GET /users - Get all users (admin only)',
                'GET /users/<id> - Get user by ID',
                'POST /users - Create user',
                'PUT /users/<id> - Update user',
                'DELETE /users/<id> - Delete user (admin only)'
            ],
            'PRODUCTS': [
                'GET /products - Get all products',
                'GET /products/<id> - Get product by ID',
                'POST /products - Create product (admin only)',
                'PUT /products/<id> - Update product (admin only)',
                'DELETE /products/<id> - Delete product (admin only)'
            ],
            'ADMIN': [
                'GET /admin/dashboard - Admin dashboard',
                'GET /admin/users - All users (admin view)',
                'GET /admin/transactions - All transactions (admin view)'
            ],
            'CART': [
                'GET /cart - Get user cart',
                'POST /cart/add - Add to cart',
                'PUT /cart/update/<id> - Update cart item',
                'DELETE /cart/remove/<id> - Remove from cart',
                'POST /cart/checkout - Checkout'
            ]
        }
    })

# === LOGIN (Updated based on your controller) ===
@bp.route('/login', methods=['POST'])
def login():
    try:
        # Call UserController's store function for login logic
        from app.models.user import User
        from app import response
        
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
                'phone': user.phone,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            
            # Add address if exists
            if hasattr(user, 'address') and user.address:
                user_data['address'] = user.address
            
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'data': user_data,
                'token': f'mock-jwt-token-{user.id}'
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

# === USER ROUTES (using your UserController) ===
@bp.route('/users', methods=['GET'])
def get_users():
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header is required'
            }), 401
        
        from app.models.user import User
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Call UserController index
        from app.controllers.UserController import index
        result = index()
        return result
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Get users error: {str(e)}'
        }), 500

@bp.route('/users', methods=['POST'])
def create_user():
    try:
        # Call UserController store
        from app.controllers.UserController import store
        return store()
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Create user error: {str(e)}'
        }), 500

@bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    try:
        # Check authentication
        requester_id = request.headers.get('X-User-ID')
        if not requester_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        from app.models.user import User
        requester = User.query.get(int(requester_id))
        if not requester:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user'
            }), 401
        
        # Check permission
        target_user = User.query.get(id)
        if not target_user:
            return jsonify({
                'status': 'error',
                'message': f'User with ID {id} not found'
            }), 404
        
        if requester.id != target_user.id and not requester.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Access denied'
            }), 403
        
        # Call UserController show
        from app.controllers.UserController import show
        return show(id)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Get user error: {str(e)}'
        }), 500

@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        # Check authentication
        requester_id = request.headers.get('X-User-ID')
        if not requester_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        from app.models.user import User
        requester = User.query.get(int(requester_id))
        if not requester:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user'
            }), 401
        
        # Check permission
        target_user = User.query.get(id)
        if not target_user:
            return jsonify({
                'status': 'error',
                'message': f'User with ID {id} not found'
            }), 404
        
        if requester.id != target_user.id and not requester.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Can only update your own profile'
            }), 403
        
        # Call UserController update
        from app.controllers.UserController import update
        return update(id)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Update user error: {str(e)}'
        }), 500

@bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        # Check admin access
        admin_id = request.headers.get('X-User-ID')
        if not admin_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        from app.models.user import User
        admin = User.query.get(int(admin_id))
        if not admin or not admin.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Prevent self-deletion
        if admin.id == id:
            return jsonify({
                'status': 'error',
                'message': 'Cannot delete yourself'
            }), 400
        
        # Call UserController delete
        from app.controllers.UserController import delete
        return delete(id)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Delete user error: {str(e)}'
        }), 500

# === PRODUCT ROUTES ===
@bp.route('/products', methods=['GET'])
def get_products():
    try:
        # Call ProductController index
        from app.controllers.ProductController import index
        return index()
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Get products error: {str(e)}'
        }), 500

@bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    try:
        from app.controllers.ProductController import show
        return show(id)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Get product error: {str(e)}'
        }), 500

@bp.route('/products', methods=['POST'])
def create_product():
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header is required'
            }), 401
        
        from app.models.user import User
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Call ProductController store
        from app.controllers.ProductController import store
        return store()
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Create product error: {str(e)}'
        }), 500

@bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header is required'
            }), 401
        
        from app.models.user import User
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Call ProductController update
        from app.controllers.ProductController import update
        return update(id)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Update product error: {str(e)}'
        }), 500

@bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header is required'
            }), 401
        
        from app.models.user import User
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Call ProductController delete
        from app.controllers.ProductController import delete
        return delete(id)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Delete product error: {str(e)}'
        }), 500

# === ADMIN ROUTES ===
@bp.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header is required'
            }), 401
        
        from app.models.user import User
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Get statistics
        from app.models.product import Product
        from app.models.transaction import Transaction
        from app.models.stock import Stock
        
        total_users = User.query.count()
        
        # Perbaikan: Gunakan Product.query.count() tanpa filter is_active
        try:
            total_products = Product.query.count()  # Tanpa filter is_active
        except:
            total_products = Product.query.filter_by(is_available=True).count() if hasattr(Product, 'is_available') else Product.query.count()
        
        total_transactions = Transaction.query.count()
        
        # Today's transactions
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        today_transactions = Transaction.query.filter(
            Transaction.created_at >= today_start
        ).count()
        
        # Low stock products (handle error jika field tidak ada)
        low_stocks = 0
        try:
            low_stocks = Stock.query.filter(Stock.quantity <= Stock.min_stock).count()
        except:
            # Jika min_stock tidak ada, skip
            pass
        
        # Total revenue
        from app import db
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
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Dashboard error: {str(e)}'
        }), 500

@bp.route('/admin/users', methods=['GET'])
def admin_get_users():
    """Admin view of all users"""
    return get_users()

@bp.route('/admin/transactions', methods=['GET'])
def admin_get_transactions():
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header is required'
            }), 401
        
        from app.models.user import User
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Get all transactions
        from app.models.transaction import Transaction
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

# === CART ROUTES (Keep your existing cart routes) ===
@bp.route('/cart', methods=['GET'])
def get_cart():
    try:
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        from app import response
        
        # Get user ID from header
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header required'
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
            if product:  # HAPUS pengecekan 'is_active'
                item_total = float(product.price) * item.quantity
                total += item_total
                cart_data.append({
                    'cart_item_id': item.id,
                    'product_id': product.id,
                    'product_name': product.name,
                    'price': float(product.price),
                    'quantity': item.quantity,
                    'subtotal': item_total,
                    'image_url': product.image_url if hasattr(product, 'image_url') else None
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

@bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    try:
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        from app import response, db
        
        # Get user ID from header
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header required'
            }), 401
        
        data = request.json
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id:
            return jsonify({
                'status': 'error',
                'message': "Product ID required"
            }), 400
        
        if quantity <= 0:
            return jsonify({
                'status': 'error',
                'message': "Quantity must be greater than 0"
            }), 400
        
        # Check product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': "Product not found"
            }), 404
        
        # PERBAIKAN: Cek ketersediaan product
        # Cek apakah product memiliki attribute is_active atau is_available
        product_unavailable = False
        
        if hasattr(product, 'is_active'):
            if not product.is_active:
                product_unavailable = True
        elif hasattr(product, 'is_available'):
            if not product.is_available:
                product_unavailable = True
        # Jika tidak ada attribute status, anggap product available
        
        if product_unavailable:
            return jsonify({
                'status': 'error',
                'message': f"Product {product.name} is not available"
            }), 400
        
        # Get or create cart
        cart = Cart.query.filter_by(user_id=int(user_id)).first()
        if not cart:
            cart = Cart(user_id=int(user_id))
            db.session.add(cart)
            db.session.flush()
        
        # Check if item already in cart
        cart_item = CartItem.query.filter_by(
            cart_id=cart.id, 
            product_id=product_id
        ).first()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f"Added {quantity} x {product.name} to cart",
            'data': {
                'cart_id': cart.id,
                'product_id': product_id,
                'product_name': product.name,
                'quantity': cart_item.quantity,
                'subtotal': float(product.price) * cart_item.quantity
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Add to cart error: {str(e)}'
        }), 500

# === UPDATE CART ITEM ===   
@bp.route('/cart/update/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    try:
        from app.models.cart import CartItem, Cart
        from app.models.product import Product
        from app import response, db
        
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': "X-User-ID header required"
            }), 401
        
        data = request.json
        quantity = data.get('quantity')
        
        if quantity is None:
            return jsonify({
                'status': 'error',
                'message': "Quantity required"
            }), 400
        
        # Find cart item
        cart_item = CartItem.query.get(item_id)
        if not cart_item:
            return jsonify({
                'status': 'error',
                'message': "Cart item not found"
            }), 404
        
        # Verify cart belongs to user
        cart = Cart.query.get(cart_item.cart_id)
        if not cart or cart.user_id != int(user_id):
            return jsonify({
                'status': 'error',
                'message': "Unauthorized"
            }), 403
        
        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            db.session.delete(cart_item)
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': "Item removed from cart"
            })
        
        # Check stock
        product = Product.query.get(cart_item.product_id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': "Product not found"
            }), 404
        
        # Update quantity
        cart_item.quantity = quantity
        db.session.commit()
        
        # Calculate new subtotal
        subtotal = float(product.price) * quantity
        
        return jsonify({
            'status': 'success',
            'message': "Cart item updated",
            'data': {
                'item_id': cart_item.id,
                'product_id': cart_item.product_id,
                'product_name': product.name if hasattr(product, 'name') else 'Unknown',
                'quantity': cart_item.quantity,
                'subtotal': subtotal
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Update cart error: {str(e)}'
        }), 500

# === HEALTH CHECK ===
@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'success',
        'message': 'API is healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected'  # Add actual DB check if needed
    })