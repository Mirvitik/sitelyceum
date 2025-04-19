import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from flask import url_for


class Notebook(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'notebooks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    model = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    company = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    price = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text)
    image_path = sqlalchemy.Column(sqlalchemy.String)  # Путь к изображению
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

    user = orm.relationship('User', back_populates="notebooks")

    def get_image_url(self):
        if self.image_path:
            return url_for('static', filename=f'uploads/notebooks/{self.image_path}')
        return url_for('static', filename='img/no-image.png')