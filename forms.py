#!/usr/bin/env python

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms_sqlalchemy.fields import QuerySelectField
from models import NetworkDevice


class LoginForm(FlaskForm):
    username = StringField('User name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class ChangePassword(FlaskForm):
    password = PasswordField('Actual Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')


class AddElement(FlaskForm):
    hostname = StringField('Hostname', validators=[DataRequired()])
    management_ip = StringField('Management IP', validators=[DataRequired()])
    vendor = SelectField('Vendor', choices=[
        ('Select Vendor', 'Select Vendor...'),
        ('Brocade', 'Brocade'),
        ('Cisco Nexus', 'Cisco Nexus'),
        ('HP', 'HP')
    ], coerce=str, validators=[DataRequired()])
    net_side = SelectField('Network Side', choices=[
        ('Select Network Side', 'Select Network Side...'),
        ('Vivo I', 'Vivo I'),
        ('Vivo II', 'Vivo II')
    ], coerce=str, validators=[DataRequired()])
    tacacs_user = StringField('Tacacs User', validators=[DataRequired()])
    tacacs_pass = PasswordField('Tacacs Pass', validators=[DataRequired()])
    submit = SubmitField('Submit')


def network_device_query():
    return NetworkDevice.query


class UpdateElement(FlaskForm):
    hostname = QuerySelectField(query_factory=network_device_query, allow_blank=True, get_label='hostname')
    tacacs_user = StringField('Tacacs User', validators=[DataRequired()])
    tacacs_pass = PasswordField('Tacacs Pass', validators=[DataRequired()])
    submit = SubmitField('Update Information')


class MassiveUpdateElement(FlaskForm):
    tacacs_user = StringField('Tacacs User', validators=[DataRequired()])
    tacacs_pass = PasswordField('Tacacs Pass', validators=[DataRequired()])
    submit = SubmitField('Update Database')
