from app.models.product import Product
from app.models.stock import Stock
from app import response, db
from flask import request

def index():
    try:
        products = Product.query.all()
        data = transform(products)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def show(id):
    try:
        product = Product.query.filter_by(id=id).first()
        if not product:
            return response.not_found([], "Product not found")
        
        data = single_transform(product)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def store():
    try:
        name = request.json.get('name')
        description = request.json.get('description', '')
        price = request.json.get('price')
        category = request.json.get('category')
        image_url = request.json.get('image_url', '')
        
        product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=image_url
        )
        
        db.session.add(product)
        db.session.flush()  # Get the product ID
        
        # Create stock for this product
        stock = Stock(
            product_id=product.id,
            quantity=request.json.get('stock_quantity', 0),
            min_stock=request.json.get('min_stock', 10)
        )
        db.session.add(stock)
        
        db.session.commit()
        return response.created([], "Product created successfully")
        
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def update(id):
    try:
        product = Product.query.filter_by(id=id).first()
        if not product:
            return response.not_found([], "Product not found")
        
        product.name = request.json.get('name', product.name)
        product.description = request.json.get('description', product.description)
        product.price = request.json.get('price', product.price)
        product.category = request.json.get('category', product.category)
        product.image_url = request.json.get('image_url', product.image_url)
        product.is_available = request.json.get('is_available', product.is_available)
        
        db.session.commit()
        return response.ok([], "Product updated successfully")
        
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def delete(id):
    try:
        product = Product.query.filter_by(id=id).first()
        if not product:
            return response.not_found([], "Product not found")
        
        db.session.delete(product)
        db.session.commit()
        return response.ok([], "Product deleted successfully")
        
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def transform(products):
    array = []
    for product in products:
        array.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price) if product.price else 0,
            'category': product.category,
            'image_url': product.image_url,
            'is_available': product.is_available,
            'stock': product.stocks.quantity if product.stocks else 0
        })
    return array

def single_transform(product):
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price) if product.price else 0,
        'category': product.category,
        'image_url': product.image_url,
        'is_available': product.is_available,
        'stock': product.stocks.quantity if product.stocks else 0,
        'min_stock': product.stocks.min_stock if product.stocks else 10,
        'created_at': product.created_at.isoformat() if product.created_at else None
    }