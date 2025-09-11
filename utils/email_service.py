"""
Free Email Service using Brevo (formerly Sendinblue)
300 emails/day completely FREE - perfect for academic use
"""

import os
import requests
import logging
from typing import Optional, Dict, Any

class FreeEmailService:
    """
    Completely free email service using Brevo API
    - 300 emails/day forever free
    - Perfect for academic institutions
    - No credit card required
    """
    
    def __init__(self):
        self.api_key = os.environ.get('BREVO_API_KEY', '')
        self.api_url = 'https://api.brevo.com/v3/smtp/email'
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'api-key': self.api_key
        }
        
        if not self.api_key:
            logging.warning("BREVO_API_KEY not set. Email functionality will be disabled.")
    
    def send_email(self, 
                   to_email: str, 
                   subject: str, 
                   html_content: Optional[str] = None,
                   text_content: Optional[str] = None,
                   from_email: Optional[str] = None,
                   from_name: str = "BigBossizzz Academic Platform") -> bool:
        """
        Send email using Brevo's free API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content (optional)
            text_content: Plain text content (optional)
            from_email: Sender email (uses default if None)
            from_name: Sender name
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        
        if not self.api_key:
            logging.error("Cannot send email: BREVO_API_KEY not configured")
            return False
        
        # Use default from_email if not provided
        if not from_email:
            from_email = "noreply@bigbossizzz.com"  # You can use any email here
        
        # Prepare email data
        email_data = {
            "sender": {
                "name": from_name,
                "email": from_email
            },
            "to": [
                {
                    "email": to_email
                }
            ],
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
                logging.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logging.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Email service error: {e}")
            return False
    
    def send_verification_email(self, user_email: str, username: str, 
                              temporary_password: str) -> bool:
        """
        Send verification email with login credentials to new student
        """
        subject = "🎓 Welcome to BigBossizzz - Your Academic Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f8f9fa; }}
                .credentials {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 Welcome to BigBossizzz</h1>
                    <p>Your Academic Examination Platform</p>
                </div>
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Your academic account has been created successfully. You can now access quizzes and examinations on the BigBossizzz platform.</p>
                    
                    <div class="credentials">
                        <h3>🔐 Your Login Credentials:</h3>
                        <p><strong>Username:</strong> {username}</p>
                        <p><strong>Temporary Password:</strong> {temporary_password}</p>
                        <p><strong>Email:</strong> {user_email}</p>
                    </div>
                    
                    <p><strong>⚠️ Important:</strong> Please change your password after first login for security.</p>
                    
                    <p style="text-align: center;">
                        <a href="http://localhost:5000/login" class="button">Login to Platform</a>
                    </p>
                    
                    <h3>📚 Next Steps:</h3>
                    <ul>
                        <li>Log in with your credentials</li>
                        <li>Complete your profile setup</li>
                        <li>Check for available quizzes</li>
                        <li>Review proctoring guidelines</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>© 2025 BigBossizzz Academic Platform</p>
                    <p>This is an automated message for academic verification.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            from_name="BigBossizzz Academic Team"
        )
    
    def send_violation_alert(self, instructor_email: str, student_name: str,
                           quiz_title: str, violation_details: str) -> bool:
        """
        Send real-time violation alert to instructor
        """
        subject = f"🚨 URGENT: Quiz Violation Alert - {student_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .alert {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .violation-box {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .button {{ display: inline-block; padding: 10px 20px; background: #dc3545; color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert">
                    <h1>🚨 URGENT VIOLATION ALERT</h1>
                </div>
                <div class="content">
                    <h2>Quiz Violation Detected</h2>
                    
                    <div class="violation-box">
                        <p><strong>Student:</strong> {student_name}</p>
                        <p><strong>Quiz:</strong> {quiz_title}</p>
                        <p><strong>Violation:</strong> {violation_details}</p>
                        <p><strong>Time:</strong> {str(logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None)))}</p>
                    </div>
                    
                    <p>Please check the live monitoring dashboard immediately for more details.</p>
                    
                    <p style="text-align: center;">
                        <a href="http://localhost:5000/admin/live-monitoring" class="button">View Live Dashboard</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=instructor_email,
            subject=subject,
            html_content=html_content,
            from_name="BigBossizzz Security System"
        )
    
    def test_connection(self) -> bool:
        """
        Test if the email service is properly configured
        """
        if not self.api_key:
            return False
        
        # Test with a simple API call
        test_url = 'https://api.brevo.com/v3/account'
        test_headers = {'api-key': self.api_key or ''}
        
        try:
            response = requests.get(test_url, headers=test_headers, timeout=10)
            return response.status_code == 200
        except:
            return False

# Global email service instance
email_service = FreeEmailService()