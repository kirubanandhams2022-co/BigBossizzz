"""
Academic Email Service - Completely FREE using Brevo API
Replaces the broken Flask-Mail system with reliable Brevo service
300 emails/day forever free - perfect for academic institutions
"""

import os
import requests
import logging
from typing import Optional
from flask import url_for
from datetime import datetime

class BrevoEmailService:
    """
    Completely free email service using Brevo API
    - 300 emails/day forever free
    - Perfect for academic institutions
    - Professional email templates
    """
    
    def __init__(self):
        self.api_key = os.environ.get('BREVO_API_KEY', '')
        self.sender_email = os.environ.get('BREVO_SENDER_EMAIL', '')
        self.sender_name = os.environ.get('BREVO_SENDER_NAME', 'BigBossizzz Academic Platform')
        self.api_url = 'https://api.brevo.com/v3/smtp/email'
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'api-key': self.api_key
        }
        
        # Validate critical configuration with development flexibility
        if not self.api_key:
            raise ValueError("❌ CRITICAL: BREVO_API_KEY not set. Email system cannot function!")
        
        # Handle sender email - strict for production, fallback for development  
        if not self.sender_email:
            is_production = os.environ.get('FLASK_ENV') == 'production'
            if is_production:
                logging.error("❌ PRODUCTION: BREVO_SENDER_EMAIL required! Please configure verified domain.")
                self.sender_email = "noreply@bigbossizzz.com"  # Will likely bounce in production
            else:
                logging.warning("⚠️ DEVELOPMENT: Using fallback sender. Set BREVO_SENDER_EMAIL for production!")
                self.sender_email = "noreply@bigbossizzz.com"  # Development fallback
    
    def send_email(self, 
                   to_email: str, 
                   subject: str, 
                   html_content: Optional[str] = None,
                   text_content: Optional[str] = None,
                   from_email: Optional[str] = None,
                   from_name: str = "BigBossizzz Academic Platform") -> bool:
        """Send email using Brevo's free API"""
        
        if not self.api_key:
            logging.error("Cannot send email: BREVO_API_KEY not configured")
            return False
        
        # Use configured sender or fail with clear error
        if not from_email:
            if self.sender_email:
                from_email = self.sender_email
            else:
                logging.error("❌ No sender email configured. Set BREVO_SENDER_EMAIL environment variable.")
                return False
        
        # Use configured sender name
        if not from_name or from_name == "BigBossizzz Academic Platform":
            from_name = self.sender_name
        
        # Prepare email data
        email_data = {
            "sender": {
                "name": from_name,
                "email": from_email
            },
            "to": [{"email": to_email}],
            "subject": subject
        }
        
        # Add content (prefer HTML over text)
        if html_content:
            email_data["htmlContent"] = html_content
        elif text_content:
            email_data["textContent"] = text_content
        else:
            logging.error("No email content provided")
            return False
        
        try:
            response = requests.post(
                self.api_url,
                json=email_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 201:
                logging.info(f"✅ Email sent successfully to {to_email}")
                return True
            else:
                logging.error(f"❌ Failed to send email: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Email service error: {e}")
            return False

# Global email service instance
brevo_service = BrevoEmailService()

def send_verification_email(user):
    """Send email verification to user - Compatible with existing registration flow"""
    try:
        # Use existing verification token (already generated and committed in register)
        token = user.verification_token
        if not token:
            logging.error("❌ No verification token found for user")
            return False
        verification_url = url_for('verify_email', token=token, _external=True)
        
        subject = '🎓 Verify Your BigBossizzz Academic Account'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .eye-logo {{ font-size: 48px; margin-bottom: 10px; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                .verification-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 12px; }}
                .url-box {{ background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; word-break: break-all; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="eye-logo">👁️</div>
                    <h1>BigBossizzz</h1>
                    <p>Academic Examination Platform</p>
                </div>
                <div class="content">
                    <h2>Welcome {user.username}!</h2>
                    <p>Thank you for joining BigBossizzz as a <strong>{user.role.title()}</strong>.</p>
                    
                    <div class="verification-box">
                        <h3>📧 Verify Your Academic Email</h3>
                        <p>To complete your registration and access academic features, please verify your email address.</p>
                        
                        <div style="text-align: center; margin: 25px 0;">
                            <a href="{verification_url}" class="button">✅ Verify Email Address</a>
                        </div>
                    </div>
                    
                    <p><strong>Can't click the button?</strong> Copy and paste this link:</p>
                    <div class="url-box">{verification_url}</div>
                    
                    <p>⏰ <strong>Important:</strong> This verification link expires in 24 hours for security.</p>
                    
                    <h3>📚 What's Next After Verification:</h3>
                    <ul>
                        <li>Access to academic dashboard</li>
                        <li>Join or create quiz sessions</li>
                        <li>Proctored examination system</li>
                        <li>Real-time academic monitoring</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>© 2025 BigBossizzz Academic Platform</p>
                    <p>This is an automated academic verification email.</p>
                    <p>If you didn't create this account, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send using Brevo
        return brevo_service.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            from_name="BigBossizzz Academic Team"
        )
        
    except Exception as e:
        logging.error(f"❌ Failed to send verification email to {user.email}: {str(e)}")
        return False

def send_credentials_email(user, temp_password):
    """Send login credentials to verified user"""
    try:
        subject = '🔑 Your BigBossizzz Academic Login Credentials'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .credentials {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #28a745; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>👁️ BigBossizzz</h1>
                    <p>Your Academic Account is Ready!</p>
                </div>
                <div class="content">
                    <h2>🎓 Hello {user.username}!</h2>
                    <p>Your academic account has been verified successfully. You can now access the BigBossizzz examination platform.</p>
                    
                    <div class="credentials">
                        <h3>🔐 Your Login Credentials:</h3>
                        <table style="width: 100%; font-family: monospace;">
                            <tr><td><strong>Username:</strong></td><td>{user.username}</td></tr>
                            <tr><td><strong>Email:</strong></td><td>{user.email}</td></tr>
                            <tr><td><strong>Password:</strong></td><td>{temp_password}</td></tr>
                            <tr><td><strong>Role:</strong></td><td>{user.role.title()}</td></tr>
                        </table>
                    </div>
                    
                    <div class="warning">
                        ⚠️ <strong>Security Notice:</strong> Please change your password after first login for account security.
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="{url_for('login', _external=True)}" class="button">🚀 Login to Platform</a>
                    </p>
                    
                    <h3>📚 Academic Features Available:</h3>
                    <ul>
                        <li>Secure proctored examinations</li>
                        <li>Real-time violation monitoring</li>
                        <li>Academic progress tracking</li>
                        <li>Course and quiz management</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        return brevo_service.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            from_name="BigBossizzz Academic Team"
        )
        
    except Exception as e:
        logging.error(f"❌ Failed to send credentials email: {str(e)}")
        return False

def send_login_notification(user, login_event=None):
    """Send login notification (compatible with routes.py)"""
    try:
        subject = f'🔔 Academic Login Alert - {user.username}'
        
        login_time = login_event.login_time if login_event else datetime.now()
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px;">
            <h3>👁️ BigBossizzz Academic Login Alert</h3>
            <p><strong>Account:</strong> {user.username} ({user.email})</p>
            <p><strong>Role:</strong> {user.role.title()}</p>
            <p><strong>Login Time:</strong> {login_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Academic Platform:</strong> BigBossizzz</p>
            <p>If this wasn't you, please contact academic support immediately.</p>
        </div>
        """
        
        return brevo_service.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            from_name="BigBossizzz Academic Security"
        )
        
    except Exception as e:
        logging.error(f"❌ Login notification failed: {str(e)}")
        return False

def send_host_login_notification(host, user=None, login_event=None):
    """Send special login notification for hosts/admins (compatible with routes.py)"""
    # Handle the specific signature expected by routes.py
    actual_user = user if user else host
    return send_login_notification(actual_user, login_event)

def send_violation_alert(instructor_email: str, student_name: str,
                       quiz_title: str, violation_details: str) -> bool:
    """Send real-time violation alert to instructor"""
    try:
        subject = f"🚨 URGENT: Academic Violation Alert - {student_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .alert {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .violation-box {{ background: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; }}
                .urgent {{ font-size: 18px; font-weight: bold; color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert">
                    <h1>🚨 URGENT ACADEMIC VIOLATION</h1>
                    <p>Immediate attention required</p>
                </div>
                <div class="content">
                    <p class="urgent">Academic integrity violation detected during examination!</p>
                    
                    <div class="violation-box">
                        <h3>📋 Violation Details:</h3>
                        <p><strong>Student:</strong> {student_name}</p>
                        <p><strong>Examination:</strong> {quiz_title}</p>
                        <p><strong>Violation:</strong> {violation_details}</p>
                        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                    
                    <p><strong>Action Required:</strong> Please review the live monitoring dashboard immediately to assess the situation.</p>
                    
                    <p style="text-align: center;">
                        <a href="{url_for('admin_dashboard', _external=True)}" class="button">🔍 View Admin Dashboard</a>
                    </p>
                    
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        This is an automated academic integrity alert from BigBossizzz platform.
                        Immediate instructor review recommended.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return brevo_service.send_email(
            to_email=instructor_email,
            subject=subject,
            html_content=html_content,
            from_name="BigBossizzz Academic Security"
        )
        
    except Exception as e:
        logging.error(f"❌ Failed to send violation alert: {str(e)}")
        return False

def test_email_service():
    """Test if the email service is working"""
    return brevo_service.api_key and len(brevo_service.api_key) > 10