from app.models.stock import Stock
from app.models.product import Product
from app import response, db
from flask import request
from datetime import datetime 

def index():
    try:
        stocks = Stock.query.join(Product).all()
        data = transform(stocks)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def show(id):
    try:
        stock = Stock.query.filter_by(id=id).first()
        if not stock:
            return response.not_found([], "Stock not found")
        data = single_transform(stock)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def store():
    try:
        product_id = request.json.get('product_id')
        quantity = request.json.get('quantity', 0)
        min_stock = request.json.get('min_stock', 10)
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            return response.not_found([], "Product not found")
        existing_stock = Stock.query.filter_by(product_id=product_id).first()
        if existing_stock:
            return response.bad_request([], "Stock already exists for this product")
        stock = Stock(
            product_id=product_id,
            quantity=quantity,
            min_stock=min_stock,
            last_restock=datetime.utcnow() 
        )
        db.session.add(stock)
        db.session.commit()
        return response.created(single_transform(stock), "Stock created successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def update(id):
    try:
        stock = Stock.query.filter_by(id=id).first()
        if not stock:
            return response.not_found([], "Stock not found")
        quantity = request.json.get('quantity')
        if quantity is not None:
            stock.quantity = quantity
        min_stock = request.json.get('min_stock')
        if min_stock is not None:
            stock.min_stock = min_stock
        stock.last_restock = datetime.utcnow()  
        stock.updated_at = datetime.utcnow()   
        db.session.commit()
        return response.ok(single_transform(stock), "Stock updated successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def delete(id):
    try:
        stock = Stock.query.filter_by(id=id).first()
        if not stock:
            return response.not_found([], "Stock not found")
        db.session.delete(stock)
        db.session.commit()
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
        stock = Stock.query.filter_by(product_id=product_id).first()
        if not stock:
            product = Product.query.filter_by(id=product_id).first()
            if not product:
                return response.not_found([], "Product not found")
            stock = Stock(
                product_id=product_id,
                quantity=quantity,
                min_stock=10,
                last_restock=datetime.utcnow()
            )
            db.session.add(stock)
        else:
            stock.quantity += quantity
            stock.last_restock = datetime.utcnow() 
        db.session.commit()
        return response.ok(single_transform(stock), f"Restocked {quantity} items successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def check_low_stock():
    try:
        low_stocks = Stock.query.filter(Stock.quantity <= Stock.min_stock).all()
        data = transform(low_stocks)
        return response.ok(data, "Low stock items")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def reduce_stock(product_id, quantity):
    """Helper function to reduce stock (used by TransactionController)"""
    try:
        stock = Stock.query.filter_by(product_id=product_id).first()
        if not stock:
            return False, f"Stock not found for product {product_id}"
        if stock.quantity < quantity:
            return False, f"Insufficient stock. Available: {stock.quantity}, Requested: {quantity}"
        stock.quantity -= quantity
        stock.updated_at = datetime.utcnow()
        return True, "Stock reduced successfully"
    except Exception as e:
        return False, str(e)

def increase_stock(product_id, quantity):
    """Helper function to increase stock"""
    try:
        stock = Stock.query.filter_by(product_id=product_id).first()
        if not stock:
            stock = Stock(
                product_id=product_id,
                quantity=quantity,
                min_stock=10,
                last_restock=datetime.utcnow()
            )
            db.session.add(stock)
        else:
            stock.quantity += quantity
            stock.last_restock = datetime.utcnow()
            stock.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Stock increased successfully"
        
    except Exception as e:
        return False, str(e)

def transform(stocks):
    array = []
    for stock in stocks:
        array.append({
            'id': stock.id,
            'product_id': stock.product_id,
            'product_name': stock.product.name if stock.product else 'Unknown',
            'product_price': float(stock.product.price) if stock.product and stock.product.price else 0,
            'quantity': stock.quantity,
            'min_stock': stock.min_stock,
            'last_restock': stock.last_restock.isoformat() if stock.last_restock else None,
            'status': 'LOW' if stock.quantity <= stock.min_stock else 'OK',
            'status_color': 'danger' if stock.quantity <= stock.min_stock else 'success',
            'created_at': stock.created_at.isoformat() if stock.created_at else None,
            'updated_at': stock.updated_at.isoformat() if stock.updated_at else None
        })
    return array

def single_transform(stock):
    return {
        'id': stock.id,
        'product_id': stock.product_id,
        'product_name': stock.product.name if stock.product else 'Unknown',
        'product_price': float(stock.product.price) if stock.product and stock.product.price else 0,
        'product_category': stock.product.category if stock.product else None,
        'quantity': stock.quantity,
        'min_stock': stock.min_stock,
        'last_restock': stock.last_restock.isoformat() if stock.last_restock else None,
        'status': 'LOW' if stock.quantity <= stock.min_stock else 'OK',
        'status_color': 'danger' if stock.quantity <= stock.min_stock else 'success',
        'created_at': stock.created_at.isoformat() if stock.created_at else None,
        'updated_at': stock.updated_at.isoformat() if stock.updated_at else None
    }