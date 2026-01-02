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
        # Build list of allowed column names from model to avoid DB errors
        allowed_cols = set([c.name for c in Product.__table__.columns])

        # Handle FormData (not JSON)
        if request.form:
            # Basic required fields
            name = request.form.get('name')
            price = request.form.get('price')
            category = request.form.get('category')
            if not all([name, price, category]):
                return response.bad_request([], "Name, price, and category are required")

            # Prepare kwargs only for allowed columns
            kwargs = {}
            def add_if_allowed(key, val):
                if key in allowed_cols:
                    kwargs[key] = val

            add_if_allowed('name', name)
            add_if_allowed('description', request.form.get('description', ''))
            try:
                add_if_allowed('price', float(price) if price else 0)
            except Exception:
                add_if_allowed('price', price)
            add_if_allowed('original_price', float(request.form.get('original_price')) if request.form.get('original_price') else None)
            add_if_allowed('category', category)
            # default image_url only if column exists
            if 'image_url' in allowed_cols:
                kwargs.setdefault('image_url', '/static/images/default-product.jpg')
            add_if_allowed('is_available', request.form.get('is_available', '1') == '1')

            # additional optional fields
            add_if_allowed('weight', request.form.get('weight'))
            add_if_allowed('type', request.form.get('type'))
            add_if_allowed('origin', request.form.get('origin'))
            add_if_allowed('process', request.form.get('process'))
            add_if_allowed('roast_level', request.form.get('roast_level'))
            add_if_allowed('flavor_notes', request.form.get('flavor_notes'))
            add_if_allowed('brewing_methods', request.form.get('brewing_methods'))
            add_if_allowed('specifications', request.form.get('specifications'))
            add_if_allowed('grade', request.form.get('grade'))
            add_if_allowed('certification', request.form.get('certification'))
            if 'is_featured' in allowed_cols:
                add_if_allowed('is_featured', request.form.get('is_featured', '0') == '1')
            if 'is_discounted' in allowed_cols:
                add_if_allowed('is_discounted', request.form.get('is_discounted', '0') == '1')
            if 'discount_percentage' in allowed_cols and request.form.get('discount_percentage'):
                try:
                    add_if_allowed('discount_percentage', float(request.form.get('discount_percentage')))
                except Exception:
                    pass
            if 'rating' in allowed_cols and request.form.get('rating'):
                try:
                    add_if_allowed('rating', float(request.form.get('rating')))
                except Exception:
                    pass

            product = Product(**kwargs)
            db.session.add(product)
            db.session.flush()

            # Handle file upload
            if 'image' in request.files and 'image_url' in allowed_cols:
                image = request.files['image']
                if image and allowed_file(image.filename):
                    filename = secure_filename(f"{product.id}_{image.filename}")
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    image.save(image_path)
                    product.image_url = f'/static/uploads/products/{filename}'

            # Calculate discount if available
            if hasattr(product, 'calculate_discount'):
                try:
                    product.calculate_discount()
                except Exception:
                    pass

            # Create stock entry if model exists
            try:
                stock_quantity = int(request.form.get('stock', 0))
            except Exception:
                stock_quantity = 0
            stock = Stock(
                product_id=product.id,
                quantity=stock_quantity,
                min_stock=int(request.form.get('min_stock', 10))
            )
            db.session.add(stock)
            db.session.commit()
            return response.created([], "Product created successfully")
        else:
            # Fallback to JSON
            data = request.json
            if not data:
                return response.bad_request([], "No data provided")
            name = data.get('name')
            price = data.get('price')
            category = data.get('category')
            if not all([name, price, category]):
                return response.bad_request([], "Name, price, and category are required")

            allowed_cols = set([c.name for c in Product.__table__.columns])
            kwargs = {}
            def add_if_allowed_json(key, val):
                if key in allowed_cols and val is not None:
                    kwargs[key] = val

            add_if_allowed_json('name', name)
            add_if_allowed_json('description', data.get('description', ''))
            try:
                add_if_allowed_json('price', float(price))
            except Exception:
                add_if_allowed_json('price', price)
            add_if_allowed_json('original_price', data.get('original_price'))
            add_if_allowed_json('category', category)
            add_if_allowed_json('image_url', data.get('image_url', '/static/images/default-product.jpg'))
            add_if_allowed_json('is_available', data.get('is_available', True))
            # optional fields
            for fld in ['weight','type','origin','process','roast_level','flavor_notes','brewing_methods','specifications','grade','certification','is_featured']:
                add_if_allowed_json(fld, data.get(fld))

            product = Product(**kwargs)
            if hasattr(product, 'calculate_discount'):
                try:
                    product.calculate_discount()
                except Exception:
                    pass

            db.session.add(product)
            db.session.flush()
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
        # Build allowed columns set
        allowed_cols = set([c.name for c in Product.__table__.columns])

        # If form data, update allowed fields from form
        if request.form:
            for key in request.form.keys():
                if key in allowed_cols:
                    val = request.form.get(key)
                    # convert basic numeric fields
                    if key in ('price', 'original_price', 'discount_percentage', 'rating'):
                        try:
                            if val is None or val == '':
                                setattr(product, key, None)
                            else:
                                setattr(product, key, float(val))
                        except Exception:
                            setattr(product, key, val)
                    elif key in ('is_featured', 'is_discounted', 'is_available'):
                        setattr(product, key, val == '1')
                    else:
                        setattr(product, key, val)

            # Handle file upload safely
            if 'image' in request.files and 'image_url' in allowed_cols:
                image = request.files['image']
                if image and allowed_file(image.filename):
                    filename = secure_filename(f"{product.id}_{image.filename}")
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                    # attempt to remove old file if it's a local path
                    try:
                        old_path = None
                        if product.image_url and product.image_url.startswith('/static/'):
                            old_path = product.image_url.replace('/static/', '')
                            if os.path.exists(old_path):
                                os.remove(old_path)
                    except Exception:
                        pass

                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    image.save(image_path)
                    product.image_url = f'/static/uploads/products/{filename}'

            # Recalculate discount if available
            if hasattr(product, 'calculate_discount'):
                try:
                    product.calculate_discount()
                except Exception:
                    pass

            product.updated_at = datetime.utcnow()
            db.session.commit()
            return response.ok([], "Product updated successfully")

        # Fallback to JSON update
        data = request.json
        if not data:
            return response.bad_request([], "No data provided")
        for key, val in data.items():
            if key in allowed_cols:
                if key in ('price', 'original_price', 'discount_percentage', 'rating'):
                    try:
                        setattr(product, key, float(val) if val is not None and val != '' else None)
                    except Exception:
                        setattr(product, key, val)
                elif key in ('is_featured', 'is_discounted', 'is_available'):
                    setattr(product, key, bool(val))
                else:
                    setattr(product, key, val)

        if hasattr(product, 'calculate_discount'):
            try:
                product.calculate_discount()
            except Exception:
                pass

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