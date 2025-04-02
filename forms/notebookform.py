from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired


class NotebookForm(FlaskForm):
    model = StringField('Модель', validators=[DataRequired()])  # название модели
    company = StringField('Компания-производитель',
                          validators=[DataRequired()])  # компания-производитель (honor, apple)
    price = IntegerField('Цена', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    submit = SubmitField('Добавить ноутбук')
