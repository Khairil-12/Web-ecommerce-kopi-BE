from flask import Blueprint, jsonify, request

bp = Blueprint('api', __name__)

# === HOME ===
@bp.route('/')
def home():
    return jsonify({
        'message': 'Ecommerce Kopi API',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'Home',
            'GET /users': 'List users',
            'POST /users': 'Register',
            'POST /login': 'Login',
            'GET /products': 'List products',
            'GET /products/<id>': 'Get product detail',
            'POST /products': 'Create product (admin)',
            'GET /stocks': 'List stocks',
            'GET /stocks/low-stock': 'Get low stock items',
            'POST /stocks/restock': 'Restock product'
        }
    })

# === USER ROUTES ===
@bp.route('/users', methods=['GET'])
def get_users():
    try:
        from app.controllers.UserController import index
        return index()
    except Exception as e:
        return jsonify({'error': f'UserController.index error: {str(e)}'}), 500

@bp.route('/users', methods=['POST'])
def create_user():
    try:
        from app.controllers.UserController import store
        return store()
    except Exception as e:
        return jsonify({'error': f'UserController.store error: {str(e)}'}), 500

@bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    try:
        from app.controllers.UserController import show
        return show(id)
    except Exception as e:
        return jsonify({'error': f'UserController.show error: {str(e)}'}), 500

@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        from app.controllers.UserController import update
        return update(id)
    except Exception as e:
        return jsonify({'error': f'UserController.update error: {str(e)}'}), 500

# === LOGIN ===
@bp.route('/login', methods=['POST'])
def login():
    try:
        from app.models.user import User
        from app import response
        
        data = request.json
        if not data or 'email' not in data or 'password' not in data:
            return response.bad_request([], 'Email and password are required')
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            return response.ok({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'full_name': user.full_name,
                'is_admin': user.is_admin,
                'is_verified': user.is_verified
            }, "Login successful")
        else:
            return response.bad_request([], "Invalid email or password")
            
    except Exception as e:
        return jsonify({'error': f'Login error: {str(e)}'}), 500

# === PRODUCT ROUTES ===
@bp.route('/products', methods=['GET'])
def get_products():
    try:
        from app.controllers.ProductController import index
        return index()
    except Exception as e:
        return jsonify({'error': f'ProductController.index error: {str(e)}'}), 500

@bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    try:
        from app.controllers.ProductController import show
        return show(id)
    except Exception as e:
        return jsonify({'error': f'ProductController.show error: {str(e)}'}), 500

@bp.route('/products', methods=['POST'])
def create_product():
    try:
        from app.controllers.ProductController import store
        return store()
    except Exception as e:
        return jsonify({'error': f'ProductController.store error: {str(e)}'}), 500

@bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    try:
        from app.controllers.ProductController import update
        return update(id)
    except Exception as e:
        return jsonify({'error': f'ProductController.update error: {str(e)}'}), 500

@bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    try:
        from app.controllers.ProductController import delete
        return delete(id)
    except Exception as e:
        return jsonify({'error': f'ProductController.delete error: {str(e)}'}), 500

# === STOCK ROUTES ===
@bp.route('/stocks', methods=['GET'])
def get_stocks():
    try:
        from app.controllers.StockController import index
        return index()
    except Exception as e:
        return jsonify({'error': f'StockController.index error: {str(e)}'}), 500

@bp.route('/stocks/<int:id>', methods=['GET'])
def get_stock(id):
    try:
        from app.controllers.StockController import show
        return show(id)
    except Exception as e:
        return jsonify({'error': f'StockController.show error: {str(e)}'}), 500

@bp.route('/stocks/low-stock', methods=['GET'])
def get_low_stock():
    try:
        from app.controllers.StockController import check_low_stock
        return check_low_stock()
    except Exception as e:
        return jsonify({'error': f'StockController.check_low_stock error: {str(e)}'}), 500

@bp.route('/stocks/restock', methods=['POST'])
def restock_product():
    try:
        from app.controllers.StockController import restock
        return restock()
    except Exception as e:
        return jsonify({'error': f'StockController.restock error: {str(e)}'}), 500

# === TRANSACTION ROUTES ===
@bp.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        from app.controllers.TransactionController import index
        return index()
    except Exception as e:
        return jsonify({'error': f'TransactionController.index error: {str(e)}'}), 500

@bp.route('/transactions/<int:id>', methods=['GET'])
def get_transaction(id):
    try:
        from app.controllers.TransactionController import show
        return show(id)
    except Exception as e:
        return jsonify({'error': f'TransactionController.show error: {str(e)}'}), 500

@bp.route('/transactions', methods=['POST'])
def create_transaction():
    try:
        from app.controllers.TransactionController import store
        return store()
    except Exception as e:
        return jsonify({'error': f'TransactionController.store error: {str(e)}'}), 500

# === CART ROUTES (Basic) ===
@bp.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    try:
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        from app import response
        
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return response.not_found([], "Cart not found")
        
        items = CartItem.query.filter_by(cart_id=cart.id).all()
        cart_data = []
        total = 0
        
        for item in items:
            product = Product.query.get(item.product_id)
            if product:
                item_total = float(product.price) * item.quantity
                total += item_total
                cart_data.append({
                    'id': item.id,
                    'product_id': product.id,
                    'product_name': product.name,
                    'price': float(product.price),
                    'quantity': item.quantity,
                    'subtotal': item_total,
                    'image_url': product.image_url
                })
        
        return response.ok({
            'cart_id': cart.id,
            'user_id': cart.user_id,
            'items': cart_data,
            'total': total,
            'item_count': len(cart_data)
        }, "Cart retrieved")
        
    except Exception as e:
        return jsonify({'error': f'Get cart error: {str(e)}'}), 500

@bp.route('/cart/<int:user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    try:
        from app.models.cart import Cart, CartItem
        from app.models.product import Product
        from app import response, db
        
        data = request.json
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        # Get or create cart
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.flush()
        
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return response.not_found([], "Product not found")
        
        # Check if item already in cart
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
        
        db.session.commit()
        
        return response.ok([], f"Added {quantity} x {product.name} to cart")
        
    except Exception as e:
        return jsonify({'error': f'Add to cart error: {str(e)}'}), 500

# === TEST ENDPOINT ===
@bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'message': 'API is working',
        'timestamp': '2024-12-17T10:00:00Z'
    })