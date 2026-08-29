import json
import re
import shutil
import os
from flask import request
from werkzeug.utils import secure_filename
from app import response
from app.models.product import Product
from app.models.stock import Stock
from app.supabase_client import db

UPLOAD_FOLDER = 'static/img/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def normalize_image_url(url):
    if not url:
        return url
    url = url.replace('\\', '/').strip()
    if url.startswith('/'):
        url = url.lstrip('/')
    if url.startswith('static/'):
        url = url[len('static/'):]
    return url

def _load_stocks():
    stocks = Stock.get_all()
    stock_map = {}
    for s in stocks:
        stock_map[s.get('product_id')] = s
    return stock_map

def index():
    try:
        products = Product.get_all()
        stock_map = _load_stocks()
        data = transform(products, stock_map)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def show(id):
    try:
        product = Product.get_by_id(id)
        if not product:
            return response.not_found([], "Product not found")
        stock = Stock.get_by_product_id(id)
        data = single_transform(product, stock)
        return response.ok(data, "")
    except Exception as e:
        print("SHOW PRODUCT ERROR:", e)
        return response.server_error([], f"Error: {e}")

def _calculate_discount(payload):
    try:
        original = payload.get('original_price')
        price = payload.get('price')
        if original and price is not None and float(original) > float(price):
            payload['discount_percentage'] = round(((float(original) - float(price)) / float(original)) * 100, 1)
            payload['is_discounted'] = True
        else:
            payload['discount_percentage'] = 0
            payload['is_discounted'] = False
    except Exception:
        payload['discount_percentage'] = 0
        payload['is_discounted'] = False
    return payload

def _build_payload(src):
    payload = {}
    get = src.get
    for fld in ['name', 'description', 'original_price', 'category', 'image_url',
                'weight', 'type', 'origin', 'process', 'roast_level', 'flavor_notes',
                'brewing_methods', 'specifications', 'grade', 'certification']:
        val = get(fld)
        if fld == 'image_url' and val:
            val = normalize_image_url(val)
        if fld in ('original_price',) and val in (None, ''):
            val = None
        payload[fld] = val
    try:
        payload['price'] = float(get('price')) if get('price') not in (None, '') else 0
    except Exception:
        payload['price'] = get('price')
    payload['is_available'] = str(get('is_available', '1')) == '1'
    payload['is_featured'] = str(get('is_featured', '0')) == '1'
    payload['is_discounted'] = str(get('is_discounted', '0')) == '1'
    try:
        payload['discount_percentage'] = float(get('discount_percentage')) if get('discount_percentage') else 0
    except Exception:
        payload['discount_percentage'] = 0
    if get('rating'):
        try:
            payload['rating'] = float(get('rating'))
        except Exception:
            pass
    if 'image_url' not in payload or not payload.get('image_url'):
        payload['image_url'] = '/static/images/default-product.jpg'
    return payload

def _copy_to_fe(image_path, filename):
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        fe_img_dir = os.path.abspath(os.path.join(base_dir, '..', 'Web-ecommerce-kopi-FE', 'img', 'products'))
        if not os.path.exists(fe_img_dir):
            os.makedirs(fe_img_dir)
        shutil.copy(image_path, os.path.join(fe_img_dir, filename))
    except Exception as e:
        print('FE copy error:', e)

def _save_upload(product_id, upload_src):
    image = upload_src.get('image') if hasattr(upload_src, 'get') else None
    if not image or not allowed_file(image.filename):
        return None
    filename = secure_filename(f"{product_id}_{image.filename}")
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(image_path)
    _copy_to_fe(image_path, filename)
    return filename

