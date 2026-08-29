from flask import Blueprint, jsonify, request
from datetime import datetime
import random
import string
import os
from werkzeug.utils import secure_filename

bp = Blueprint('api', __name__)
UPLOAD_FOLDER = 'img/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_user_or_error():
    from app.models.user import User
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None, (jsonify({
            'status': 'error',
            'message': 'X-User-ID header is required'
        }), 401)
    user = User.get_by_id(int(user_id))
    if not user:
        return None, (jsonify({
            'status': 'error',
            'message': 'Invalid user'
        }), 401)
    return user, None


def _require_admin():
    from app.models.user import User
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None, (jsonify({
            'status': 'error',
            'message': 'X-User-ID header is required'
        }), 401)
    user = User.get_by_id(int(user_id))
    if not user:
        return None, (jsonify({
            'status': 'error',
            'message': 'Invalid user'
        }), 401)
    if not user.get('is_admin'):
        return None, (jsonify({
            'status': 'error',
            'message': 'Admin access required'
        }), 403)
    return user, None


@bp.route('/')
def home():
    return jsonify({
        'status': 'success',
        'message': 'Ecommerce Kopi API',
        'version': '3.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'testing_guide': 'Check /test endpoint for testing instructions'
    })

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
            '8. Use customer ID to test cart functionality',
            '9. POST /logout - Logout current user'
        ],
        'endpoints': {
            'AUTH': [
                'POST /login - Login',
                'POST /logout - Logout current user',
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

@bp.route('/login', methods=['POST'])
def login():
    try:
        from app.models.user import User
        data = request.json
        if not data or 'password' not in data or ('email' not in data and 'username' not in data):
            return jsonify({
                'success': False,
                'message': 'Email/username and password are required'
            }), 400
        user = None
        if data.get('email'):
            user = User.get_by_email(data.get('email'))
        else:
            user = User.get_by_username(data.get('username'))
        if user and User.check_password(user, data['password']):
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'phone': user.get('phone'),
                'is_admin': user.get('is_admin'),
                'created_at': user.get('created_at')
            }
            if user.get('address'):
                user_data['address'] = user['address']
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user_data,
                'token': f'mock-jwt-token-{user["id"]}'
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

@bp.route('/users', methods=['GET'])
def get_users():
    try:
        user, error = _require_admin()
        if error:
            return error
        from app.controllers.UserController import index
        return index()
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Get users error: {str(e)}'
        }), 500

@bp.route('/users', methods=['POST'])
def create_user():
    try:
        from app.controllers.UserController import store
        return store()
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Create user error: {str(e)}'
        }), 500

@bp.route('/register', methods=['POST'])
def register():
    try:
        return create_user()
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Register error: {str(e)}'
        }), 500

@bp.route('/logout', methods=['POST'])
def logout():
    try:
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({
                'status': 'success',
                'message': 'Logged out (no active session)'
            })
        from app.models.user import User
        user = User.get_by_id(int(user_id))
        if user:
            print(f"User {user['username']} (ID: {user['id']}) logged out at {datetime.utcnow()}")
        return jsonify({
            'status': 'success',
            'message': 'Successfully logged out',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Client should clear localStorage and redirect to login page'
        })
    except Exception as e:
        return jsonify({
            'status': 'success',
            'message': 'Logout completed',
            'error_note': str(e) if str(e) else None,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

@bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    try:
        requester_id = request.headers.get('X-User-ID')
        if requester_id:
            from app.models.user import User
            requester = User.get_by_id(int(requester_id))
            if not requester:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid user'
                }), 401
        from app.models.product import Product
        product = Product.get_by_id(id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': f'Product with ID {id} not found'
            }), 404
        from app.controllers.ProductController import show
        return show(id)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Get product error: {str(e)}'
        }), 500

