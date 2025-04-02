import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Notebook(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'Notebooks'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    model = sqlalchemy.Column(sqlalchemy.String)  # название модели
    company = sqlalchemy.Column(sqlalchemy.String)  # компания-производитель (honor, apple)
    price = sqlalchemy.Column(sqlalchemy.Integer)
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                      default=datetime.datetime.now)  # дата создания ноутбука
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship("User", back_populates="notebooks")  # создаём ассоциацию с пользователем

    def check_password(self, passw):
        if passw == self.hashed_password:
            return True
        return False
