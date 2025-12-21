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

# === LOGIN (Updated based controller) ===
@bp.route('/login', methods=['POST'])
def login():
    try:
        from app.models.user import User
        from app import response
        
        data = request.json
        # Accept either email or username for login
        if not data or 'password' not in data or ('email' not in data and 'username' not in data):
            return jsonify({
                'success': False,
                'message': 'Email/username and password are required'
            }), 400

        identifier = data.get('email') or data.get('username')

        # Try to find by email first, then by username
        user = None
        if data.get('email'):
            user = User.query.filter_by(email=data.get('email')).first()
        else:
            user = User.query.filter_by(username=data.get('username')).first()

        if user and user.check_password(data['password']):
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }

            if hasattr(user, 'address') and user.address:
                user_data['address'] = user.address

            # Return shape compatible with frontend (expects `success` and `user`)
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user_data,
                'token': f'mock-jwt-token-{user.id}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid email/username or password'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login error: {str(e)}'
        }), 500

# === USER ROUTES (using UserController) ===
@bp.route('/users', methods=['GET'])
def get_users():
    try:
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


# Convenience endpoint for frontend register form
@bp.route('/register', methods=['POST'])
def register():
    try:
        # Reuse existing create_user logic
        return create_user()
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Register error: {str(e)}'
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
        from app.controllers.ProductController import index
        return index()
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Get products error: {str(e)}'
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

#=== PRODUCT SOFT DELETE /  DEACTIVATE PRODUCTS ===
@bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        from app.models.user import User
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        from app.models.product import Product
        from app import db
        
        product = Product.query.get(id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': f'Product with ID {id} not found'
            }), 404
        
        if hasattr(product, 'is_active'):
            product.is_active = False
        elif hasattr(product, 'is_available'):
            product.is_available = False
        else:
            if hasattr(product, 'deleted_at'):
                product.deleted_at = datetime.utcnow()
            else:
                product_name = product.name
                from app.models.stock import Stock
                stock = Stock.query.filter_by(product_id=id).first()
                if stock:
                    db.session.delete(stock)
                db.session.delete(product)
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': f'Product "{product_name}" permanently deleted',
                    'data': {
                        'id': id,
                        'name': product_name,
                        'deleted_at': datetime.utcnow().isoformat()
                    }
                })
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Product "{product.name}" has been deactivated',
            'data': {
                'id': product.id,
                'name': product.name,
                'status': 'deactivated',
                'deactivated_at': product.updated_at.isoformat() if product.updated_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error deleting product: {str(e)}'
        }), 500
    
#ACTIVATE PRODUCT
@bp.route('/products/<int:id>/activate', methods=['PUT'])
def activate_product(id):
    """Reactivate a deactivated product (admin only)"""
    try:
        # Check admin access
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        from app.models.user import User
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        from app.models.product import Product
        from app import db
        
        product = Product.query.get(id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': f'Product with ID {id} not found'
            }), 404
        
        # Reactivate product
        activated = False
        
        if hasattr(product, 'is_active'):
            if not product.is_active:
                product.is_active = True
                activated = True
        elif hasattr(product, 'is_available'):
            if not product.is_available:
                product.is_available = True
                activated = True
        elif hasattr(product, 'deleted_at'):
            if product.deleted_at:
                product.deleted_at = None
                activated = True
        
        if not activated:
            return jsonify({
                'status': 'info',
                'message': f'Product "{product.name}" is already active',
                'data': {
                    'id': product.id,
                    'name': product.name,
                    'status': 'active'
                }
            })
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Product "{product.name}" has been reactivated',
            'data': {
                'id': product.id,
                'name': product.name,
                'status': 'active',
                'reactivated_at': product.updated_at.isoformat() if product.updated_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error activating product: {str(e)}'
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
            total_products = Product.query.count()  
        except:
            total_products = Product.query.filter_by(is_available=True).count() if hasattr(Product, 'is_available') else Product.query.count()
        
        total_transactions = Transaction.query.count()
        
        # Today's transactions
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        today_transactions = Transaction.query.filter(
            Transaction.created_at >= today_start
        ).count()
        
        # Low stock products 
        low_stocks = 0
        try:
            low_stocks = Stock.query.filter(Stock.quantity <= Stock.min_stock).count()
        except:
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

# === CUSTOMER DASHBOARD ===
@bp.route('/customer/dashboard', methods=['GET'])
def customer_dashboard():
    try:
        # Require authenticated customer (non-admin)
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'X-User-ID header is required'
            }), 401

        from app.models.user import User
        from app.models.transaction import Transaction
        from app.models.cart import Cart, CartItem
        from app import db
        from app.models.product import Product

        user = User.query.get(int(user_id))
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user'
            }), 401

        if user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Customer access required'
            }), 403

        # Customer-scoped stats
        total_orders = Transaction.query.filter_by(user_id=user.id).count()

        total_spent_result = db.session.query(db.func.sum(Transaction.total_amount)).filter(Transaction.user_id == user.id).scalar()
        total_spent = float(total_spent_result) if total_spent_result else 0

        recent = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.created_at.desc()).limit(5).all()
        recent_list = []
        for t in recent:
            recent_list.append({
                'id': t.id,
                'transaction_code': t.transaction_code,
                'total_amount': float(t.total_amount) if t.total_amount else 0,
                'status': t.status,
                'created_at': t.created_at.isoformat() if t.created_at else None
            })

        # Cart summary
        cart = Cart.query.filter_by(user_id=user.id).first()
        item_count = 0
        cart_total = 0
        if cart:
            items = CartItem.query.filter_by(cart_id=cart.id).all()
            item_count = sum(i.quantity for i in items)
            for i in items:
                p = Product.query.get(i.product_id)
                if p and hasattr(p, 'price'):
                    cart_total += float(p.price) * i.quantity

        data = {
            'customer': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'total_orders': total_orders,
            'total_spent': total_spent,
            'recent_transactions': recent_list,
            'cart': {
                'item_count': item_count,
                'cart_total': cart_total
            },
            'dashboard_updated': datetime.utcnow().isoformat()
        }

        return jsonify({
            'status': 'success',
            'message': 'Customer dashboard data',
            'data': data
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Customer dashboard error: {str(e)}'
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

# === REMOVE CART ITEM ===
@bp.route('/cart/remove/<int:item_id>', methods=['DELETE'])
def remove_cart_item(item_id):
    try:
        from app.models.cart import CartItem, Cart
        from app import db
        
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        # Find cart item
        cart_item = CartItem.query.get(item_id)
        if not cart_item:
            return jsonify({
                'status': 'error',
                'message': f'Cart item {item_id} not found'
            }), 404
        
        # Verify cart belongs to user
        cart = Cart.query.get(cart_item.cart_id)
        if not cart or cart.user_id != int(user_id):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 403
        
        # Remove item
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Item removed from cart',
            'data': {
                'removed_item_id': item_id,
                'product_id': cart_item.product_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Remove from cart error: {str(e)}'
        }), 500
    
# === CLEAR CART ===
@bp.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    try:
        from app.models.cart import Cart, CartItem
        from app import db
        
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
                'message': 'Cart is already empty'
            })
        
        # Delete all cart items
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Cart cleared successfully',
            'data': {
                'cart_id': cart.id,
                'items_removed': True
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Clear cart error: {str(e)}'
        }), 500

