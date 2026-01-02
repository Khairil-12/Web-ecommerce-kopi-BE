from app.models.product import Product
from app.models.stock import Stock
from app import response, db
from flask import request
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Konfigurasi upload
UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        print("SHOW PRODUCT ERROR:", e)
        return response.server_error([], f"Error: {e}")


def store():
    try:
        # Handle FormData (not JSON)
        if request.form:
            # Field required
            name = request.form.get('name')
            price = request.form.get('price')
            category = request.form.get('category')
            
            if not all([name, price, category]):
                return response.bad_request([], "Name, price, and category are required")
            
            # Create product dengan semua field
            product = Product(
                name=name,
                description=request.form.get('description', ''),
                price=float(price) if price else 0,
                original_price=float(request.form.get('original_price')) if request.form.get('original_price') else None,
                category=category,
                image_url='/static/images/default-product.jpg',  # Default
                is_available=request.form.get('is_available', '1') == '1',
                
                # Field baru untuk kopi
                weight=request.form.get('weight'),
                type=request.form.get('type'),
                origin=request.form.get('origin'),
                process=request.form.get('process'),
                roast_level=request.form.get('roast_level'),
                flavor_notes=request.form.get('flavor_notes'),
                brewing_methods=request.form.get('brewing_methods'),
                specifications=request.form.get('specifications'),
                grade=request.form.get('grade'),
                certification=request.form.get('certification'),
                is_featured=request.form.get('is_featured', '0') == '1',
                is_discounted=request.form.get('is_discounted', '0') == '1',
                discount_percentage=float(request.form.get('discount_percentage')) if request.form.get('discount_percentage') else 0,
                rating=float(request.form.get('rating')) if request.form.get('rating') else None
            )
            
            db.session.add(product)
            db.session.flush()  # Get product ID
            
            # Handle file upload
            if 'image' in request.files:
                image = request.files['image']
                if image and allowed_file(image.filename):
                    filename = secure_filename(f"{product.id}_{image.filename}")
                    # Pastikan folder uploads exists
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                    
                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    image.save(image_path)
                    product.image_url = f'/static/uploads/products/{filename}'
            
            # Calculate discount
            product.calculate_discount()
            
            # Create stock entry
            stock_quantity = int(request.form.get('stock', 0))
            stock = Stock(
                product_id=product.id,
                quantity=stock_quantity,
                min_stock=int(request.form.get('min_stock', 10))
            )
            db.session.add(stock)
            
            db.session.commit()
            
            return response.created([], "Product created successfully")
        else:
            # Fallback to JSON if no FormData
            data = request.json
            if not data:
                return response.bad_request([], "No data provided")
            
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
        
        # Handle FormData (not JSON)
        if request.form:
            # Update fields from FormData
            if 'name' in request.form:
                product.name = request.form['name']
            if 'description' in request.form:
                product.description = request.form['description']
            if 'price' in request.form:
                product.price = float(request.form['price']) if request.form['price'] else 0
            if 'category' in request.form:
                product.category = request.form['category']
            if 'weight' in request.form:
                product.weight = request.form['weight']
            if 'type' in request.form:
                product.type = request.form['type']
            if 'origin' in request.form:
                product.origin = request.form['origin']
            if 'process' in request.form:
                product.process = request.form['process']
            if 'roast_level' in request.form:
                product.roast_level = request.form['roast_level']
            if 'flavor_notes' in request.form:
                product.flavor_notes = request.form['flavor_notes']
            if 'brewing_methods' in request.form:
                product.brewing_methods = request.form['brewing_methods']
            if 'specifications' in request.form:
                product.specifications = request.form['specifications']
            if 'grade' in request.form:
                product.grade = request.form['grade']
            if 'certification' in request.form:
                product.certification = request.form['certification']
            if 'is_featured' in request.form:
                product.is_featured = request.form['is_featured'] == '1'
            if 'is_available' in request.form:
                product.is_available = request.form['is_available'] == '1'
            if 'is_discounted' in request.form:
                product.is_discounted = request.form['is_discounted'] == '1'
            if 'discount_percentage' in request.form:
                product.discount_percentage = float(request.form['discount_percentage']) if request.form['discount_percentage'] else 0
            if 'rating' in request.form:
                product.rating = float(request.form['rating']) if request.form['rating'] else None
            if 'original_price' in request.form:
                product.original_price = float(request.form['original_price']) if request.form['original_price'] else None
            
            # Handle file upload
            if 'image' in request.files:
                image = request.files['image']
                if image and allowed_file(image.filename):
                    filename = secure_filename(f"{product.id}_{image.filename}")
                    # Pastikan folder uploads exists
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                    
                    # Hapus gambar lama jika ada
                    if product.image_url and os.path.exists(product.image_url.replace('/static/', '')):
                        try:
                            os.remove(product.image_url.replace('/static/', ''))
                        except:
                            pass
                    
                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    image.save(image_path)
                    product.image_url = f'/static/uploads/products/{filename}'
            
            # Recalculate discount
            product.calculate_discount()
            
            product.updated_at = datetime.utcnow()
            db.session.commit()
            
            return response.ok([], "Product updated successfully")
        else:
            # Fallback to JSON
            data = request.json
            if not data:
                return response.bad_request([], "No data provided")
            
            product.name = data.get('name', product.name)
            product.description = data.get('description', product.description)
            product.price = data.get('price', product.price)
            product.category = data.get('category', product.category)
            product.image_url = data.get('image_url', product.image_url)
            product.is_available = data.get('is_available', product.is_available)
            
            # Update additional fields if present
            if 'weight' in data:
                product.weight = data['weight']
            if 'type' in data:
                product.type = data['type']
            if 'origin' in data:
                product.origin = data['origin']
            if 'process' in data:
                product.process = data['process']
            if 'roast_level' in data:
                product.roast_level = data['roast_level']
            if 'flavor_notes' in data:
                product.flavor_notes = data['flavor_notes']
            if 'brewing_methods' in data:
                product.brewing_methods = data['brewing_methods']
            if 'specifications' in data:
                product.specifications = data['specifications']
            if 'grade' in data:
                product.grade = data['grade']
            if 'certification' in data:
                product.certification = data['certification']
            if 'is_featured' in data:
                product.is_featured = data['is_featured']
            
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
            'original_price': float(product.original_price) if product.original_price else None,
            'category': product.category,
            'image_url': product.image_url,
            'is_available': product.is_available,
            'is_featured': product.is_featured,
            'is_discounted': product.is_discounted,
            'discount_percentage': product.discount_percentage,
            'rating': product.rating,
            'stock': product.stocks.quantity if product.stocks else 0,
            'weight': product.weight,
            'type': product.type,
            'origin': product.origin,
            'process': product.process,
            'roast_level': product.roast_level,
            'flavor_notes': product.flavor_notes,
            'brewing_methods': product.brewing_methods,
            'specifications': product.specifications,
            'specs': specs,
            'spec_meta': spec_meta,
            'grade': product.grade,
            'certification': product.certification,
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
        'original_price': float(product.original_price) if product.original_price else None,
        'category': product.category,
        'image_url': product.image_url,
        'is_available': product.is_available,
        'is_featured': product.is_featured,
        'is_discounted': product.is_discounted,
        'discount_percentage': product.discount_percentage,
        'rating': product.rating,
        'stock': product.stocks.quantity if product.stocks else 0,
        'weight': product.weight,
        'type': product.type,
        'origin': product.origin,
        'process': product.process,
        'roast_level': product.roast_level,
        'flavor_notes': product.flavor_notes,
        'brewing_methods': product.brewing_methods,
        'specifications': product.specifications,
        'specs': specs,
        'spec_meta': spec_meta,
        'grade': product.grade,
        'certification': product.certification,
        'min_stock': product.stocks.min_stock if product.stocks else 10,
        'created_at': product.created_at.isoformat() if product.created_at else None,
        'updated_at': product.updated_at.isoformat() if product.updated_at else None
    }