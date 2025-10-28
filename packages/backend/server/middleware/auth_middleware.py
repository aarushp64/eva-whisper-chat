from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def auth_required():
    """
    Decorator to protect routes that require authentication
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                # Verify JWT token
                verify_jwt_in_request()
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({"message": "Unauthorized access"}), 401
        return decorator
    return wrapper