@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        user, error = _get_user_or_error()
        if error:
            return error
        from app.models.user import User
        target_user = User.get_by_id(id)
        if not target_user:
            return jsonify({
                'status': 'error',
                'message': f'User with ID {id} not found'
            }), 404
        if user['id'] != id and not user.get('is_admin'):
            return jsonify({
                'status': 'error',
                'message': 'Can only update your own profile'
            }), 403
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
        admin, error = _require_admin()
        if error:
            return error
        if admin['id'] == id:
            return jsonify({
                'status': 'error',
                'message': 'Cannot delete yourself'
            }), 400
        from app.controllers.UserController import delete
        return delete(id)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Delete user error: {str(e)}'
        }), 500

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
        user, error = _require_admin()
        if error:
            return error
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
        user, error = _require_admin()
        if error:
            return error
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
        user, error = _require_admin()
        if error:
            return error
        from app.models.product import Product
        product = Product.get_by_id(id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': f'Product with ID {id} not found'
            }), 404
        from app.models.stock import Stock
        Stock.delete_by_product_id(id)
        Product.delete(id)
        return jsonify({
            'status': 'success',
            'message': f'Product "{product["name"]}" permanently deleted',
            'data': {
                'id': id,
                'name': product['name'],
                'deleted_at': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error deleting product: {str(e)}'
        }), 500

@bp.route('/products/<int:id>/activate', methods=['PUT'])
def activate_product(id):
    try:
        user, error = _require_admin()
        if error:
            return error
        from app.models.product import Product
        product = Product.get_by_id(id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': f'Product with ID {id} not found'
            }), 404
        if product.get('is_available'):
            return jsonify({
                'status': 'info',
                'message': f'Product "{product["name"]}" is already active',
                'data': {
                    'id': id,
                    'name': product['name'],
                    'status': 'active'
                }
            })
        Product.update(id, {'is_available': True})
        return jsonify({
            'status': 'success',
            'message': f'Product "{product["name"]}" has been reactivated',
            'data': {
                'id': id,
                'name': product['name'],
                'status': 'active',
                'reactivated_at': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error activating product: {str(e)}'
        }), 500

@bp.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    try:
        admin, error = _require_admin()
        if error:
            return error
        from app.models.user import User
        from app.models.product import Product
        from app.models.transaction import Transaction
        from app.models.stock import Stock
        total_users = len(User.get_all())
        total_products = len(Product.get_all())
        transactions = Transaction.get_all()
        total_transactions = len(transactions)
        today = datetime.utcnow().date().isoformat()
        today_transactions = len([t for t in transactions if (t.get('created_at') or '').startswith(today)])
        low_stocks = len([s for s in Stock.get_all() if s.get('quantity', 0) <= s.get('min_stock', 10)])
        total_revenue = Transaction.sum_total_all()
        stats = {
            'total_users': total_users,
            'total_products': total_products,
            'total_transactions': total_transactions,
            'today_transactions': today_transactions,
            'low_stock_products': low_stocks,
            'total_revenue': total_revenue,
            'admin': {
                'id': admin['id'],
                'username': admin['username'],
                'email': admin['email']
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
    return get_users()

@bp.route('/admin/transactions', methods=['GET'])
def admin_get_transactions():
    try:
        admin, error = _require_admin()
        if error:
            return error
        from app.models.transaction import Transaction
        from app.models.user import User
        transactions = Transaction.get_all()
        users = {u['id']: u for u in User.get_all()}
        transactions_data = []
        for transaction in transactions:
            user = users.get(transaction.get('user_id'))
            transactions_data.append({
                'id': transaction.get('id'),
                'transaction_code': transaction.get('transaction_code'),
                'user_id': transaction.get('user_id'),
                'username': user.get('username') if user else 'Unknown',
                'total_amount': float(transaction.get('total_amount', 0) or 0),
                'status': transaction.get('status'),
                'payment_method': transaction.get('payment_method'),
                'shipping_address': transaction.get('shipping_address'),
                'created_at': transaction.get('created_at')
            })
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

@bp.route('/transactions/<int:transaction_id>', methods=['GET'])
def get_transaction_detail(transaction_id):
    try:
        user, error = _get_user_or_error()
        if error:
            return error
        from app.models.transaction import Transaction, TransactionItem
        from app.models.product import Product
        txn = Transaction.get_by_id(transaction_id)
        if not txn:
            return jsonify({'status': 'error', 'message': 'Transaction not found'}), 404
        if not user.get('is_admin') and txn.get('user_id') != int(user['id']):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        items = []
        for it in TransactionItem.get_by_transaction_id(transaction_id):
            prod = Product.get_by_id(it.get('product_id'))
            items.append({
                'id': it.get('id'),
                'product_id': it.get('product_id'),
                'product_name': prod.get('name') if prod else None,
                'image_url': prod.get('image_url') if prod else None,
                'quantity': it.get('quantity'),
                'price': float(it.get('price', 0) or 0),
                'subtotal': float(it.get('subtotal', 0) or 0)
            })
        txn_data = {
            'id': txn.get('id'),
            'transaction_code': txn.get('transaction_code'),
            'user_id': txn.get('user_id'),
            'total_amount': float(txn.get('total_amount', 0) or 0),
            'status': txn.get('status'),
            'payment_method': txn.get('payment_method'),
            'shipping_address': txn.get('shipping_address'),
            'notes': txn.get('notes'),
            'created_at': txn.get('created_at'),
            'items': items
        }
        return jsonify({'status': 'success', 'message': 'Transaction found', 'data': txn_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error fetching transaction: {str(e)}'}), 500

@bp.route('/customer/dashboard', methods=['GET'])
def customer_dashboard():
    try:
        user, error = _get_user_or_error()
        if error:
            return error
        if user.get('is_admin'):
            return jsonify({
                'status': 'error',
                'message': 'Customer access required'
            }), 403
        from app.models.transaction import Transaction
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        total_orders = Transaction.count_by_user(user['id'])
        total_spent = Transaction.sum_total_by_user(user['id'])
        recent = Transaction.get_recent_by_user(user['id'], limit=5)
        recent_list = []
        for t in recent:
            recent_list.append({
                'id': t.get('id'),
                'transaction_code': t.get('transaction_code'),
                'total_amount': float(t.get('total_amount', 0) or 0),
                'status': t.get('status'),
                'created_at': t.get('created_at')
            })
        cart = Cart.get_by_user_id(user['id'])
        item_count = 0
        cart_total = 0
        if cart:
            items = CartItem.get_by_cart_id(cart['id'])
            item_count = sum(i.get('quantity', 0) for i in items)
            for i in items:
                p = Product.get_by_id(i.get('product_id'))
                if p and p.get('price'):
                    cart_total += float(p.get('price')) * i.get('quantity', 0)
        data = {
            'customer': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
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

@bp.route('/cart', methods=['GET'])
def get_cart():
    try:
        user, error = _get_user_or_error()
        if error:
            return error
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        cart = Cart.get_by_user_id(int(user['id']))
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
        items = CartItem.get_by_cart_id(cart['id'])
        cart_data = []
        total = 0
        for item in items:
            product = Product.get_by_id(item.get('product_id'))
            if product:
                item_total = float(product.get('price', 0) or 0) * item.get('quantity', 0)
                total += item_total
                cart_data.append({
                    'cart_item_id': item.get('id'),
                    'product_id': product.get('id'),
                    'product_name': product.get('name'),
                    'price': float(product.get('price', 0) or 0),
                    'quantity': item.get('quantity'),
                    'subtotal': item_total,
                    'image_url': product.get('image_url')
                })
        return jsonify({
            'status': 'success',
            'message': 'Cart retrieved',
            'data': {
                'cart_id': cart.get('id'),
                'user_id': cart.get('user_id'),
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
        user, error = _get_user_or_error()
        if error:
            return error
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
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
        product = Product.get_by_id(product_id)
        if not product:
            return jsonify({
                'status': 'error',
                'message': "Product not found"
            }), 404
        if not product.get('is_available'):
            return jsonify({
                'status': 'error',
                'message': f"Product {product['name']} is not available"
            }), 400
        cart = Cart.get_by_user_id(int(user['id']))
        if not cart:
            cart = Cart.create({'user_id': int(user['id'])})
        cart_item = CartItem.get_by_cart_and_product(cart['id'], product_id)
        if cart_item:
            new_qty = cart_item['quantity'] + quantity
            CartItem.update(cart_item['id'], {'quantity': new_qty})
            cart_item['quantity'] = new_qty
        else:
            cart_item = CartItem.create({
                'cart_id': cart['id'],
                'product_id': product_id,
                'quantity': quantity
            })
        return jsonify({
            'status': 'success',
            'message': f"Added {quantity} x {product['name']} to cart",
            'data': {
                'cart_id': cart.get('id'),
                'product_id': product_id,
                'product_name': product['name'],
                'quantity': cart_item['quantity'],
                'subtotal': float(product.get('price', 0) or 0) * cart_item['quantity']
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Add to cart error: {str(e)}'
        }), 500

@bp.route('/cart/update/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    try:
        user, error = _get_user_or_error()
        if error:
            return error
        from app.models.cart import CartItem, Cart
        from app.models.product import Product
        data = request.json
        quantity = data.get('quantity')
        if quantity is None:
            return jsonify({
                'status': 'error',
                'message': "Quantity required"
            }), 400
        cart_item = CartItem.get_by_id(item_id)
        if not cart_item:
            return jsonify({
                'status': 'error',
                'message': "Cart item not found"
            }), 404
        cart = Cart.get_by_id(cart_item['cart_id'])
        if not cart or cart['user_id'] != int(user['id']):
            return jsonify({
                'status': 'error',
                'message': "Unauthorized"
            }), 403
        if quantity <= 0:
            CartItem.delete(item_id)
            return jsonify({
                'status': 'success',
                'message': "Item removed from cart"
            })
        product = Product.get_by_id(cart_item['product_id'])
        if not product:
            return jsonify({
                'status': 'error',
                'message': "Product not found"
            }), 404
        CartItem.update(item_id, {'quantity': quantity})
        subtotal = float(product.get('price', 0) or 0) * quantity
        return jsonify({
            'status': 'success',
            'message': "Cart item updated",
            'data': {
                'item_id': item_id,
                'product_id': cart_item['product_id'],
                'product_name': product.get('name'),
                'quantity': quantity,
                'subtotal': subtotal
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Update cart error: {str(e)}'
        }), 500

@bp.route('/cart/remove/<int:item_id>', methods=['DELETE'])
def remove_cart_item(item_id):
    try:
        user, error = _get_user_or_error()
        if error:
            return error
        from app.models.cart import CartItem, Cart
        cart_item = CartItem.get_by_id(item_id)
        if not cart_item:
            return jsonify({
                'status': 'error',
                'message': f'Cart item {item_id} not found'
            }), 404
        cart = Cart.get_by_id(cart_item['cart_id'])
        if not cart or cart['user_id'] != int(user['id']):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 403
        CartItem.delete(item_id)
        return jsonify({
            'status': 'success',
            'message': 'Item removed from cart',
            'data': {
                'removed_item_id': item_id,
                'product_id': cart_item['product_id']
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Remove from cart error: {str(e)}'
        }), 500

@bp.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    try:
        user, error = _get_user_or_error()
        if error:
            return error
        from app.models.cart import Cart, CartItem
        cart = Cart.get_by_user_id(int(user['id']))
        if not cart:
            return jsonify({
                'status': 'success',
                'message': 'Cart is already empty'
            })
        CartItem.delete_by_cart_id(cart['id'])
        return jsonify({
            'status': 'success',
            'message': 'Cart cleared successfully',
            'data': {
                'cart_id': cart.get('id'),
                'items_removed': True
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Clear cart error: {str(e)}'
        }), 500

@bp.route('/cart/checkout', methods=['POST'])
def checkout_cart():
    try:
        user, error = _get_user_or_error()
        if error:
            return error
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        from app.models.transaction import Transaction, TransactionItem
        from app.models.stock import Stock
        data = request.json
        payment_method = data.get('payment_method', 'Bank Transfer')
        shipping_address = data.get('shipping_address')
        notes = data.get('notes', '')
        if not shipping_address:
            shipping_address = user.get('address')
        cart = Cart.get_by_user_id(int(user['id']))
        if not cart:
            return jsonify({
                'status': 'error',
                'message': 'Cart is empty'
            }), 400
        cart_items = CartItem.get_by_cart_id(cart['id'])
        if not cart_items:
            return jsonify({
                'status': 'error',
                'message': 'Cart is empty'
            }), 400
        total_amount = 0
        order_items = []
        for item in cart_items:
            product = Product.get_by_id(item.get('product_id'))
            if not product:
                continue
            stock = Stock.get_by_product_id(product['id'])
            if not stock or stock.get('quantity', 0) < item.get('quantity', 0):
                return jsonify({
                    'status': 'error',
                    'message': f'Insufficient stock for {product.get("name")}. Available: {stock.get("quantity", 0) if stock else 0}'
                }), 400
            price = float(product.get('price') or 0)
            subtotal = price * item.get('quantity', 0)
            total_amount += subtotal
            order_items.append({
                'product_id': product['id'],
                'quantity': item.get('quantity'),
                'price': price,
                'subtotal': subtotal
            })
        def generate_code():
            date_str = datetime.utcnow().strftime("%Y%m%d")
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            return f"TRX-{date_str}-{random_str}"
        transaction = Transaction.create({
            'transaction_code': generate_code(),
            'user_id': int(user['id']),
            'total_amount': total_amount,
            'status': 'pending',
            'payment_method': payment_method,
            'shipping_address': shipping_address,
            'notes': notes
        })
        if not transaction:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create transaction'
            }), 500
        for oi in order_items:
            TransactionItem.create({
                'transaction_id': transaction['id'],
                'product_id': oi['product_id'],
                'quantity': oi['quantity'],
                'price': oi['price'],
                'subtotal': oi['subtotal']
            })
            stock = Stock.get_by_product_id(oi['product_id'])
            if stock:
                Stock.update(stock['id'], {'quantity': stock['quantity'] - oi['quantity']})
        CartItem.delete_by_cart_id(cart['id'])
        return jsonify({
            'status': 'success',
            'message': 'Checkout successful. Order created!',
            'data': {
                'transaction_id': transaction.get('id'),
                'transaction_code': transaction.get('transaction_code'),
                'total_amount': float(transaction.get('total_amount')),
                'status': transaction.get('status'),
                'item_count': len(order_items)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Checkout error: {str(e)}'
        }), 500

@bp.route('/health', methods=['GET'])
def health_check():
    try:
        from app.supabase_client import db as supabase_db
        supabase_db.get_client().postgrest.schema('public').from_('users').select('id').limit(1).execute()
        database = 'connected'
    except Exception as e:
        database = f'error: {str(e)}'
    return jsonify({
        'status': 'success',
        'message': 'API is healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': database
    })