from app.supabase_client import db
from datetime import datetime

class Product:
    table_name = 'products'
    
    @staticmethod
    def create(data):
        payload = {
            'name': data.get('name'),
            'description': data.get('description'),
            'price': float(data.get('price', 0)),
            'category': data.get('category'),
            'image_url': data.get('image_url'),
            'is_available': data.get('is_available', True),
            'original_price': float(data.get('original_price')) if data.get('original_price') else None,
            'is_featured': data.get('is_featured', False),
            'is_discounted': data.get('is_discounted', False),
            'discount_percentage': float(data.get('discount_percentage', 0)),
            'rating': float(data.get('rating')) if data.get('rating') else None,
            'specifications': data.get('specifications'),
            'weight': data.get('weight'),
            'type': data.get('type'),
            'origin': data.get('origin'),
            'process': data.get('process'),
            'roast_level': data.get('roast_level'),
            'flavor_notes': data.get('flavor_notes'),
            'brewing_methods': data.get('brewing_methods'),
            'grade': data.get('grade'),
            'certification': data.get('certification'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        response = db.table(Product.table_name).insert(payload).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(product_id):
        response = db.table(Product.table_name).select("*").eq('id', product_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_all():
        response = db.table(Product.table_name).select("*").execute()
        return response.data if response.data else []
    
    @staticmethod
    def get_available():
        response = db.table(Product.table_name).select("*").eq('is_available', True).execute()
        return response.data if response.data else []
    
    @staticmethod
    def update(product_id, data):
        payload = {}
        allowed_fields = ['name', 'description', 'price', 'category', 'image_url', 'is_available', 
                         'original_price', 'is_featured', 'is_discounted', 'discount_percentage', 
                         'rating', 'specifications', 'weight', 'type', 'origin', 'process', 
                         'roast_level', 'flavor_notes', 'brewing_methods', 'grade', 'certification']
        
        for field in allowed_fields:
            if field in data:
                if field in ['price', 'original_price', 'discount_percentage', 'rating']:
                    payload[field] = float(data[field]) if data[field] is not None else None
                else:
                    payload[field] = data[field]
        
        payload['updated_at'] = datetime.utcnow().isoformat()
        
        response = db.table(Product.table_name).update(payload).eq('id', product_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(product_id):
        response = db.table(Product.table_name).delete().eq('id', product_id).execute()
        return response.data
    
    @staticmethod
    def count_available():
        response = db.table(Product.table_name).select("id", count='exact').eq('is_available', True).execute()
        return response.count if hasattr(response, 'count') else 0
