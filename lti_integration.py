"""
LTI (Learning Tools Interoperability) Integration Module
Provides LTI 1.1 and LTI 1.3 support for Canvas, Blackboard, Moodle integration
"""

import hashlib
import hmac
import time
import uuid
import base64
import urllib.parse
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import requests
from flask import request, session, url_for, redirect, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from models import User, Quiz, QuizAttempt

# LTI Configuration
class LTIConfig:
    # LTI 1.1 Parameters
    LTI_VERSION = "LTI-1p0"
    LTI_MESSAGE_TYPE = "basic-lti-launch-request"
    
    # LTI 1.3 Parameters
    LTI_13_VERSION = "1.3.0"
    LTI_13_MESSAGE_TYPE = "LtiResourceLinkRequest"
    
    # Supported LMS platforms
    SUPPORTED_PLATFORMS = {
        'canvas': {
            'name': 'Canvas',
            'oauth_url_template': 'https://{domain}/api/lti/authorize_redirect',
            'token_url_template': 'https://{domain}/login/oauth2/token',
            'grade_passback_url_template': 'https://{domain}/api/lti/v1/tools/{tool_id}/grade_passback'
        },
        'blackboard': {
            'name': 'Blackboard Learn',
            'oauth_url_template': 'https://{domain}/webapps/bb-auth-provider-sso/execute/authorizeRequest',
            'token_url_template': 'https://{domain}/learn/api/public/v1/oauth2/token',
            'grade_passback_url_template': 'https://{domain}/learn/api/public/v1/courses/{course_id}/gradebook/columns/{column_id}/attempts/{attempt_id}'
        },
        'moodle': {
            'name': 'Moodle',
            'oauth_url_template': 'https://{domain}/mod/lti/auth.php',
            'token_url_template': 'https://{domain}/mod/lti/token.php',
            'grade_passback_url_template': 'https://{domain}/mod/lti/service.php'
        }
    }

