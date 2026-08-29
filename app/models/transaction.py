from app.supabase_client import db
from datetime import datetime

class Transaction:
    table_name = 'transactions'
    
    @staticmethod
    def create(data):
        payload = {
            'transaction_code': data.get('transaction_code'),
            'user_id': data.get('user_id'),
            'total_amount': float(data.get('total_amount', 0)),
            'status': data.get('status', 'pending'),
            'payment_method': data.get('payment_method'),
            'shipping_address': data.get('shipping_address'),
            'notes': data.get('notes'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        response = db.table(Transaction.table_name).insert(payload).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(transaction_id):
        response = db.table(Transaction.table_name).select("*").eq('id', transaction_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_user_id(user_id):
        response = db.table(Transaction.table_name).select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
        return response.data if response.data else []
    
    @staticmethod
    def get_all():
        response = db.table(Transaction.table_name).select("*").order('created_at', desc=True).execute()
        return response.data if response.data else []
    
    @staticmethod
    def get_today():
        today = datetime.utcnow().date().isoformat()
        response = db.table(Transaction.table_name).select("*").gte('created_at', today).execute()
        return response.data if response.data else []
    
    @staticmethod
    def get_recent_by_user(user_id, limit=5):
        response = db.table(Transaction.table_name).select("*").eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        return response.data if response.data else []
    
    @staticmethod
    def update(transaction_id, data):
        payload = {}
        allowed_fields = ['status', 'payment_method', 'shipping_address', 'notes', 'total_amount']
        for field in allowed_fields:
            if field in data:
                if field == 'total_amount':
                    payload[field] = float(data[field])
                else:
                    payload[field] = data[field]
        
        payload['updated_at'] = datetime.utcnow().isoformat()
        
        response = db.table(Transaction.table_name).update(payload).eq('id', transaction_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(transaction_id):
        response = db.table(Transaction.table_name).delete().eq('id', transaction_id).execute()
        return response.data
    
    @staticmethod
    def count_by_user(user_id):
        response = db.table(Transaction.table_name).select("id", count='exact').eq('user_id', user_id).execute()
        return response.count if hasattr(response, 'count') else 0
    
    @staticmethod
    def sum_total_by_user(user_id):
        response = db.table(Transaction.table_name).select("total_amount").eq('user_id', user_id).execute()
        if response.data:
            return sum(float(t.get('total_amount', 0)) for t in response.data)
        return 0
    
    @staticmethod
    def sum_total_all():
        response = db.table(Transaction.table_name).select("total_amount").execute()
        if response.data:
            return sum(float(t.get('total_amount', 0)) for t in response.data)
        return 0

class TransactionItem:
    table_name = 'transaction_items'
    
    @staticmethod
    def create(data):
        payload = {
            'transaction_id': data.get('transaction_id'),
            'product_id': data.get('product_id'),
            'quantity': int(data.get('quantity', 1)),
            'price': float(data.get('price', 0)),
            'subtotal': float(data.get('subtotal', 0)),
            'created_at': datetime.utcnow().isoformat()
        }
        response = db.table(TransactionItem.table_name).insert(payload).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_transaction_id(transaction_id):
        response = db.table(TransactionItem.table_name).select("*").eq('transaction_id', transaction_id).execute()
        return response.data if response.data else []
    
    @staticmethod
    def delete_by_transaction_id(transaction_id):
        response = db.table(TransactionItem.table_name).delete().eq('transaction_id', transaction_id).execute()
        return response.data
