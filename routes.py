from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Quiz, Question, QuestionOption, QuizAttempt, Answer, ProctoringEvent
from forms import RegistrationForm, LoginForm, QuizForm, QuestionForm, ProfileForm
from email_service import send_verification_email, send_credentials_email
from datetime import datetime
import json
import logging

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/default-accounts')
def default_accounts():
    """Show default login accounts"""
    return render_template('default_accounts.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken. Please choose a different username.', 'error')
            return render_template('register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        if send_verification_email(user):
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return render_template('verify_email.html', user=user, resent=False)
        else:
            flash('Registration successful, but we could not send the verification email. You can request a new one from the login page.', 'warning')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/verify/<token>')
def verify_email(token):
    """Verify email address"""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('login'))
    
    if user.verify_email(token):
        # Store the original password temporarily to send in email
        # In production, you might want to generate a temporary password instead
        temp_password = "Please change this password after login"
        
        db.session.commit()
        
        # Send credentials email
        if send_credentials_email(user, temp_password):
            flash('Email verified successfully! Your login credentials have been sent to your email.', 'success')
        else:
            flash('Email verified successfully! You can now log in with your credentials.', 'success')
    else:
        flash('Email verification failed. Please try again.', 'error')
    
    return redirect(url_for('login'))

@app.route('/resend-verification/<email>')
def resend_verification(email):
    """Resend email verification"""
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))
    
    if user.is_verified:
        flash('Your email is already verified. You can log in now.', 'info')
        return redirect(url_for('login'))
    
    # Generate new verification token
    user.generate_verification_token()
    db.session.commit()
    
    # Send verification email
    if send_verification_email(user):
        flash('Verification email sent successfully! Please check your inbox and spam folder.', 'success')
        return render_template('verify_email.html', user=user, resent=True)
    else:
        flash('Failed to send verification email. Please try again later.', 'error')
    
    return redirect(url_for('login'))

@app.route('/request-verification', methods=['GET', 'POST'])
def request_verification():
    """Request email verification page"""
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('request_verification.html')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address.', 'error')
            return render_template('request_verification.html')
        
        if user.is_verified:
            flash('Your email is already verified. You can log in now.', 'info')
            return redirect(url_for('login'))
        
        # Generate new verification token
        user.generate_verification_token()
        db.session.commit()
        
        # Send verification email
        if send_verification_email(user):
            flash('Verification email sent successfully! Please check your inbox and spam folder.', 'success')
            return render_template('verify_email.html', user=user, resent=True)
        else:
            flash('Failed to send verification email. Please try again later.', 'error')
    
    return render_template('request_verification.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Please verify your email address before logging in.', 'warning')
                # Add resend verification option
                resend_link = url_for('resend_verification', email=user.email)
                flash(f'Need a new verification email? <a href="{resend_link}">Click here to resend</a>', 'info')
                return render_template('login.html', form=form)
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - redirects based on user role"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_host():
        return redirect(url_for('host_dashboard'))
    else:
        return redirect(url_for('participant_dashboard'))