# === CHECKOUT CART ===
@bp.route('/cart/checkout', methods=['POST'])
def checkout_cart():
    try:
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        from app.models.transaction import Transaction, TransactionItem
        from app.models.user import User
        from app.models.stock import Stock
        from app import db
        import random
        import string
        
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        data = request.json
        payment_method = data.get('payment_method', 'Bank Transfer')
        shipping_address = data.get('shipping_address')
        notes = data.get('notes', '')
        
        # Get user for shipping address if not provided
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        if not shipping_address:
            shipping_address = user.address
        
        # Get cart
        cart = Cart.query.filter_by(user_id=int(user_id)).first()
        if not cart:
            return jsonify({
                'status': 'error',
                'message': 'Cart is empty'
            }), 400
        
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return jsonify({
                'status': 'error',
                'message': 'Cart is empty'
            }), 400
        
        # Calculate total and check stock
        total_amount = 0
        transaction_items = []
        
        for item in cart_items:
            product = Product.query.get(item.product_id)
            if not product:
                continue
            
            # Check stock
            stock = Stock.query.filter_by(product_id=product.id).first()
            if not stock or stock.quantity < item.quantity:
                return jsonify({
                    'status': 'error',
                    'message': f'Insufficient stock for {product.name}. Available: {stock.quantity if stock else 0}'
                }), 400
            
            # Calculate subtotal
            price = float(product.price) if product.price else 0
            subtotal = price * item.quantity
            total_amount += subtotal
            
            # Prepare transaction item
            transaction_item = TransactionItem(
                product_id=product.id,
                quantity=item.quantity,
                price=price,
                subtotal=subtotal
            )
            transaction_items.append(transaction_item)
        
        # Generate transaction code
        def generate_code():
            date_str = datetime.utcnow().strftime("%Y%m%d")
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            return f"TRX-{date_str}-{random_str}"
        
        # Create transaction
        transaction = Transaction(
            transaction_code=generate_code(),
            user_id=int(user_id),
            total_amount=total_amount,
            status='pending',
            payment_method=payment_method,
            shipping_address=shipping_address,
            notes=notes
        )
        
        db.session.add(transaction)
        db.session.flush()  # Get transaction ID
        
        # Add items to transaction and reduce stock
        for i, item in enumerate(transaction_items):
            item.transaction_id = transaction.id
            db.session.add(item)
            
            # Reduce stock
            stock = Stock.query.filter_by(product_id=item.product_id).first()
            stock.quantity -= item.quantity
        
        # Clear cart after checkout
        CartItem.query.filter_by(cart_id=cart.id).delete()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Checkout successful. Order created!',
            'data': {
                'transaction_id': transaction.id,
                'transaction_code': transaction.transaction_code,
                'total_amount': float(transaction.total_amount),
                'status': transaction.status,
                'item_count': len(transaction_items)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Checkout error: {str(e)}'
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