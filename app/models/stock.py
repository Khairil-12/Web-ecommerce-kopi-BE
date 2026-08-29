from app.supabase_client import db
from datetime import datetime

class Stock:
    table_name = 'stocks'
    
    @staticmethod
    def create(data):
        payload = {
            'product_id': data.get('product_id'),
            'quantity': int(data.get('quantity', 0)),
            'min_stock': int(data.get('min_stock', 10)),
            'last_restock': datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        response = db.table(Stock.table_name).insert(payload).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(stock_id):
        response = db.table(Stock.table_name).select("*").eq('id', stock_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_product_id(product_id):
        response = db.table(Stock.table_name).select("*").eq('product_id', product_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_all():
        response = db.table(Stock.table_name).select("*").execute()
        return response.data if response.data else []
    
    @staticmethod
    def update(stock_id, data):
        payload = {}
        if 'quantity' in data:
            payload['quantity'] = int(data['quantity'])
        if 'min_stock' in data:
            payload['min_stock'] = int(data['min_stock'])
        if 'last_restock' in data:
            payload['last_restock'] = data['last_restock']
        
        payload['updated_at'] = datetime.utcnow().isoformat()
        
        response = db.table(Stock.table_name).update(payload).eq('id', stock_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def update_by_product_id(product_id, data):
        payload = {}
        if 'quantity' in data:
            payload['quantity'] = int(data['quantity'])
        if 'min_stock' in data:
            payload['min_stock'] = int(data['min_stock'])
        if 'last_restock' in data:
            payload['last_restock'] = data['last_restock']
        
        payload['updated_at'] = datetime.utcnow().isoformat()
        
        response = db.table(Stock.table_name).update(payload).eq('product_id', product_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(stock_id):
        response = db.table(Stock.table_name).delete().eq('id', stock_id).execute()
        return response.data
    
    @staticmethod
    def delete_by_product_id(product_id):
        response = db.table(Stock.table_name).delete().eq('product_id', product_id).execute()
        return response.data
    
    @staticmethod
    def count_low_stock():
        response = db.table(Stock.table_name).select("id", count='exact').filter('quantity', 'lte', 'min_stock').execute()
        return response.count if hasattr(response, 'count') else 0
