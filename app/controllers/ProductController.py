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
        data = request.json
        
        # Field required
        name = data.get('name')
        price = data.get('price')
        category = data.get('category')
        
        if not all([name, price, category]):
            return response.bad_request([], "Name, price, and category are required")
        
        # Create product dengan semua field
        product = Product(
            name=name,
            description=data.get('description', ''),
            price=float(price),
            original_price=data.get('original_price'),
            category=category,
            image_url=data.get('image_url', '/static/images/default-product.jpg'),
            is_available=data.get('is_available', True),
            
            # Field baru untuk kopi
            weight=data.get('weight'),
            type=data.get('type'),
            origin=data.get('origin'),
            process=data.get('process'),
            roast_level=data.get('roast_level'),
            flavor_notes=data.get('flavor_notes'),
            brewing_methods=data.get('brewing_methods'),
            specifications=data.get('specifications'),
            grade=data.get('grade'),
            certification=data.get('certification'),
            is_featured=data.get('is_featured', False)
        )
        
        # Hitung diskon otomatis
        product.calculate_discount()
        
        db.session.add(product)
        db.session.flush()  # Get product ID
        
        # Create stock entry
        from app.models.stock import Stock
        stock_quantity = data.get('stock', 0)
        stock = Stock(
            product_id=product.id,
            quantity=stock_quantity,
            min_stock=data.get('min_stock', 10)
        )
        db.session.add(stock)
        
        db.session.commit()
        
        return response.created([], "Product created successfully")
        
    except Exception as e:
        db.session.rollback()
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
        # normalize specifications into an array `specs` for frontend convenience
        raw_specs = product.specifications
        specs = []
        try:
            if raw_specs is None:
                specs = []
            elif isinstance(raw_specs, (list, tuple)):
                specs = list(raw_specs)
            else:
                s = str(raw_specs).strip()
                # try parse JSON array first
                try:
                    import json

                    j = json.loads(s)
                    if isinstance(j, list):
                        specs = [str(x).strip() for x in j if str(x).strip()]
                    else:
                        specs = []
                except Exception:
                    # split on newlines, <br>, semicolon or pipe. Avoid splitting on comma (may be part of values)
                    import re

                    parts = re.split(r"\r?\n|<br\s*/?>|;|\|", s)
                    specs = [p.strip() for p in parts if p and p.strip()]
        except Exception:
            specs = []

        # build metadata from specs (e.g. 'Asal: Gayo' -> spec_meta['asal'] = 'Gayo')
        spec_meta = {}
        try:
            for s in specs:
                if not s or ':' not in s:
                    continue
                k, v = s.split(':', 1)
                key = k.strip().lower().replace(' ', '_')
                val = v.strip()
                if key:
                    spec_meta[key] = val
        except Exception:
            spec_meta = {}

        array.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price) if product.price else 0,
            'category': product.category,
            'image_url': product.image_url,
            'is_available': product.is_available,
            'stock': product.stocks.quantity if product.stocks else 0,
            'specifications': product.specifications,
            'specs': specs,
            'spec_meta': spec_meta,
        })
    return array

def single_transform(product):
    # prepare specs array similar to transform()
    raw_specs = product.specifications
    specs = []
    try:
        if raw_specs is None:
            specs = []
        elif isinstance(raw_specs, (list, tuple)):
            specs = list(raw_specs)
        else:
            s = str(raw_specs).strip()
            try:
                import json

                j = json.loads(s)
                if isinstance(j, list):
                    specs = [str(x).strip() for x in j if str(x).strip()]
                else:
                    specs = []
            except Exception:
                import re

                parts = re.split(r"\r?\n|<br\s*/?>|;|\|", s)
                specs = [p.strip() for p in parts if p and p.strip()]
    except Exception:
        specs = []

    # build metadata from specs
    spec_meta = {}
    try:
        for s in specs:
            if not s or ':' not in s:
                continue
            k, v = s.split(':', 1)
            key = k.strip().lower().replace(' ', '_')
            val = v.strip()
            if key:
                spec_meta[key] = val
    except Exception:
        spec_meta = {}

    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price) if product.price else 0,
        'category': product.category,
        'image_url': product.image_url,
        'is_available': product.is_available,
        'stock': product.stocks.quantity if product.stocks else 0,
        'specifications': product.specifications,
        'specs': specs,
        'spec_meta': spec_meta,
        'min_stock': product.stocks.min_stock if product.stocks else 10,
        'created_at': product.created_at.isoformat() if product.created_at else None
    }