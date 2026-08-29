from app.supabase_client import db
from datetime import datetime

class Cart:
    table_name = 'carts'
    
    @staticmethod
    def create(data):
        payload = {
            'user_id': data.get('user_id'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        response = db.table(Cart.table_name).insert(payload).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(cart_id):
        response = db.table(Cart.table_name).select("*").eq('id', cart_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_user_id(user_id):
        response = db.table(Cart.table_name).select("*").eq('user_id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(cart_id):
        response = db.table(Cart.table_name).delete().eq('id', cart_id).execute()
        return response.data

class CartItem:
    table_name = 'cart_items'
    
    @staticmethod
    def create(data):
        payload = {
            'cart_id': data.get('cart_id'),
            'product_id': data.get('product_id'),
            'quantity': int(data.get('quantity', 1)),
            'created_at': datetime.utcnow().isoformat()
        }
        response = db.table(CartItem.table_name).insert(payload).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(item_id):
        response = db.table(CartItem.table_name).select("*").eq('id', item_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_cart_id(cart_id):
        response = db.table(CartItem.table_name).select("*").eq('cart_id', cart_id).execute()
        return response.data if response.data else []
    
    @staticmethod
    def get_by_cart_and_product(cart_id, product_id):
        response = db.table(CartItem.table_name).select("*").eq('cart_id', cart_id).eq('product_id', product_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def update(item_id, data):
        payload = {}
        if 'quantity' in data:
            payload['quantity'] = int(data['quantity'])
        
        response = db.table(CartItem.table_name).update(payload).eq('id', item_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(item_id):
        response = db.table(CartItem.table_name).delete().eq('id', item_id).execute()
        return response.data
    
    @staticmethod
    def delete_by_cart_id(cart_id):
        response = db.table(CartItem.table_name).delete().eq('cart_id', cart_id).execute()
        return response.data
