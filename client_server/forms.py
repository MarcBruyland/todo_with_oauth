from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, PasswordField, DateField, HiddenField
from wtforms.validators import DataRequired, Optional


class TodoForm(FlaskForm):
    id = IntegerField('Todo id')
    todo = StringField('Todo', validators=[DataRequired()])
    due = DateField('Due Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Submit')


