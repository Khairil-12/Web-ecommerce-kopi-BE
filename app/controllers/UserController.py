from app.models.user import User
from app import response, db
from flask import request
import json

def index():
    try:
        users = User.query.all()
        data = transform(users)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def show(id):
    try:
        user = User.query.filter_by(id=id).first()
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
        if User.query.filter_by(email=email).first():
            return response.bad_request([], "Email already registered")
        if User.query.filter_by(username=username).first():
            return response.bad_request([], "Username already taken")
        user = User(
            username=username,
            email=email,
            phone=phone,
            address=address
        )
        user.set_password(password)
        user.is_admin = is_admin 
        db.session.add(user)
        db.session.commit()
        return response.created([], "User created successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def update(id):
    try:
        user = User.query.filter_by(id=id).first()
        if not user:
            return response.not_found([], "User not found")
        user.username = request.json.get('username', user.username)
        user.email = request.json.get('email', user.email)
        user.phone = request.json.get('phone', user.phone)
        user.address = request.json.get('address', user.address)
        if 'password' in request.json:
            user.set_password(request.json['password'])
        db.session.commit()
        return response.ok([], "User updated successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def delete(id):
    try:
        user = User.query.filter_by(id=id).first()
        if not user:
            return response.not_found([], "User not found")
        db.session.delete(user)
        db.session.commit()
        return response.ok([], "User deleted successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def transform(users):
    array = []
    for user in users:
        array.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'address': user.address, 
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    return array

def single_transform(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'address': user.address,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None
    }