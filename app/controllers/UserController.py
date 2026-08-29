from app.models.user import User
from app import response
from flask import request
import json

def index():
    try:
        users = User.get_all()
        data = transform(users)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def show(id):
    try:
        user = User.get_by_id(id)
        if not user:
            return response.not_found([], "User not found")
        data = single_transform(user)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def store():
    try:
        username = request.json.get('username')
        email = request.json.get('email')
        password = request.json.get('password')
        phone = request.json.get('phone', '')
        address = request.json.get('address', '')
        is_admin = request.json.get('is_admin', False)
        
        if User.get_by_email(email):
            return response.bad_request([], "Email already registered")
        if User.get_by_username(username):
            return response.bad_request([], "Username already taken")
        
        user_data = {
            'username': username,
            'email': email,
            'password': password,
            'phone': phone,
            'address': address,
            'is_admin': is_admin,
            'full_name': request.json.get('full_name'),
            'city': request.json.get('city'),
            'postal_code': request.json.get('postal_code'),
            'province': request.json.get('province')
        }
        
        User.create(user_data)
        return response.created([], "User created successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def update(id):
    try:
        user = User.get_by_id(id)
        if not user:
            return response.not_found([], "User not found")
        
        update_data = {}
        if 'username' in request.json:
            update_data['username'] = request.json['username']
        if 'email' in request.json:
            update_data['email'] = request.json['email']
        if 'phone' in request.json:
            update_data['phone'] = request.json['phone']
        if 'address' in request.json:
            update_data['address'] = request.json['address']
        if 'password' in request.json:
            update_data['password'] = request.json['password']
        if 'full_name' in request.json:
            update_data['full_name'] = request.json['full_name']
        if 'city' in request.json:
            update_data['city'] = request.json['city']
        if 'postal_code' in request.json:
            update_data['postal_code'] = request.json['postal_code']
        if 'province' in request.json:
            update_data['province'] = request.json['province']
        
        User.update(id, update_data)
        return response.ok([], "User updated successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def delete(id):
    try:
        user = User.get_by_id(id)
        if not user:
            return response.not_found([], "User not found")
        User.delete(id)
        return response.ok([], "User deleted successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def transform(users):
    array = []
    for user in users:
        array.append({
            'id': user.get('id'),
            'username': user.get('username'),
            'email': user.get('email'),
            'phone': user.get('phone'),
            'address': user.get('address'),
            'is_admin': user.get('is_admin'),
            'created_at': user.get('created_at')
        })
    return array

def single_transform(user):
    return {
        'id': user.get('id'),
        'username': user.get('username'),
        'email': user.get('email'),
        'phone': user.get('phone'),
        'address': user.get('address'),
        'is_admin': user.get('is_admin'),
        'created_at': user.get('created_at'),
        'updated_at': user.get('updated_at')
    }