class LTIProvider:
    """LTI Provider implementation for accepting launches from LMS"""
    
    def __init__(self, consumer_key: str, consumer_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        
    def validate_signature(self, request_data: Dict) -> bool:
        """Validate OAuth 1.0 signature for LTI 1.1 requests"""
        try:
            # Extract signature from request
            oauth_signature = request_data.get('oauth_signature', '')
            if not oauth_signature:
                return False
            
            # Remove signature from parameters for validation
            params = {k: v for k, v in request_data.items() if k != 'oauth_signature'}
            
            # Create base string
            base_string = self._create_base_string('POST', request.url_root.rstrip('/') + '/lti/launch', params)
            
            # Create signing key
            signing_key = f"{urllib.parse.quote_plus(self.consumer_secret)}&"
            
            # Calculate expected signature
            expected_signature = base64.b64encode(
                hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
            ).decode()
            
            return hmac.compare_digest(oauth_signature, expected_signature)
            
        except Exception as e:
            logging.error(f"LTI signature validation error: {e}")
            return False
    
    def _create_base_string(self, method: str, url: str, params: Dict) -> str:
        """Create OAuth base string for signature validation"""
        # Normalize parameters
        normalized_params = []
        for key, value in sorted(params.items()):
            normalized_params.append(f"{urllib.parse.quote_plus(str(key))}={urllib.parse.quote_plus(str(value))}")
        
        param_string = "&".join(normalized_params)
        
        return f"{method}&{urllib.parse.quote_plus(url)}&{urllib.parse.quote_plus(param_string)}"
    
    def process_launch_request(self, request_data: Dict) -> Tuple[bool, Dict]:
        """Process LTI launch request and extract user/context information"""
        try:
            # Validate required LTI parameters
            required_params = [
                'lti_message_type', 'lti_version', 'resource_link_id',
                'user_id', 'oauth_consumer_key'
            ]
            
            for param in required_params:
                if param not in request_data:
                    return False, {'error': f'Missing required parameter: {param}'}
            
            # Validate message type and version
            if request_data.get('lti_message_type') != LTIConfig.LTI_MESSAGE_TYPE:
                return False, {'error': 'Invalid LTI message type'}
            
            if request_data.get('lti_version') != LTIConfig.LTI_VERSION:
                return False, {'error': 'Unsupported LTI version'}
            
            # Validate consumer key
            if request_data.get('oauth_consumer_key') != self.consumer_key:
                return False, {'error': 'Invalid consumer key'}
            
            # Extract user information
            user_info = {
                'lti_user_id': request_data.get('user_id'),
                'username': request_data.get('lis_person_sourcedid', ''),
                'email': request_data.get('lis_person_contact_email_primary', ''),
                'first_name': request_data.get('lis_person_name_given', ''),
                'last_name': request_data.get('lis_person_name_family', ''),
                'full_name': request_data.get('lis_person_name_full', ''),
                'roles': request_data.get('roles', '').split(',')
            }
            
            # Extract context information
            context_info = {
                'course_id': request_data.get('context_id', ''),
                'course_title': request_data.get('context_title', ''),
                'resource_link_id': request_data.get('resource_link_id'),
                'resource_link_title': request_data.get('resource_link_title', ''),
                'resource_link_description': request_data.get('resource_link_description', ''),
                'tool_consumer_instance_guid': request_data.get('tool_consumer_instance_guid', ''),
                'tool_consumer_instance_name': request_data.get('tool_consumer_instance_name', ''),
            }
            
            # Extract grade passback information
            grade_info = {
                'lis_outcome_service_url': request_data.get('lis_outcome_service_url', ''),
                'lis_result_sourcedid': request_data.get('lis_result_sourcedid', ''),
                'lis_person_sourcedid': request_data.get('lis_person_sourcedid', '')
            }
            
            return True, {
                'user_info': user_info,
                'context_info': context_info,
                'grade_info': grade_info,
                'custom_params': {k: v for k, v in request_data.items() if k.startswith('custom_')}
            }
            
        except Exception as e:
            logging.error(f"LTI launch processing error: {e}")
            return False, {'error': f'Launch processing failed: {str(e)}'}

class LTIUser:
    """Manages LTI user provisioning and authentication"""
    
    @staticmethod
    def create_or_update_user(lti_data: Dict) -> Optional[User]:
        """Create or update user from LTI launch data"""
        try:
            user_info = lti_data.get('user_info', {})
            lti_user_id = user_info.get('lti_user_id')
            email = user_info.get('email')
            
            if not lti_user_id:
                return None
            
            # Check if user exists by LTI user ID or email
            user = User.query.filter(
                (User.lti_user_id == lti_user_id) | 
                (User.email == email and email != '')
            ).first()
            
            if user:
                # Update existing user
                user.lti_user_id = lti_user_id
                if email and not user.email:
                    user.email = email
                if user_info.get('username') and not user.username:
                    user.username = user_info.get('username')
            else:
                # Create new user
                username = user_info.get('username') or f"lti_user_{lti_user_id}"
                email = email or f"{username}@lti.local"
                
                # Determine user role based on LTI roles
                roles = user_info.get('roles', [])
                role = 'participant'  # default
                
                if any(r.lower() in ['instructor', 'teacher', 'administrator'] for r in roles):
                    role = 'host'
                elif any(r.lower() in ['admin', 'administrator'] for r in roles):
                    role = 'admin'
                
                user = User(
                    username=username,
                    email=email,
                    role=role,
                    lti_user_id=lti_user_id,
                    is_verified=True,  # LTI users are pre-verified
                    password_hash=generate_password_hash(str(uuid.uuid4()))  # Random password
                )
                
                db.session.add(user)
            
            db.session.commit()
            return user
            
        except Exception as e:
            logging.error(f"LTI user creation error: {e}")
            db.session.rollback()
            return None

class LTIGradePassback:
    """Handles grade passback to LMS"""
    
    def __init__(self, consumer_key: str, consumer_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
    
    def send_grade(self, grade_info: Dict, score: float, max_score: float = 100.0) -> bool:
        """Send grade back to LMS via LTI grade passback"""
        try:
            service_url = grade_info.get('lis_outcome_service_url')
            source_id = grade_info.get('lis_result_sourcedid')
            
            if not service_url or not source_id:
                logging.warning("Missing grade passback information")
                return False
            
            # Calculate normalized score (0.0 to 1.0)
            normalized_score = min(max(score / max_score, 0.0), 1.0)
            
            # Create XML payload for grade passback
            xml_payload = self._create_grade_xml(source_id, normalized_score)
            
            # Create OAuth parameters
            oauth_params = {
                'oauth_callback': 'about:blank',
                'oauth_consumer_key': self.consumer_key,
                'oauth_nonce': str(uuid.uuid4()),
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': str(int(time.time())),
                'oauth_version': '1.0'
            }
            
            # Create base string and signature
            base_string = self._create_base_string('POST', service_url, oauth_params)
            signing_key = f"{urllib.parse.quote_plus(self.consumer_secret)}&"
            signature = base64.b64encode(
                hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
            ).decode()
            
            oauth_params['oauth_signature'] = signature
            
            # Create Authorization header
            auth_header = 'OAuth ' + ', '.join([f'{k}="{v}"' for k, v in oauth_params.items()])
            
            # Send grade passback request
            headers = {
                'Authorization': auth_header,
                'Content-Type': 'application/xml'
            }
            
            response = requests.post(service_url, data=xml_payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logging.info(f"Grade passback successful for source_id: {source_id}")
                return True
            else:
                logging.error(f"Grade passback failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Grade passback error: {e}")
            return False
    
    def _create_grade_xml(self, source_id: str, score: float) -> str:
        """Create XML payload for LTI grade passback"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
    <imsx_POXHeader>
        <imsx_POXRequestHeaderInfo>
            <imsx_version>V1.0</imsx_version>
            <imsx_messageIdentifier>{uuid.uuid4()}</imsx_messageIdentifier>
        </imsx_POXRequestHeaderInfo>
    </imsx_POXHeader>
    <imsx_POXBody>
        <replaceResultRequest>
            <resultRecord>
                <sourcedGUID>
                    <sourcedId>{source_id}</sourcedId>
                </sourcedGUID>
                <result>
                    <resultScore>
                        <language>en</language>
                        <textString>{score:.6f}</textString>
                    </resultScore>
                </result>
            </resultRecord>
        </replaceResultRequest>
    </imsx_POXBody>
</imsx_POXEnvelopeRequest>"""
    
    def _create_base_string(self, method: str, url: str, params: Dict) -> str:
        """Create OAuth base string for signature"""
        normalized_params = []
        for key, value in sorted(params.items()):
            normalized_params.append(f"{urllib.parse.quote_plus(str(key))}={urllib.parse.quote_plus(str(value))}")
        
        param_string = "&".join(normalized_params)
        return f"{method}&{urllib.parse.quote_plus(url)}&{urllib.parse.quote_plus(param_string)}"

class LTIToolConfiguration:
    """Generates LTI tool configuration for LMS setup"""
    
    @staticmethod
    def generate_xml_config(base_url: str, consumer_key: str, title: str = "BigBossizzz Proctoring Platform") -> str:
        """Generate LTI Tool Configuration XML"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<cartridge_basiclti_link xmlns="http://www.imsglobal.org/xsd/imslticc_v1p0"
    xmlns:blti="http://www.imsglobal.org/xsd/imsbasiclti_v1p0"
    xmlns:lticm="http://www.imsglobal.org/xsd/imslticm_v1p0"
    xmlns:lticp="http://www.imsglobal.org/xsd/imslticp_v1p0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imslticc_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticc_v1p0.xsd
    http://www.imsglobal.org/xsd/imsbasiclti_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imsbasiclti_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticm_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticm_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticp_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticp_v1p0.xsd">

    <blti:title>{title}</blti:title>
    <blti:description>Comprehensive online examination and quiz management system with advanced proctoring capabilities</blti:description>
    <blti:icon>{base_url}/static/img/icon.png</blti:icon>
    <blti:launch_url>{base_url}/lti/launch</blti:launch_url>
    
    <blti:extensions platform="canvas.instructure.com">
        <lticm:property name="tool_id">bigbossizzz_proctoring</lticm:property>
        <lticm:property name="privacy_level">public</lticm:property>
        <lticm:options name="course_navigation">
            <lticm:property name="url">{base_url}/lti/launch</lticm:property>
            <lticm:property name="text">{title}</lticm:property>
            <lticm:property name="enabled">true</lticm:property>
        </lticm:options>
        <lticm:options name="assignment_selection">
            <lticm:property name="url">{base_url}/lti/launch</lticm:property>
            <lticm:property name="text">{title}</lticm:property>
            <lticm:property name="enabled">true</lticm:property>
            <lticm:property name="message_type">ContentItemSelectionRequest</lticm:property>
        </lticm:options>
    </blti:extensions>
    
    <blti:extensions platform="blackboard.com">
        <lticm:property name="tool_id">bigbossizzz_proctoring</lticm:property>
        <lticm:property name="privacy_level">public</lticm:property>
    </blti:extensions>
    
    <blti:extensions platform="moodle.org">
        <lticm:property name="tool_id">bigbossizzz_proctoring</lticm:property>
        <lticm:property name="privacy_level">public</lticm:property>
    </blti:extensions>
    
    <cartridge_bundle identifierref="BLTI001_Bundle"/>
    <cartridge_icon identifierref="BLTI001_Icon"/>
</cartridge_basiclti_link>"""
    
    @staticmethod
    def generate_json_config(base_url: str, consumer_key: str, title: str = "BigBossizzz Proctoring Platform") -> Dict:
        """Generate LTI 1.3 Tool Configuration JSON"""
        return {
            "title": title,
            "description": "Comprehensive online examination and quiz management system with advanced proctoring capabilities",
            "oidc_initiation_url": f"{base_url}/lti/1.3/login",
            "target_link_uri": f"{base_url}/lti/1.3/launch",
            "scopes": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
            ],
            "extensions": [
                {
                    "domain": base_url.replace('https://', '').replace('http://', ''),
                    "tool_id": "bigbossizzz_proctoring",
                    "platform": "canvas.instructure.com",
                    "settings": {
                        "placements": [
                            {
                                "placement": "course_navigation",
                                "message_type": "LtiResourceLinkRequest",
                                "text": title,
                                "enabled": True
                            },
                            {
                                "placement": "assignment_selection",
                                "message_type": "LtiDeepLinkingRequest", 
                                "text": title,
                                "enabled": True
                            }
                        ]
                    }
                }
            ],
            "public_jwk_url": f"{base_url}/lti/1.3/jwks",
            "custom_fields": {
                "canvas_user_id": "$Canvas.user.id",
                "canvas_course_id": "$Canvas.course.id",
                "canvas_assignment_id": "$Canvas.assignment.id"
            }
        }

# Helper functions for LTI integration
def get_lti_provider(consumer_key: str = None, consumer_secret: str = None) -> LTIProvider:
    """Get configured LTI provider instance"""
    # In production, these should come from environment variables or database
    default_key = "bigbossizzz_lti_key"
    default_secret = "bigbossizzz_lti_secret_change_in_production"
    
    return LTIProvider(
        consumer_key=consumer_key or default_key,
        consumer_secret=consumer_secret or default_secret
    )

def get_lti_grade_passback(consumer_key: str = None, consumer_secret: str = None) -> LTIGradePassback:
    """Get configured LTI grade passback instance"""
    default_key = "bigbossizzz_lti_key"
    default_secret = "bigbossizzz_lti_secret_change_in_production"
    
    return LTIGradePassback(
        consumer_key=consumer_key or default_key,
        consumer_secret=consumer_secret or default_secret
    )