from flask import jsonify, make_response
def ok(values, message):
    res = {
        'data': values,
        'message': message,
        'status': 'success'
    }
    return make_response(jsonify(res)), 200

def created(values, message):
    res = {
        'data': values,
        'message': message,
        'status': 'success'
    }
    return make_response(jsonify(res)), 201

def bad_request(values, message):
    res = {
        'data': values,
        'message': message,
        'status': 'error'
    }
    return make_response(jsonify(res)), 400

def not_found(values, message):
    res = {
        'data': values,
        'message': message,
        'status': 'error'
    }
    return make_response(jsonify(res)), 404

def server_error(values, message):
    res = {
        'data': values,
        'message': message,
        'status': 'error'
    }
    return make_response(jsonify(res)), 500