from wtforms import Form, BooleanField, TextField, PasswordField, validators

class RegistrationForm(Form):
    username = TextField('Username', [validators.Required()])
    email = TextField('Email Address')
    password = PasswordField('New Password', [validators.Required()])


class LoginForm(Form):
    username = TextField('Enter Username', [validators.Required()])
    password = PasswordField('Enter Password', [validators.Required()])



