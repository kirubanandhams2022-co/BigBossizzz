# Proctoring Platform

## Overview

This is a comprehensive online examination and quiz management system with advanced proctoring capabilities. The platform supports role-based access with three user types: administrators, hosts (who create and manage quizzes), and participants (who take quizzes). The system includes real-time proctoring features, email verification, quiz creation tools, and comprehensive result tracking.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask-based web application** with SQLAlchemy ORM for database operations
- **Role-based authentication** using Flask-Login with three user roles (admin, host, participant)
- **Email verification system** with token-based account activation
- **Session management** with secure session handling and proxy fix middleware

### Database Design
- **PostgreSQL database** with SQLAlchemy models for Users, Quizzes, Questions, QuestionOptions, QuizAttempts, Answers, and ProctoringEvents
- **User model** includes verification tokens, password hashing, and role management
- **Quiz model** supports multiple question types (multiple choice, true/false, text) with time limits and proctoring settings
- **Attempt tracking** with comprehensive answer storage and proctoring event logging

### Frontend Architecture
- **Jinja2 templating** with Bootstrap dark theme for responsive UI
- **Client-side JavaScript** for quiz timer, auto-save functionality, and proctoring controls
- **Real-time proctoring** using WebRTC for camera access and browser behavior monitoring
- **Progressive enhancement** with fallback support for non-JavaScript environments

### Authentication & Authorization
- **Password-based authentication** with werkzeug password hashing
- **Email verification workflow** requiring users to verify email before receiving login credentials
- **Role-based access control** with different dashboard views and permissions per role
- **Session-based login** with secure cookie handling

### Proctoring System
- **Browser-based monitoring** including tab switching detection, fullscreen enforcement, and screenshot detection
- **Camera integration** for facial recognition and monitoring (WebRTC-based)
- **Behavioral tracking** monitoring mouse movements, keyboard activity, window focus, and right-click/copy-paste prevention
- **Event logging** storing all proctoring violations and suspicious activities in the database

### Quiz Management
- **Dynamic quiz creation** with support for multiple question types and configurable time limits
- **Real-time quiz taking** with auto-save functionality and timer warnings
- **Comprehensive result tracking** showing scores, correct/incorrect answers, and time spent
- **Administrative oversight** with system-wide statistics and user management

## External Dependencies

### Email Services
- **Flask-Mail** for SMTP email delivery with Gmail integration support
- **Email templates** for verification emails and credential distribution
- **Environment-based configuration** for SMTP settings and authentication

### Frontend Libraries
- **Bootstrap 5** with dark theme variant for responsive design
- **Font Awesome 6** for consistent iconography throughout the interface
- **Custom CSS** for quiz-specific styling and proctoring indicators

### Database
- **PostgreSQL** as the primary database with connection pooling and health checks
- **SQLAlchemy** for ORM operations with declarative base and relationship management
- **Database migrations** supported through Flask-SQLAlchemy

### JavaScript Libraries
- **WebRTC APIs** for camera and microphone access in proctoring features
- **HTML5 Canvas** for image capture and face detection processing
- **Local Storage API** for temporary quiz answer storage and auto-save functionality

### Security & Monitoring
- **Werkzeug security** for password hashing and session management
- **Environment variable configuration** for sensitive settings like database URLs and email credentials
- **Proxy fix middleware** for proper header handling in production deployments