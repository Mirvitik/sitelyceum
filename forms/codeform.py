from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class CodeForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField('Войти')
