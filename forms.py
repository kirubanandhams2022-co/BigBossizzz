from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SelectField, IntegerField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from wtforms.widgets import TextArea

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=4, max=20, message='Username must be between 4 and 20 characters')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('participant', 'Participant'),
        ('host', 'Host')
    ], validators=[DataRequired()])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class QuizForm(FlaskForm):
    title = StringField('Quiz Title', validators=[
        DataRequired(), 
        Length(max=200, message='Title cannot exceed 200 characters')
    ])
    description = TextAreaField('Description', widget=TextArea())
    time_limit = IntegerField('Time Limit (minutes)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=300, message='Time limit must be between 1 and 300 minutes')
    ], default=60)
    proctoring_enabled = BooleanField('Enable Proctoring', default=True)
    shuffle_options = BooleanField('Shuffle Answer Options for Each Participant', default=True)
    quiz_file = FileField('Upload Quiz File (TXT/CSV format)', validators=[
        FileAllowed(['txt', 'csv'], 'Only TXT and CSV files allowed!')
    ])
    create_from_file = BooleanField('Create Quiz from Uploaded File', default=False)

class QuestionOptionForm(FlaskForm):
    option_text = StringField('Option', validators=[DataRequired(), Length(max=500)])
    is_correct = BooleanField('Correct Answer')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question', validators=[DataRequired()], widget=TextArea())
    question_type = SelectField('Question Type', choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('text', 'Text Answer')
    ], default='multiple_choice')
    points = IntegerField('Points', validators=[
        DataRequired(), 
        NumberRange(min=1, max=10, message='Points must be between 1 and 10')
    ], default=1)
    options = FieldList(FormField(QuestionOptionForm), min_entries=4)

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=4, max=20, message='Username must be between 4 and 20 characters')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match')
    ])
