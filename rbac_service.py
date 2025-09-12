"""
BigBossizzz RBAC Service
Enterprise role and permission management service with comprehensive utilities
"""

from flask import current_app, request
from app import db
from models import User, Role, Permission, UserRole, RolePermission, RoleAuditLog
from datetime import datetime
import json
import logging

class RBACService:
    """
    Comprehensive RBAC management service providing all role and permission operations
    """
    
    @staticmethod
    def initialize_default_permissions():
        """Initialize default permissions for the system"""
        default_permissions = [
            # System Management
            {'name': 'manage_system', 'display_name': 'Manage System', 'description': 'Full system administration access', 'category': 'system'},
            {'name': 'view_system_logs', 'display_name': 'View System Logs', 'description': 'Access to system logs and monitoring', 'category': 'system'},
            {'name': 'manage_integrations', 'display_name': 'Manage Integrations', 'description': 'Configure LTI and other integrations', 'category': 'system'},
            
            # User Management
            {'name': 'manage_users', 'display_name': 'Manage Users', 'description': 'Create, edit, and delete user accounts', 'category': 'user'},
            {'name': 'view_users', 'display_name': 'View Users', 'description': 'View user accounts and profiles', 'category': 'user'},
            {'name': 'assign_roles', 'display_name': 'Assign Roles', 'description': 'Assign and remove user roles', 'category': 'user'},
            {'name': 'reset_passwords', 'display_name': 'Reset Passwords', 'description': 'Reset user passwords', 'category': 'user'},
            
            # Role and Permission Management
            {'name': 'manage_roles', 'display_name': 'Manage Roles', 'description': 'Create, edit, and delete roles', 'category': 'rbac'},
            {'name': 'manage_permissions', 'display_name': 'Manage Permissions', 'description': 'Create, edit, and delete permissions', 'category': 'rbac'},
            {'name': 'view_role_assignments', 'display_name': 'View Role Assignments', 'description': 'View user role assignments', 'category': 'rbac'},
            {'name': 'audit_rbac_changes', 'display_name': 'Audit RBAC Changes', 'description': 'View role and permission change logs', 'category': 'rbac'},
            
            # Quiz Management
            {'name': 'create_quizzes', 'display_name': 'Create Quizzes', 'description': 'Create new quizzes and exams', 'category': 'quiz'},
            {'name': 'edit_quizzes', 'display_name': 'Edit Quizzes', 'description': 'Edit existing quizzes', 'category': 'quiz'},
            {'name': 'delete_quizzes', 'display_name': 'Delete Quizzes', 'description': 'Delete quizzes permanently', 'category': 'quiz'},
            {'name': 'manage_quiz_settings', 'display_name': 'Manage Quiz Settings', 'description': 'Configure quiz proctoring and advanced settings', 'category': 'quiz'},
            {'name': 'view_all_quizzes', 'display_name': 'View All Quizzes', 'description': 'Access to all quizzes in the system', 'category': 'quiz'},
            {'name': 'duplicate_quizzes', 'display_name': 'Duplicate Quizzes', 'description': 'Create copies of existing quizzes', 'category': 'quiz'},
            
            # Quiz Taking
            {'name': 'take_quizzes', 'display_name': 'Take Quizzes', 'description': 'Participate in quizzes and exams', 'category': 'quiz'},
            {'name': 'view_own_results', 'display_name': 'View Own Results', 'description': 'View personal quiz results', 'category': 'quiz'},
            {'name': 'retake_quizzes', 'display_name': 'Retake Quizzes', 'description': 'Retake quizzes when allowed', 'category': 'quiz'},
            
            # Proctoring
            {'name': 'manage_proctoring', 'display_name': 'Manage Proctoring', 'description': 'Configure proctoring settings', 'category': 'proctoring'},
            {'name': 'view_proctoring_events', 'display_name': 'View Proctoring Events', 'description': 'Monitor proctoring violations', 'category': 'proctoring'},
            {'name': 'review_violations', 'display_name': 'Review Violations', 'description': 'Review and resolve proctoring violations', 'category': 'proctoring'},
            
            # Reporting and Analytics
            {'name': 'view_reports', 'display_name': 'View Reports', 'description': 'Access quiz and user reports', 'category': 'reports'},
            {'name': 'generate_advanced_reports', 'display_name': 'Generate Advanced Reports', 'description': 'Create custom and advanced reports', 'category': 'reports'},
            {'name': 'export_data', 'display_name': 'Export Data', 'description': 'Export quiz data and reports', 'category': 'reports'},
            {'name': 'view_analytics', 'display_name': 'View Analytics', 'description': 'Access system analytics and insights', 'category': 'reports'},
            {'name': 'view_plagiarism_reports', 'display_name': 'View Plagiarism Reports', 'description': 'Access plagiarism detection results', 'category': 'reports'},
            
            # Communication
            {'name': 'send_notifications', 'display_name': 'Send Notifications', 'description': 'Send notifications to users', 'category': 'communication'},
            {'name': 'manage_announcements', 'display_name': 'Manage Announcements', 'description': 'Create and manage system announcements', 'category': 'communication'},
        ]
        
        created_count = 0
        for perm_data in default_permissions:
            try:
                if not Permission.query.filter_by(name=perm_data['name']).first():
                    permission = Permission()
                    permission.name = perm_data['name']
                    permission.display_name = perm_data['display_name']
                    permission.description = perm_data['description']
                    permission.category = perm_data['category']
                    permission.is_system_permission = True
                    db.session.add(permission)
                    created_count += 1
                    logging.info(f"Created permission: {perm_data['name']}")
            except Exception as e:
                logging.error(f"Failed to create permission {perm_data['name']}: {e}")
        
        if created_count > 0:
            try:
                db.session.commit()
                logging.info(f"Initialized {created_count} default permissions")
            except Exception as e:
                logging.error(f"Failed to commit permissions: {e}")
                db.session.rollback()
                created_count = 0
        
        return created_count
    
    @staticmethod
    def initialize_default_roles():
        """Initialize default roles with appropriate permissions"""
        default_roles = [
            {
                'name': 'admin',
                'display_name': 'System Administrator',
                'description': 'Full system access with all permissions',
                'permissions': [
                    'manage_system', 'view_system_logs', 'manage_integrations',
                    'manage_users', 'view_users', 'assign_roles', 'reset_passwords',
                    'manage_roles', 'manage_permissions', 'view_role_assignments', 'audit_rbac_changes',
                    'create_quizzes', 'edit_quizzes', 'delete_quizzes', 'manage_quiz_settings', 'view_all_quizzes', 'duplicate_quizzes',
                    'manage_proctoring', 'view_proctoring_events', 'review_violations',
                    'view_reports', 'generate_advanced_reports', 'export_data', 'view_analytics', 'view_plagiarism_reports',
                    'send_notifications', 'manage_announcements'
                ]
            },
            {
                'name': 'host',
                'display_name': 'Quiz Host/Instructor',
                'description': 'Can create and manage quizzes, view results',
                'permissions': [
                    'view_users',
                    'create_quizzes', 'edit_quizzes', 'manage_quiz_settings', 'duplicate_quizzes',
                    'view_proctoring_events', 'review_violations',
                    'view_reports', 'export_data', 'view_analytics', 'view_plagiarism_reports',
                    'send_notifications'
                ]
            },
            {
                'name': 'participant',
                'display_name': 'Quiz Participant/Student',
                'description': 'Can take quizzes and view own results',
                'permissions': [
                    'take_quizzes', 'view_own_results', 'retake_quizzes'
                ]
            },
            {
                'name': 'moderator',
                'display_name': 'Quiz Moderator',
                'description': 'Can assist with quiz management and monitoring',
                'permissions': [
                    'view_users',
                    'view_all_quizzes', 'manage_quiz_settings',
                    'view_proctoring_events', 'review_violations',
                    'view_reports', 'view_analytics'
                ]
            },
            {
                'name': 'analyst',
                'display_name': 'Data Analyst',
                'description': 'Can access reports and analytics',
                'permissions': [
                    'view_reports', 'generate_advanced_reports', 'export_data', 'view_analytics', 'view_plagiarism_reports'
                ]
            }
        ]
        
        created_count = 0
        for role_data in default_roles:
            existing_role = Role.query.filter_by(name=role_data['name']).first()
            if not existing_role:
                role = Role()
                role.name = role_data['name']
                role.display_name = role_data['display_name']
                role.description = role_data['description']
                role.is_system_role = True
                db.session.add(role)
                db.session.flush()  # Get the role ID
                
                # Add permissions to role
                for perm_name in role_data['permissions']:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role_permission = RolePermission()
                        role_permission.role_id = role.id
                        role_permission.permission_id = permission.id
                        db.session.add(role_permission)
                
                created_count += 1
        
        if created_count > 0:
            db.session.commit()
            logging.info(f"Initialized {created_count} default roles")
        
        return created_count
    
    @staticmethod
    def create_role(name, display_name, description, permission_names=None, created_by_user_id=None):
        """Create a new role with optional permissions"""
        if Role.query.filter_by(name=name).first():
            raise ValueError(f"Role '{name}' already exists")
        
        role = Role()
        role.name = name
        role.display_name = display_name
        role.description = description
        role.created_by = created_by_user_id
        db.session.add(role)
        db.session.flush()
        
        # Add permissions if provided
        if permission_names:
            for perm_name in permission_names:
                permission = Permission.query.filter_by(name=perm_name).first()
                if permission:
                    role_permission = RolePermission()
                    role_permission.role_id = role.id
                    role_permission.permission_id = permission.id
                    role_permission.granted_by = created_by_user_id
                    db.session.add(role_permission)
        
        # Create audit log
        RBACService._create_audit_log(
            action='create',
            entity_type='role',
            entity_id=role.id,
            performed_by=created_by_user_id,
            new_values=json.dumps({
                'name': name,
                'display_name': display_name,
                'description': description,
                'permissions': permission_names or []
            })
        )
        
        db.session.commit()
        return role
    
    @staticmethod
    def update_role(role_id, **kwargs):
        """Update an existing role"""
        role = Role.query.get_or_404(role_id)
        
        if role.is_system_role and 'name' in kwargs:
            raise ValueError("Cannot modify name of system role")
        
        old_values = {
            'name': role.name,
            'display_name': role.display_name,
            'description': role.description
        }
        
        # Update role fields
        for key, value in kwargs.items():
            if hasattr(role, key) and key not in ['id', 'created_at', 'is_system_role']:
                setattr(role, key, value)
        
        role.updated_at = datetime.utcnow()
        
        # Create audit log
        RBACService._create_audit_log(
            action='update',
            entity_type='role',
            entity_id=role.id,
            performed_by=kwargs.get('updated_by'),
            old_values=json.dumps(old_values),
            new_values=json.dumps(kwargs)
        )
        
        db.session.commit()
        return role
    
    @staticmethod
    def delete_role(role_id, performed_by_user_id=None):
        """Delete a role (if not system role)"""
        role = Role.query.get_or_404(role_id)
        
        if role.is_system_role:
            raise ValueError("Cannot delete system role")
        
        old_values = {
            'name': role.name,
            'display_name': role.display_name,
            'description': role.description,
            'user_count': role.user_count,
            'permission_count': role.permission_count
        }
        
        # Create audit log before deletion
        RBACService._create_audit_log(
            action='delete',
            entity_type='role',
            entity_id=role.id,
            performed_by=performed_by_user_id,
            old_values=json.dumps(old_values)
        )
        
        db.session.delete(role)
        db.session.commit()
        return True
    
    @staticmethod
    def assign_role_to_user(user_id, role_name, assigned_by_user_id=None, expires_at=None):
        """Assign a role to a user"""
        user = User.query.get_or_404(user_id)
        role = Role.query.filter_by(name=role_name).first()
        
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        # Check if already assigned
        existing = UserRole.query.filter_by(user_id=user_id, role_id=role.id).first()
        if existing:
            if existing.is_active:
                raise ValueError(f"User already has role '{role_name}'")
            else:
                # Reactivate existing assignment
                existing.is_active = True
                existing.expires_at = expires_at
                user_role = existing
        else:
            user_role = UserRole()
            user_role.user_id = user_id
            user_role.role_id = role.id
            user_role.assigned_by = assigned_by_user_id
            user_role.expires_at = expires_at
            db.session.add(user_role)
        
        # Create audit log
        RBACService._create_audit_log(
            action='assign',
            entity_type='user_role',
            entity_id=user_role.id,
            target_user_id=user_id,
            performed_by=assigned_by_user_id,
            new_values=json.dumps({
                'user_id': user_id,
                'role_name': role_name,
                'expires_at': expires_at.isoformat() if expires_at else None
            })
        )
        
        db.session.commit()
        return user_role
    
    @staticmethod
    def revoke_role_from_user(user_id, role_name, revoked_by_user_id=None):
        """Revoke a role from a user"""
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        user_role = UserRole.query.filter_by(user_id=user_id, role_id=role.id, is_active=True).first()
        if not user_role:
            raise ValueError(f"User does not have active role '{role_name}'")
        
        # Create audit log before revocation
        RBACService._create_audit_log(
            action='revoke',
            entity_type='user_role',
            entity_id=user_role.id,
            target_user_id=user_id,
            performed_by=revoked_by_user_id,
            old_values=json.dumps({
                'user_id': user_id,
                'role_name': role_name,
                'assigned_at': user_role.assigned_at.isoformat()
            })
        )
        
        db.session.delete(user_role)
        db.session.commit()
        return True
    
    @staticmethod
    def get_user_permissions(user_id):
        """Get all permissions for a user through their roles"""
        user = User.query.get_or_404(user_id)
        return user.get_all_permissions()
    
    @staticmethod
    def get_role_users(role_name):
        """Get all users with a specific role"""
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return []
        
        user_roles = UserRole.query.filter_by(role_id=role.id, is_active=True).all()
        return [ur.user for ur in user_roles]
    
    @staticmethod
    def bulk_assign_roles(user_ids, role_names, assigned_by_user_id=None):
        """Assign multiple roles to multiple users"""
        results = []
        for user_id in user_ids:
            for role_name in role_names:
                try:
                    user_role = RBACService.assign_role_to_user(
                        user_id, role_name, assigned_by_user_id
                    )
                    results.append({'success': True, 'user_id': user_id, 'role': role_name})
                except Exception as e:
                    results.append({'success': False, 'user_id': user_id, 'role': role_name, 'error': str(e)})
        
        return results
    
    @staticmethod
    def get_audit_logs(entity_type=None, entity_id=None, user_id=None, limit=100):
        """Get audit logs with optional filtering"""
        query = RoleAuditLog.query
        
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        if entity_id:
            query = query.filter_by(entity_id=entity_id)
        if user_id:
            query = query.filter_by(target_user_id=user_id)
        
        return query.order_by(RoleAuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def cleanup_expired_roles():
        """Remove expired role assignments"""
        expired_roles = UserRole.query.filter(
            UserRole.expires_at.isnot(None),
            UserRole.expires_at < datetime.utcnow(),
            UserRole.is_active == True
        ).all()
        
        count = 0
        for user_role in expired_roles:
            # Create audit log for automatic expiration
            RBACService._create_audit_log(
                action='expire',
                entity_type='user_role',
                entity_id=user_role.id,
                target_user_id=user_role.user_id,
                performed_by=None,  # System action
                old_values=json.dumps({
                    'user_id': user_role.user_id,
                    'role_id': user_role.role_id,
                    'expires_at': user_role.expires_at.isoformat()
                })
            )
            
            user_role.is_active = False
            count += 1
        
        if count > 0:
            db.session.commit()
            logging.info(f"Deactivated {count} expired role assignments")
        
        return count
    
    @staticmethod
    def _create_audit_log(action, entity_type, entity_id, performed_by=None, 
                         target_user_id=None, old_values=None, new_values=None, reason=None):
        """Create an audit log entry"""
        audit_log = RoleAuditLog()
        audit_log.action = action
        audit_log.entity_type = entity_type
        audit_log.entity_id = entity_id
        audit_log.target_user_id = target_user_id
        audit_log.performed_by = performed_by
        audit_log.old_values = old_values
        audit_log.new_values = new_values
        audit_log.reason = reason
        audit_log.ip_address = request.remote_addr if request else None
        audit_log.user_agent = request.headers.get('User-Agent') if request else None
        db.session.add(audit_log)
        return audit_log

def initialize_rbac_system():
    """Initialize the entire RBAC system with default data"""
    logging.info("Initializing RBAC system...")
    
    # Initialize permissions first
    perm_count = RBACService.initialize_default_permissions()
    
    # Then initialize roles with permissions
    role_count = RBACService.initialize_default_roles()
    
    logging.info(f"RBAC initialization complete: {perm_count} permissions, {role_count} roles created")
    
    return {'permissions_created': perm_count, 'roles_created': role_count}