@app.route('/host/dashboard')
@login_required
def host_dashboard():
    """Host dashboard"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    quizzes = Quiz.query.filter_by(creator_id=current_user.id).order_by(Quiz.created_at.desc()).all()
    
    # Get recent quiz attempts for host's quizzes
    recent_attempts = []
    for quiz in quizzes:
        attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).order_by(QuizAttempt.started_at.desc()).limit(5).all()
        recent_attempts.extend(attempts)
    
    recent_attempts.sort(key=lambda x: x.started_at, reverse=True)
    recent_attempts = recent_attempts[:10]  # Show only 10 most recent
    
    return render_template('host_dashboard.html', quizzes=quizzes, recent_attempts=recent_attempts)

@app.route('/participant/dashboard')
@login_required
def participant_dashboard():
    """Participant dashboard"""
    # Get available quizzes (you might want to implement invitation system)
    available_quizzes = Quiz.query.filter_by(is_active=True).all()
    
    # Get participant's quiz attempts
    my_attempts = QuizAttempt.query.filter_by(participant_id=current_user.id).order_by(QuizAttempt.started_at.desc()).all()
    
    return render_template('participant_dashboard.html', available_quizzes=available_quizzes, my_attempts=my_attempts)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get system statistics
    total_users = User.query.count()
    total_hosts = User.query.filter_by(role='host').count()
    total_participants = User.query.filter_by(role='participant').count()
    total_quizzes = Quiz.query.count()
    total_attempts = QuizAttempt.query.count()
    
    # Recent registrations
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    stats = {
        'total_users': total_users,
        'total_hosts': total_hosts,
        'total_participants': total_participants,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts
    }
    
    return render_template('admin_dashboard.html', stats=stats, recent_users=recent_users)

@app.route('/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    """Create a new quiz"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    form = QuizForm()
    if form.validate_on_submit():
        quiz = Quiz(
            title=form.title.data,
            description=form.description.data,
            time_limit=form.time_limit.data,
            proctoring_enabled=form.proctoring_enabled.data,
            creator_id=current_user.id
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz created successfully! Now add questions to your quiz.', 'success')
        return redirect(url_for('edit_quiz', quiz_id=quiz.id))
    
    return render_template('create_quiz.html', form=form)

@app.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    """Edit quiz and manage questions"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied. You can only edit your own quizzes.', 'error')
        return redirect(url_for('host_dashboard'))
    
    form = QuizForm(obj=quiz)
    question_form = QuestionForm()
    
    if form.validate_on_submit() and 'update_quiz' in request.form:
        quiz.title = form.title.data
        quiz.description = form.description.data
        quiz.time_limit = form.time_limit.data
        quiz.proctoring_enabled = form.proctoring_enabled.data
        quiz.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('edit_quiz', quiz_id=quiz.id))
    
    return render_template('edit_quiz.html', quiz=quiz, form=form, question_form=question_form)

@app.route('/quiz/<int:quiz_id>/add_question', methods=['POST'])
@login_required
def add_question(quiz_id):
    """Add a question to quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('host_dashboard'))
    
    question_text = request.form.get('question_text')
    question_type = request.form.get('question_type', 'multiple_choice')
    points = int(request.form.get('points', 1))
    
    if not question_text:
        flash('Question text is required.', 'error')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))
    
    question = Question(
        quiz_id=quiz_id,
        question_text=question_text,
        question_type=question_type,
        points=points,
        order=len(quiz.questions)
    )
    
    db.session.add(question)
    db.session.commit()
    
    # Add options for multiple choice questions
    if question_type == 'multiple_choice':
        for i in range(4):  # Default 4 options
            option_text = request.form.get(f'option_{i}')
            is_correct = request.form.get(f'correct_{i}') == 'on'
            
            if option_text:
                option = QuestionOption(
                    question_id=question.id,
                    option_text=option_text,
                    is_correct=is_correct,
                    order=i
                )
                db.session.add(option)
    
    elif question_type == 'true_false':
        # Add True/False options
        true_option = QuestionOption(
            question_id=question.id,
            option_text='True',
            is_correct=request.form.get('correct_answer') == 'true',
            order=0
        )
        false_option = QuestionOption(
            question_id=question.id,
            option_text='False',
            is_correct=request.form.get('correct_answer') == 'false',
            order=1
        )
        db.session.add(true_option)
        db.session.add(false_option)
    
    db.session.commit()
    flash('Question added successfully!', 'success')
    return redirect(url_for('edit_quiz', quiz_id=quiz_id))

