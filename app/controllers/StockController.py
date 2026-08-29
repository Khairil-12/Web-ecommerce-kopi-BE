from app.models.stock import Stock
from app.models.product import Product
from app import response
from flask import request
from datetime import datetime

def index():
    try:
        stocks = Stock.get_all()
        products = Product.get_all()
        product_map = {p.get('id'): p for p in products}
        data = transform(stocks, product_map)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def show(id):
    try:
        stock = Stock.get_by_id(id)
        if not stock:
            return response.not_found([], "Stock not found")
        product = Product.get_by_id(stock['product_id'])
        data = single_transform(stock, product)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def store():
    try:
        product_id = request.json.get('product_id')
        quantity = request.json.get('quantity', 0)
        min_stock = request.json.get('min_stock', 10)
        product = Product.get_by_id(product_id)
        if not product:
            return response.not_found([], "Product not found")
        existing_stock = Stock.get_by_product_id(product_id)
        if existing_stock:
            return response.bad_request([], "Stock already exists for this product")
        stock = Stock.create({
            'product_id': product_id,
            'quantity': quantity,
            'min_stock': min_stock,
            'last_restock': datetime.utcnow().isoformat()
        })
        if not stock:
            return response.server_error([], "Failed to create stock")
        return response.created(single_transform(stock, product), "Stock created successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def update(id):
    try:
        stock = Stock.get_by_id(id)
        if not stock:
            return response.not_found([], "Stock not found")
        update_data = {}
        if request.json.get('quantity') is not None:
            update_data['quantity'] = request.json['quantity']
        if request.json.get('min_stock') is not None:
            update_data['min_stock'] = request.json['min_stock']
        update_data['last_restock'] = datetime.utcnow().isoformat()
        Stock.update(id, update_data)
        stock = Stock.get_by_id(id)
        product = Product.get_by_id(stock['product_id'])
        return response.ok(single_transform(stock, product), "Stock updated successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def delete(id):
    try:
        stock = Stock.get_by_id(id)
        if not stock:
            return response.not_found([], "Stock not found")
        Stock.delete(id)
        return response.ok([], "Stock deleted successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def restock():
    try:
        product_id = request.json.get('product_id')
        quantity = request.json.get('quantity', 0)
        if quantity <= 0:
            return response.bad_request([], "Quantity must be greater than 0")
        stock = Stock.get_by_product_id(product_id)
        if not stock:
            product = Product.get_by_id(product_id)
            if not product:
                return response.not_found([], "Product not found")
            stock = Stock.create({
                'product_id': product_id,
                'quantity': quantity,
                'min_stock': 10,
                'last_restock': datetime.utcnow().isoformat()
            })
        else:
            Stock.update(stock['id'], {
                'quantity': stock['quantity'] + quantity,
                'last_restock': datetime.utcnow().isoformat()
            })
        stock = Stock.get_by_product_id(product_id)
        product = Product.get_by_id(product_id)
        return response.ok(single_transform(stock, product), f"Restocked {quantity} items successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def check_low_stock():
    try:
        stocks = Stock.get_all()
        products = Product.get_all()
        product_map = {p.get('id'): p for p in products}
        low_stocks = [s for s in stocks if s.get('quantity', 0) <= s.get('min_stock', 10)]
        data = transform(low_stocks, product_map)
        return response.ok(data, "Low stock items")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def reduce_stock(product_id, quantity):
    try:
        stock = Stock.get_by_product_id(product_id)
        if not stock:
            return False, f"Stock not found for product {product_id}"
        if stock['quantity'] < quantity:
            return False, f"Insufficient stock. Available: {stock['quantity']}, Requested: {quantity}"
        Stock.update(stock['id'], {'quantity': stock['quantity'] - quantity})
        return True, "Stock reduced successfully"
    except Exception as e:
        return False, str(e)

def increase_stock(product_id, quantity):
    try:
        stock = Stock.get_by_product_id(product_id)
        if not stock:
            Stock.create({
                'product_id': product_id,
                'quantity': quantity,
                'min_stock': 10,
                'last_restock': datetime.utcnow().isoformat()
            })
        else:
            Stock.update(stock['id'], {
                'quantity': stock['quantity'] + quantity,
                'last_restock': datetime.utcnow().isoformat()
            })
        return True, "Stock increased successfully"
    except Exception as e:
        return False, str(e)

def transform(stocks, product_map=None):
    if product_map is None:
        products = Product.get_all()
        product_map = {p.get('id'): p for p in products}
    return [single_transform(s, product_map.get(s.get('product_id'))) for s in stocks]

def single_transform(stock, product=None):
    if product is None:
        product = Product.get_by_id(stock.get('product_id'))
    quantity = stock.get('quantity', 0)
    min_stock = stock.get('min_stock', 10)
    return {
        'id': stock.get('id'),
        'product_id': stock.get('product_id'),
        'product_name': product.get('name') if product else 'Unknown',
        'product_price': float(product.get('price')) if product and product.get('price') else 0,
        'product_category': product.get('category') if product else None,
        'quantity': quantity,
        'min_stock': min_stock,
        'last_restock': stock.get('last_restock'),
        'status': 'LOW' if quantity <= min_stock else 'OK',
        'status_color': 'danger' if quantity <= min_stock else 'success',
        'created_at': stock.get('created_at'),
        'updated_at': stock.get('updated_at')
    }