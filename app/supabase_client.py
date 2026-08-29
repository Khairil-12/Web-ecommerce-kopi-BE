import os
from supabase import create_client, Client
from datetime import datetime

class SupabaseDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = None
        return cls._instance
    
    def __init__(self):
        pass
    
    def _ensure_client(self):
        if self.client is None:
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
            self.client: Client = create_client(url, key)
    
    def get_client(self) -> Client:
        self._ensure_client()
        return self.client
    
    def table(self, table_name: str):
        self._ensure_client()
        return self.client.table(table_name)

db = SupabaseDB()

class QueryHelper:
    @staticmethod
    def dict_to_payload(data: dict) -> dict:
        payload = {}
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                payload[key] = value.isoformat()
            else:
                payload[key] = value
        return payload
    
    @staticmethod
    def handle_response(response):
        if response.data:
            return response.data
        return None
    
    @staticmethod
    async def execute_query(query):
        try:
            response = query.execute()
            return QueryHelper.handle_response(response)
        except Exception as e:
            raise Exception(f"Query error: {str(e)}")