@app.route('/quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    """View quiz details"""
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz_list.html', quiz=quiz)

@app.route('/quiz/<int:quiz_id>/take')
@login_required
def take_quiz(quiz_id):
    """Take a quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not quiz.is_active:
        flash('This quiz is not currently active.', 'error')
        return redirect(url_for('participant_dashboard'))
    
    # Check if user already has an active attempt
    existing_attempt = QuizAttempt.query.filter_by(
        participant_id=current_user.id,
        quiz_id=quiz_id,
        status='in_progress'
    ).first()
    
    if existing_attempt:
        return redirect(url_for('continue_quiz', attempt_id=existing_attempt.id))
    
    # Create new attempt
    attempt = QuizAttempt(
        participant_id=current_user.id,
        quiz_id=quiz_id
    )
    
    db.session.add(attempt)
    db.session.commit()
    
    return redirect(url_for('continue_quiz', attempt_id=attempt.id))

@app.route('/attempt/<int:attempt_id>')
@login_required
def continue_quiz(attempt_id):
    """Continue taking a quiz"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.participant_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('participant_dashboard'))
    
    if attempt.status != 'in_progress':
        flash('This quiz attempt has already been completed.', 'error')
        return redirect(url_for('quiz_results', attempt_id=attempt_id))
    
    quiz = attempt.quiz
    questions = quiz.questions
    
    # Get existing answers
    existing_answers = {answer.question_id: answer for answer in attempt.answers}
    
    return render_template('take_quiz.html', 
                         attempt=attempt, 
                         quiz=quiz, 
                         questions=questions,
                         existing_answers=existing_answers)

@app.route('/attempt/<int:attempt_id>/submit', methods=['POST'])
@login_required
def submit_quiz(attempt_id):
    """Submit quiz answers"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.participant_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('participant_dashboard'))
    
    if attempt.status != 'in_progress':
        flash('This quiz has already been submitted.', 'error')
        return redirect(url_for('quiz_results', attempt_id=attempt_id))
    
    quiz = attempt.quiz
    
    # Process answers
    for question in quiz.questions:
        answer_key = f'question_{question.id}'
        
        # Check if answer already exists
        existing_answer = Answer.query.filter_by(
            attempt_id=attempt_id,
            question_id=question.id
        ).first()
        
        if existing_answer:
            # Update existing answer
            answer = existing_answer
        else:
            # Create new answer
            answer = Answer(
                attempt_id=attempt_id,
                question_id=question.id
            )
        
        if question.question_type == 'multiple_choice' or question.question_type == 'true_false':
            selected_option_id = request.form.get(answer_key)
            if selected_option_id:
                answer.selected_option_id = int(selected_option_id)
                selected_option = QuestionOption.query.get(selected_option_id)
                answer.is_correct = selected_option.is_correct if selected_option else False
            else:
                answer.is_correct = False
        
        elif question.question_type == 'text':
            answer.text_answer = request.form.get(answer_key, '')
            # For text answers, manual grading would be needed
            answer.is_correct = None
        
        db.session.add(answer)
    
    # Mark attempt as completed
    attempt.completed_at = datetime.utcnow()
    attempt.status = 'completed'
    attempt.calculate_score()
    
    db.session.commit()
    
    flash('Quiz submitted successfully!', 'success')
    return redirect(url_for('quiz_results', attempt_id=attempt_id))

@app.route('/results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    """View quiz results"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.participant_id != current_user.id and attempt.quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    quiz = attempt.quiz
    questions = quiz.questions
    answers = {answer.question_id: answer for answer in attempt.answers}
    
    return render_template('quiz_results.html', 
                         attempt=attempt, 
                         quiz=quiz, 
                         questions=questions,
                         answers=answers)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if username is taken by another user
        if form.username.data != current_user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already taken.', 'error')
                return render_template('profile.html', form=form)
        
        # Check if email is taken by another user
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already registered.', 'error')
                return render_template('profile.html', form=form)
        
        # Update profile
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Update password if provided
        if form.current_password.data and form.new_password.data:
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'error')
                return render_template('profile.html', form=form)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', form=form)

# API endpoints for proctoring
@app.route('/api/proctoring/event', methods=['POST'])
@login_required
def log_proctoring_event():
    """Log a proctoring event"""
    data = request.get_json()
    
    if not data or 'attempt_id' not in data or 'event_type' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    attempt = QuizAttempt.query.get(data['attempt_id'])
    if not attempt or attempt.participant_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    event = ProctoringEvent(
        attempt_id=data['attempt_id'],
        event_type=data['event_type'],
        details=data.get('details', ''),
        severity=data.get('severity', 'low')
    )
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/quiz/<int:quiz_id>/questions')
@login_required
def get_quiz_questions(quiz_id):
    """Get quiz questions for AJAX loading"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    questions = []
    for question in quiz.questions:
        question_data = {
            'id': question.id,
            'text': question.question_text,
            'type': question.question_type,
            'points': question.points,
            'options': []
        }
        
        for option in question.options:
            question_data['options'].append({
                'id': option.id,
                'text': option.option_text,
                'is_correct': option.is_correct
            })
        
        questions.append(question_data)
    
    return jsonify({'questions': questions})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
