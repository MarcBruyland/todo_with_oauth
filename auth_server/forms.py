from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = StringField("User name", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    client_id = HiddenField("client_id", validators=[DataRequired()])
    redirect_url = HiddenField("redirect_url", validators=[DataRequired()])
    submit = SubmitField('Submit')



