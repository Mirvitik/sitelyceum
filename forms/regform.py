from flask_wtf import FlaskForm, RecaptchaField
from wtforms import EmailField
from wtforms.fields.simple import PasswordField, SubmitField, StringField, TelField
from wtforms.validators import DataRequired


class RegForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired()])
    phone = TelField('Телефон', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField('Войти')
