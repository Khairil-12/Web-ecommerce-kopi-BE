from app.supabase_client import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    table_name = 'users'
    
    @staticmethod
    def create(data):
        payload = {
            'username': data.get('username'),
            'email': data.get('email'),
            'password_hash': generate_password_hash(data.get('password')),
            'phone': data.get('phone'),
            'full_name': data.get('full_name'),
            'address': data.get('address'),
            'city': data.get('city'),
            'postal_code': data.get('postal_code'),
            'province': data.get('province'),
            'is_admin': data.get('is_admin', False),
            'is_verified': data.get('is_verified', False),
            'email_verified': data.get('email_verified', False),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        response = db.table(User.table_name).insert(payload).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(user_id):
        response = db.table(User.table_name).select("*").eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_email(email):
        response = db.table(User.table_name).select("*").eq('email', email).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_username(username):
        response = db.table(User.table_name).select("*").eq('username', username).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_all():
        response = db.table(User.table_name).select("*").execute()
        return response.data if response.data else []
    
    @staticmethod
    def update(user_id, data):
        payload = {}
        allowed_fields = ['username', 'email', 'phone', 'full_name', 'address', 'city', 'postal_code', 'province', 'is_admin', 'is_verified', 'email_verified']
        for field in allowed_fields:
            if field in data:
                payload[field] = data[field]
        
        if 'password' in data:
            payload['password_hash'] = generate_password_hash(data['password'])
        
        payload['updated_at'] = datetime.utcnow().isoformat()
        
        response = db.table(User.table_name).update(payload).eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(user_id):
        response = db.table(User.table_name).delete().eq('id', user_id).execute()
        return response.data
    
    @staticmethod
    def check_password(user, password):
        if not user or 'password_hash' not in user:
            return False
        return check_password_hash(user['password_hash'], password)
