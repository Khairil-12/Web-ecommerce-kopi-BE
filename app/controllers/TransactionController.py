from app.models.transaction import Transaction, TransactionItem
from app.models.product import Product
from app.models.user import User
from app.models.stock import Stock
from app import response
from flask import request
from datetime import datetime
import random
import string

def generate_transaction_code():
    """Generate unique transaction code"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TRX-{date_str}-{random_str}"

def index():
    try:
        transactions = Transaction.get_all()
        data = transform(transactions)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def show(id):
    try:
        transaction = Transaction.get_by_id(id)
        if not transaction:
            return response.not_found([], "Transaction not found")
        data = single_transform(transaction)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def store():
    try:
        user_id = request.json.get('user_id')
        items = request.json.get('items', [])
        payment_method = request.json.get('payment_method')
        shipping_address = request.json.get('shipping_address')
        notes = request.json.get('notes', '')
        user = User.get_by_id(user_id)
        if not user:
            return response.not_found([], "User not found")
        if not items:
            return response.bad_request([], "No items in transaction")
        total_amount = 0
        order_items = []
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            product = Product.get_by_id(product_id)
            if not product:
                return response.not_found([], f"Product {product_id} not found")
            stock = Stock.get_by_product_id(product_id)
            if not stock or stock.get('quantity', 0) < quantity:
                return response.bad_request([], f"Insufficient stock for product {product.get('name')}")
            price = float(product.get('price') or 0)
            subtotal = price * quantity
            total_amount += subtotal
            order_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal
            })
        transaction = Transaction.create({
            'transaction_code': generate_transaction_code(),
            'user_id': user_id,
            'total_amount': total_amount,
            'status': 'pending',
            'payment_method': payment_method,
            'shipping_address': shipping_address,
            'notes': notes
        })
        if not transaction:
            return response.server_error([], "Failed to create transaction")
        for oi in order_items:
            TransactionItem.create({
                'transaction_id': transaction['id'],
                'product_id': oi['product_id'],
                'quantity': oi['quantity'],
                'price': oi['price'],
                'subtotal': oi['subtotal']
            })
            stock = Stock.get_by_product_id(oi['product_id'])
            if stock:
                Stock.update(stock['id'], {'quantity': stock['quantity'] - oi['quantity']})
        return response.created(single_transform(transaction), "Transaction created successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def update_status(id):
    try:
        transaction = Transaction.get_by_id(id)
        if not transaction:
            return response.not_found([], "Transaction not found")
        new_status = request.json.get('status')
        valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return response.bad_request([], f"Invalid status. Valid: {', '.join(valid_statuses)}")
        Transaction.update(id, {'status': new_status})
        return response.ok([], f"Transaction status updated to {new_status}")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def user_transactions(user_id):
    try:
        transactions = Transaction.get_by_user_id(user_id)
        data = transform(transactions)
        return response.ok(data, f"Transactions for user {user_id}")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def delete(id):
    try:
        transaction = Transaction.get_by_id(id)
        if not transaction:
            return response.not_found([], "Transaction not found")
        if transaction.get('status') != 'cancelled':
            for item in TransactionItem.get_by_transaction_id(id):
                stock = Stock.get_by_product_id(item.get('product_id'))
                if stock:
                    Stock.update(stock['id'], {'quantity': stock['quantity'] + item.get('quantity')})
        Transaction.delete(id)
        return response.ok([], "Transaction deleted successfully")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def transform(transactions):
    users = {u['id']: u for u in User.get_all()}
    array = []
    for transaction in transactions:
        user = users.get(transaction.get('user_id'))
        items = TransactionItem.get_by_transaction_id(transaction.get('id'))
        array.append({
            'id': transaction.get('id'),
            'transaction_code': transaction.get('transaction_code'),
            'user_id': transaction.get('user_id'),
            'username': user.get('username') if user else 'Unknown',
            'total_amount': float(transaction.get('total_amount') or 0),
            'status': transaction.get('status'),
            'payment_method': transaction.get('payment_method'),
            'item_count': len(items),
            'created_at': transaction.get('created_at')
        })
    return array

def single_transform(transaction):
    items = []
    for item in TransactionItem.get_by_transaction_id(transaction.get('id')):
        prod = Product.get_by_id(item.get('product_id'))
        items.append({
            'id': item.get('id'),
            'product_id': item.get('product_id'),
            'product_name': prod.get('name') if prod else 'Unknown',
            'quantity': item.get('quantity'),
            'price': float(item.get('price') or 0),
            'subtotal': float(item.get('subtotal') or 0)
        })
    return {
        'id': transaction.get('id'),
        'transaction_code': transaction.get('transaction_code'),
        'user_id': transaction.get('user_id'),
        'username': transaction.get('username'),
        'total_amount': float(transaction.get('total_amount') or 0),
        'status': transaction.get('status'),
        'payment_method': transaction.get('payment_method'),
        'shipping_address': transaction.get('shipping_address'),
        'notes': transaction.get('notes'),
        'items': items,
        'created_at': transaction.get('created_at'),
        'updated_at': transaction.get('updated_at')
    }