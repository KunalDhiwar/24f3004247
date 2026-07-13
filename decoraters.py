from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(func):
      @wraps(func)
      def wrapper(*args, **kwargs):
            if "user_id" not in session:
                  flash("Please login first", "Warnig")
                  return redirect(url_for("login"))
            return func(*args, **kwargs)
      return wrapper

def role_required(*allowed_roles):
      def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                  if "user_id" not in session:
                        flash("Please login first", "Warning")
                        return redirect(url_for("login"))
                  
                  if session.get("roal") not in allowed_roles:
                        flash("Access denied", "Danger")
                        return redirect(url_for("login"))
                  
                  return func(*args, **kwargs)
            return wrapper
      return decorator
