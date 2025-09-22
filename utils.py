from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(403)  # user not logged in
            if current_user.role not in roles:
                return abort(403)  # logged in but wrong role
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper
