from app.models.transaction import Transaction, TransactionItem
from app.models.product import Product
from app.models.user import User
from app.models.stock import Stock
from app import response, db
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
        transactions = Transaction.query.all()
        data = transform(transactions)
        return response.ok(data, "")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def show(id):
    try:
        transaction = Transaction.query.filter_by(id=id).first()
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
        
        # Validate user exists
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return response.not_found([], "User not found")
        
        if not items:
            return response.bad_request([], "No items in transaction")
        
        # Calculate total amount and check stock
        total_amount = 0
        transaction_items = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            # Get product
            product = Product.query.filter_by(id=product_id).first()
            if not product:
                return response.not_found([], f"Product {product_id} not found")
            
            # Check stock
            stock = Stock.query.filter_by(product_id=product_id).first()
            if not stock or stock.quantity < quantity:
                return response.bad_request([], f"Insufficient stock for product {product.name}")
            
            # Calculate subtotal
            price = float(product.price) if product.price else 0
            subtotal = price * quantity
            total_amount += subtotal
            
            # Prepare transaction item
            transaction_item = TransactionItem(
                product_id=product_id,
                quantity=quantity,
                price=price,
                subtotal=subtotal
            )
            transaction_items.append(transaction_item)
        
        # Create transaction
        transaction = Transaction(
            transaction_code=generate_transaction_code(),
            user_id=user_id,
            total_amount=total_amount,
            status='pending',
            payment_method=payment_method,
            shipping_address=shipping_address,
            notes=notes
        )
        
        db.session.add(transaction)
        db.session.flush()  # Get transaction ID
        
        # Add items to transaction
        for item in transaction_items:
            item.transaction_id = transaction.id
            db.session.add(item)
            
            # Reduce stock
            stock = Stock.query.filter_by(product_id=item.product_id).first()
            stock.quantity -= item.quantity
        
        db.session.commit()
        
        return response.created(single_transform(transaction), "Transaction created successfully")
        
    except Exception as e:
        db.session.rollback()
        print(e)
        return response.server_error([], f"Error: {e}")

def update_status(id):
    try:
        transaction = Transaction.query.filter_by(id=id).first()
        if not transaction:
            return response.not_found([], "Transaction not found")
        
        new_status = request.json.get('status')
        valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'completed', 'cancelled']
        
        if new_status not in valid_statuses:
            return response.bad_request([], f"Invalid status. Valid: {', '.join(valid_statuses)}")
        
        transaction.status = new_status
        db.session.commit()
        
        return response.ok([], f"Transaction status updated to {new_status}")
        
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def user_transactions(user_id):
    try:
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        data = transform(transactions)
        return response.ok(data, f"Transactions for user {user_id}")
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def delete(id):
    try:
        transaction = Transaction.query.filter_by(id=id).first()
        if not transaction:
            return response.not_found([], "Transaction not found")
        
        # Restore stock if transaction is cancelled
        if transaction.status != 'cancelled':
            # Restore stock for each item
            for item in transaction.items:
                stock = Stock.query.filter_by(product_id=item.product_id).first()
                if stock:
                    stock.quantity += item.quantity
        
        db.session.delete(transaction)
        db.session.commit()
        
        return response.ok([], "Transaction deleted successfully")
        
    except Exception as e:
        print(e)
        return response.server_error([], f"Error: {e}")

def transform(transactions):
    array = []
    for transaction in transactions:
        array.append({
            'id': transaction.id,
            'transaction_code': transaction.transaction_code,
            'user_id': transaction.user_id,
            'username': transaction.user.username if transaction.user else 'Unknown',
            'total_amount': float(transaction.total_amount) if transaction.total_amount else 0,
            'status': transaction.status,
            'payment_method': transaction.payment_method,
            'item_count': len(transaction.items),
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None
        })
    return array

def single_transform(transaction):
    items = []
    for item in transaction.items:
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else 'Unknown',
            'quantity': item.quantity,
            'price': float(item.price) if item.price else 0,
            'subtotal': float(item.subtotal) if item.subtotal else 0
        })
    
    return {
        'id': transaction.id,
        'transaction_code': transaction.transaction_code,
        'user_id': transaction.user_id,
        'username': transaction.user.username if transaction.user else 'Unknown',
        'total_amount': float(transaction.total_amount) if transaction.total_amount else 0,
        'status': transaction.status,
        'payment_method': transaction.payment_method,
        'shipping_address': transaction.shipping_address,
        'notes': transaction.notes,
        'items': items,
        'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
        'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None
    }