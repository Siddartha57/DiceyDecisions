from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, IntegerField, TextAreaField, RadioField
from wtforms.validators import Length, DataRequired, Email, EqualTo, ValidationError
from web.models import User

class Login(FlaskForm):
    username= StringField('Username',validators=[DataRequired(),Length(4,20)])
    password = PasswordField('Password',validators=[DataRequired(),Length(6,30)])
    submit = SubmitField('submit')

class Register(FlaskForm):
    username= StringField('Username',validators=[DataRequired(),Length(4,20)])
    email = EmailField('Email address', validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(6,30)])
    confirm_password = PasswordField('Confirm Password',validators=[EqualTo('password')])
    submit = SubmitField('submit')

class CreateRoomForm(FlaskForm):
    title = StringField('Room Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description (optional)', validators=[Length(max=500)])
    submit = SubmitField('Create Room')

class JoinRoomForm(FlaskForm):
    room_code = StringField('Enter Room Code', validators=[DataRequired(), Length(min=6, max=8)])
    submit = SubmitField('Join Room')

class SubmitOptionForm(FlaskForm):
    text = StringField('Add an Option', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Submit Option')

class VoteForm(FlaskForm):
    selected_option = RadioField('Choose an option', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Vote')

