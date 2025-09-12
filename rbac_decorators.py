"""
BigBossizzz RBAC Decorators
Advanced permission-based decorators for route protection and access control
"""

from functools import wraps
from flask import flash, redirect, url_for, request, jsonify, abort
from flask_login import current_user
import logging

def require_permission(permission_name, redirect_url=None, api_mode=False):
    """
    Decorator to require a specific permission for accessing a route
    
    Args:
        permission_name (str): The permission name to check
        redirect_url (str, optional): URL to redirect to if permission denied
        api_mode (bool): If True, returns JSON error instead of redirect
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            
            if not current_user.has_permission(permission_name):
                # Log unauthorized access attempt
                logging.warning(f"User {current_user.username} attempted to access {request.endpoint} without permission: {permission_name}")
                
                if api_mode:
                    return jsonify({
                        'error': 'Permission denied',
                        'required_permission': permission_name
                    }), 403
                
                flash(f'Access denied. You need the "{permission_name}" permission to access this resource.', 'error')
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    # Redirect based on user role
                    if current_user.is_admin():
                        return redirect(url_for('admin_dashboard'))
                    elif current_user.is_host():
                        return redirect(url_for('host_dashboard'))
                    else:
                        return redirect(url_for('participant_dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_any_permission(permission_names, redirect_url=None, api_mode=False):
    """
    Decorator to require any of the specified permissions for accessing a route
    
    Args:
        permission_names (list): List of permission names to check
        redirect_url (str, optional): URL to redirect to if permission denied
        api_mode (bool): If True, returns JSON error instead of redirect
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            
            if not current_user.has_any_permission(permission_names):
                logging.warning(f"User {current_user.username} attempted to access {request.endpoint} without any of permissions: {permission_names}")
                
                if api_mode:
                    return jsonify({
                        'error': 'Permission denied',
                        'required_permissions': permission_names
                    }), 403
                
                flash(f'Access denied. You need one of these permissions: {", ".join(permission_names)}', 'error')
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_all_permissions(permission_names, redirect_url=None, api_mode=False):
    """
    Decorator to require all specified permissions for accessing a route
    
    Args:
        permission_names (list): List of permission names to check
        redirect_url (str, optional): URL to redirect to if permission denied
        api_mode (bool): If True, returns JSON error instead of redirect
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            
            if not current_user.has_all_permissions(permission_names):
                logging.warning(f"User {current_user.username} attempted to access {request.endpoint} without all permissions: {permission_names}")
                
                if api_mode:
                    return jsonify({
                        'error': 'Permission denied',
                        'required_permissions': permission_names
                    }), 403
                
                flash(f'Access denied. You need all of these permissions: {", ".join(permission_names)}', 'error')
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(role_name, redirect_url=None, api_mode=False):
    """
    Decorator to require a specific role for accessing a route
    
    Args:
        role_name (str): The role name to check
        redirect_url (str, optional): URL to redirect to if role not found
        api_mode (bool): If True, returns JSON error instead of redirect
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            
            if not current_user.has_role(role_name):
                logging.warning(f"User {current_user.username} attempted to access {request.endpoint} without role: {role_name}")
                
                if api_mode:
                    return jsonify({
                        'error': 'Role required',
                        'required_role': role_name
                    }), 403
                
                flash(f'Access denied. You need the "{role_name}" role to access this resource.', 'error')
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_any_role(role_names, redirect_url=None, api_mode=False):
    """
    Decorator to require any of the specified roles for accessing a route
    
    Args:
        role_names (list): List of role names to check
        redirect_url (str, optional): URL to redirect to if no role found
        api_mode (bool): If True, returns JSON error instead of redirect
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('login'))
            
            user_roles = current_user.get_roles()
            if not any(role in user_roles for role in role_names):
                logging.warning(f"User {current_user.username} attempted to access {request.endpoint} without any of roles: {role_names}")
                
                if api_mode:
                    return jsonify({
                        'error': 'Role required',
                        'required_roles': role_names
                    }), 403
                
                flash(f'Access denied. You need one of these roles: {", ".join(role_names)}', 'error')
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(redirect_url=None, api_mode=False):
    """
    Convenience decorator for admin-only routes
    """
    return require_role('admin', redirect_url, api_mode)

def host_required(redirect_url=None, api_mode=False):
    """
    Convenience decorator for host-only routes
    """
    return require_role('host', redirect_url, api_mode)

def host_or_admin_required(redirect_url=None, api_mode=False):
    """
    Convenience decorator for host or admin routes
    """
    return require_any_role(['host', 'admin'], redirect_url, api_mode)

# Permission checking functions (not decorators)
def check_permission(user, permission_name):
    """Check if a user has a specific permission"""
    if not user or not user.is_authenticated:
        return False
    return user.has_permission(permission_name)

def check_any_permission(user, permission_names):
    """Check if a user has any of the specified permissions"""
    if not user or not user.is_authenticated:
        return False
    return user.has_any_permission(permission_names)

def check_all_permissions(user, permission_names):
    """Check if a user has all specified permissions"""
    if not user or not user.is_authenticated:
        return False
    return user.has_all_permissions(permission_names)

def get_user_permissions(user):
    """Get all permissions for a user"""
    if not user or not user.is_authenticated:
        return []
    return user.get_all_permissions()

def get_user_roles(user):
    """Get all roles for a user"""
    if not user or not user.is_authenticated:
        return []
    return user.get_roles()

# Context processor for templates
def permission_context_processor():
    """Add permission checking functions to template context"""
    return {
        'check_permission': lambda perm: check_permission(current_user, perm),
        'check_any_permission': lambda perms: check_any_permission(current_user, perms),
        'check_all_permissions': lambda perms: check_all_permissions(current_user, perms),
        'user_permissions': get_user_permissions(current_user) if current_user.is_authenticated else [],
        'user_roles': get_user_roles(current_user) if current_user.is_authenticated else []
    }