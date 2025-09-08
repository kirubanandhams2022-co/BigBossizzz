from flask_mail import Message
from app import mail, app
from flask import url_for, render_template_string
import logging

def send_verification_email(user):
    """Send email verification to user"""
    try:
        token = user.generate_verification_token()
        verification_url = url_for('verify_email', token=token, _external=True)
        
        subject = 'Verify Your Email - Proctoring Platform'
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Welcome to Our Proctoring Platform!</h2>
            <p>Hello {user.username},</p>
            <p>Thank you for registering as a {user.role.title()}. To complete your registration, please verify your email address by clicking the link below:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email Address</a>
            </div>
            <p>If you cannot click the button, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{verification_url}</p>
            <p>This link will expire in 24 hours for security reasons.</p>
            <hr style="margin: 30px 0; border: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">If you did not create this account, please ignore this email.</p>
        </div>
        """
        
        text_body = f"""
        Welcome to Our Proctoring Platform!
        
        Hello {user.username},
        
        Thank you for registering as a {user.role.title()}. To complete your registration, please verify your email address by visiting:
        
        {verification_url}
        
        This link will expire in 24 hours for security reasons.
        
        If you did not create this account, please ignore this email.
        """
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )
        
        mail.send(msg)
        logging.info(f"Verification email sent to {user.email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

def send_credentials_email(user, password):
    """Send login credentials to user after email verification"""
    try:
        login_url = url_for('login', _external=True)
        
        subject = 'Your Login Credentials - Proctoring Platform'
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Your Account is Ready!</h2>
            <p>Hello {user.username},</p>
            <p>Your email has been verified successfully. Here are your login credentials:</p>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Email:</strong> {user.email}</p>
                <p><strong>Role:</strong> {user.role.title()}</p>
                <p><strong>Login URL:</strong> <a href="{login_url}">{login_url}</a></p>
            </div>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{login_url}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Login Now</a>
            </div>
            <p><strong>Important Security Notes:</strong></p>
            <ul>
                <li>Please change your password after your first login</li>
                <li>Do not share your credentials with anyone</li>
                <li>Log out completely when finished</li>
            </ul>
            <hr style="margin: 30px 0; border: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">This email contains sensitive information. Please keep it secure.</p>
        </div>
        """
        
        text_body = f"""
        Your Account is Ready!
        
        Hello {user.username},
        
        Your email has been verified successfully. Here are your login credentials:
        
        Email: {user.email}
        Role: {user.role.title()}
        Login URL: {login_url}
        
        Important Security Notes:
        - Please change your password after your first login
        - Do not share your credentials with anyone
        - Log out completely when finished
        
        This email contains sensitive information. Please keep it secure.
        """
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )
        
        mail.send(msg)
        logging.info(f"Credentials email sent to {user.email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send credentials email to {user.email}: {str(e)}")
        return False

def send_quiz_invitation(user, quiz, host):
    """Send quiz invitation to participant"""
    try:
        quiz_url = url_for('take_quiz', quiz_id=quiz.id, _external=True)
        
        subject = f'Quiz Invitation: {quiz.title}'
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Quiz Invitation</h2>
            <p>Hello {user.username},</p>
            <p>You have been invited to take a quiz by {host.username}.</p>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">{quiz.title}</h3>
                <p><strong>Description:</strong> {quiz.description or 'No description provided'}</p>
                <p><strong>Time Limit:</strong> {quiz.time_limit} minutes</p>
                <p><strong>Proctoring:</strong> {'Enabled' if quiz.proctoring_enabled else 'Disabled'}</p>
            </div>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{quiz_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Start Quiz</a>
            </div>
            <p>Please ensure you have a stable internet connection and are in a quiet environment before starting.</p>
        </div>
        """
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=html_body
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        logging.error(f"Failed to send quiz invitation to {user.email}: {str(e)}")
        return False