def store():
    try:
        if request.form:
            data = request.form
            payload = _build_payload(data)
        else:
            data = request.json
            if not data:
                return response.bad_request([], "No data provided")
            payload = _build_payload(data)

        name = payload.get('name')
        price = payload.get('price')
        category = payload.get('category')
        if not all([name, price, category]):
            return response.bad_request([], "Name, price, and category are required")

        payload = _calculate_discount(payload)

        product = Product.create(payload)
        if not product:
            return response.server_error([], "Failed to create product in database")

        from datetime import datetime
        stock_qty_field = data.get('stock') if hasattr(data, 'get') else request.form.get('stock')
        try:
            stock_quantity = int(stock_qty_field) if stock_qty_field else 0
        except Exception:
            stock_quantity = 0
        min_stock = data.get('min_stock', 10) if hasattr(data, 'get') else request.form.get('min_stock', 10)
        Stock.create({
            'product_id': product.get('id'),
            'quantity': stock_quantity,
            'min_stock': int(min_stock or 10)
        })

        filename = _save_upload(product.get('id'), request.files if request.files else {})
        if filename:
            Product.update(product.get('id'), {'image_url': f'img/products/{filename}'})

        return response.created([], "Product created successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def update(id):
    try:
        product = Product.get_by_id(id)
        if not product:
            return response.not_found([], "Product not found")

        if request.form:
            payload = _build_payload(request.form)
        else:
            data = request.json
            if not data:
                return response.bad_request([], "No data provided")
            payload = _build_payload(data)

        payload = _calculate_discount(payload)

        filename = _save_upload(id, request.files if request.files else {})
        if filename:
            payload['image_url'] = f'img/products/{filename}'

        Product.update(id, payload)
        return response.ok([], "Product updated successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def delete(id):
    try:
        product = Product.get_by_id(id)
        if not product:
            return response.not_found([], "Product not found")
        Stock.delete_by_product_id(id)
        Product.delete(id)
        return response.ok([], "Product deleted successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def _parse_specs(raw_specs):
    specs = []
    try:
        if raw_specs is None:
            specs = []
        elif isinstance(raw_specs, (list, tuple)):
            specs = list(raw_specs)
        else:
            s = str(raw_specs).strip()
            try:
                j = json.loads(s)
                if isinstance(j, list):
                    specs = [str(x).strip() for x in j if str(x).strip()]
                else:
                    specs = []
            except Exception:
                parts = re.split(r"\r?\n|<br\s*/?>|;|\|", s)
                specs = [p.strip() for p in parts if p and p.strip()]
    except Exception:
        specs = []
    return specs

def _parse_spec_meta(specs):
    spec_meta = {}
    try:
        for s in specs:
            if not s or ':' not in s:
                continue
            k, v = s.split(':', 1)
            key = k.strip().lower().replace(' ', '_')
            if key:
                spec_meta[key] = v.strip()
    except Exception:
        spec_meta = {}
    return spec_meta

def _serialize(product, stock):
    specs = _parse_specs(product.get('specifications'))
    return {
        'id': product.get('id'),
        'name': product.get('name'),
        'description': product.get('description'),
        'price': float(product.get('price')) if product.get('price') else 0,
        'original_price': float(product.get('original_price')) if product.get('original_price') else None,
        'category': product.get('category'),
        'image_url': product.get('image_url'),
        'is_available': product.get('is_available'),
        'is_featured': product.get('is_featured'),
        'is_discounted': product.get('is_discounted'),
        'discount_percentage': product.get('discount_percentage'),
        'rating': product.get('rating'),
        'stock': stock.get('quantity', 0) if stock else 0,
        'weight': product.get('weight'),
        'type': product.get('type'),
        'origin': product.get('origin'),
        'process': product.get('process'),
        'roast_level': product.get('roast_level'),
        'flavor_notes': product.get('flavor_notes'),
        'brewing_methods': product.get('brewing_methods'),
        'specifications': product.get('specifications'),
        'specs': specs,
        'spec_meta': _parse_spec_meta(specs),
        'grade': product.get('grade'),
        'certification': product.get('certification'),
    }

def transform(products, stock_map=None):
    if stock_map is None:
        stock_map = _load_stocks()
    return [_serialize(p, stock_map.get(p.get('id'))) for p in products]

def single_transform(product, stock=None):
    data = _serialize(product, stock)
    data['min_stock'] = stock.get('min_stock', 10) if stock else 10
    data['created_at'] = product.get('created_at')
    data['updated_at'] = product.get('updated_at')
    return data