from flask_mail import Message
from app import mail, app
from flask import url_for, render_template_string
import logging
from datetime import datetime

def send_verification_email(user):
    """Send email verification to user"""
    try:
        # Check if email is configured
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            logging.warning(f"Email not configured. Auto-verifying user {user.email} for development")
            # Auto-verify user for development/demo purposes
            user.is_verified = True
            from app import db
            db.session.commit()
            return True
            
        token = user.generate_verification_token()
        verification_url = url_for('verify_email', token=token, _external=True)
        
        subject = 'Verify Your Email - BigBossizzz'
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">👁️ Welcome to BigBossizzz!</h2>
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
👁️ Welcome to BigBossizzz!
        
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
        # Skip email if not configured - just log credentials
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            logging.info(f"CREDENTIALS for {user.email} - Username: {user.username}, Password: {password}")
            return True
            
        login_url = url_for('login', _external=True)
        
        subject = 'Your Login Credentials - BigBossizzz'
        
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

def send_login_notification(user, login_event):
    """Send login notification to user (like VIT Moodle system)"""
    try:
        import platform
        from datetime import datetime
        import re
        
        # Parse user agent for device info
        user_agent = login_event.user_agent or ''
        device_info = parse_user_agent(user_agent)
        
        # Format date and time
        login_time = login_event.login_time.strftime('%A, %d %B %Y, %I:%M %p')
        
        subject = f'New sign in to your {user.role.title()} account'
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                <h2 style="margin: 0;">👁️ BigBossizzz Security Alert</h2>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                <p style="font-size: 16px; margin-bottom: 20px;">Hi <strong>{user.username}</strong>,</p>
                
                <p style="margin-bottom: 20px;">Your BigBossizzz account was just signed in to from a new device.</p>
                
                <div style="background-color: white; padding: 20px; border-radius: 5px; border-left: 4px solid #007bff; margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 30%;">Your account:</td>
                            <td style="padding: 8px 0;">{user.username} {user.email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Login time:</td>
                            <td style="padding: 8px 0;">{login_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Device:</td>
                            <td style="padding: 8px 0; word-break: break-all;">{device_info}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">IP Address:</td>
                            <td style="padding: 8px 0;">{login_event.ip_address}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold;">✅ If this was you, then you don't need to do anything.</p>
                </div>
                
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold;">⚠️ If you don't recognize this activity, please change your password immediately.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_for('profile', _external=True)}" style="background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">🔒 Change Password</a>
                </div>
                
                <hr style="margin: 30px 0; border: 1px solid #dee2e6;">
                
                <p style="color: #6c757d; font-size: 12px; margin: 0;">This is an automated security notification from BigBossizzz. Do not reply to this email.</p>
            </div>
        </div>
        """
        
        text_body = f"""
        BigBossizzz Security Alert
        
        Hi {user.username},
        
        Your BigBossizzz account was just signed in to from a new device.
        
        Your account: {user.username} {user.email}
        Login time: {login_time}
        Device: {device_info}
        IP Address: {login_event.ip_address}
        
        If this was you, then you don't need to do anything.
        
        If you don't recognize this activity, please change your password immediately.
        
        Change Password: {url_for('profile', _external=True)}
        
        This is an automated security notification from BigBossizzz.
        """
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=text_body,
            html=html_body
        )
        
        mail.send(msg)
        logging.info(f"Login notification sent to {user.email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send login notification to {user.email}: {str(e)}")
        return False

def send_host_login_notification(host_user, participant_user, login_event):
    """Send login notification to host when participant logs in"""
    try:
        from datetime import datetime
        
        # Parse user agent for device info
        device_info = parse_user_agent(login_event.user_agent or '')
        login_time = login_event.login_time.strftime('%A, %d %B %Y, %I:%M %p')
        
        subject = f'Participant Login Alert: {participant_user.username}'
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #28a745; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                <h2 style="margin: 0;">👁️ BigBossizzz Host Alert</h2>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                <p style="font-size: 16px; margin-bottom: 20px;">Hi <strong>{host_user.username}</strong>,</p>
                
                <p style="margin-bottom: 20px;">A participant under your supervision has logged in to BigBossizzz.</p>
                
                <div style="background-color: white; padding: 20px; border-radius: 5px; border-left: 4px solid #28a745; margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 30%;">Participant:</td>
                            <td style="padding: 8px 0;">{participant_user.username} ({participant_user.email})</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Login time:</td>
                            <td style="padding: 8px 0;">{login_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Device:</td>
                            <td style="padding: 8px 0; word-break: break-all;">{device_info}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">IP Address:</td>
                            <td style="padding: 8px 0;">{login_event.ip_address}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_for('host_dashboard', _external=True)}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">📊 View Dashboard</a>
                </div>
                
                <hr style="margin: 30px 0; border: 1px solid #dee2e6;">
                
                <p style="color: #6c757d; font-size: 12px; margin: 0;">This is an automated notification from BigBossizzz. Do not reply to this email.</p>
            </div>
        </div>
        """
        
        msg = Message(
            subject=subject,
            recipients=[host_user.email],
            html=html_body
        )
        
        mail.send(msg)
        logging.info(f"Host login notification sent to {host_user.email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send host notification to {host_user.email}: {str(e)}")
        return False

def parse_user_agent(user_agent):
    """Parse user agent string to extract readable device info"""
    import re
    
    if not user_agent:
        return 'Unknown Device'
    
    # Browser detection
    browser = 'Unknown Browser'
    if 'Chrome' in user_agent and 'Edg' not in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        browser = 'Safari'
    elif 'Edg' in user_agent:
        browser = 'Microsoft Edge'
    elif 'Opera' in user_agent or 'OPR' in user_agent:
        browser = 'Opera'
    
    # OS detection
    os_name = 'Unknown OS'
    if 'Windows NT 10.0' in user_agent:
        os_name = 'Windows 10/11'
    elif 'Windows NT' in user_agent:
        os_name = 'Windows'
    elif 'Mac OS X' in user_agent:
        os_name = 'macOS'
    elif 'Linux' in user_agent:
        os_name = 'Linux'
    elif 'Android' in user_agent:
        os_name = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        os_name = 'iOS'
    
    # Version extraction for Chrome
    version = ''
    if 'Chrome' in user_agent:
        version_match = re.search(r'Chrome/([0-9]+\.[0-9]+)', user_agent)
        if version_match:
            version = f' {version_match.group(1)}'
    
    return f'{browser}{version} on {os_name}'
