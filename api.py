from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from data.db_session import create_session
from data.users import User
from data.notebooks import Notebook
from functools import wraps
import datetime

api = Blueprint('api', __name__)


def login_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return jsonify({'error': 'Authentication required'}), 401

        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == auth.username).first()
        if not user or not user.check_password(auth.password):
            return jsonify({'error': 'Invalid credentials'}), 401

        return f(user, *args, **kwargs)

    return decorated_function


@api.route('/users', methods=['GET'])
def get_users():
    db_sess = create_session()
    users = db_sess.query(User).all()
    return jsonify({
        'users': [{
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'created_at': user.created_at.isoformat()
        } for user in users]
    })


@api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    db_sess = create_session()
    user = db_sess.query(User).get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone,
        'created_at': user.created_at.isoformat()
    })


@api.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not all(key in data for key in ['first_name', 'last_name', 'email', 'phone', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400

    db_sess = create_session()
    if db_sess.query(User).filter(User.email == data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        password_hash=generate_password_hash(data['password']),
        email_verified=False
    )

    db_sess.add(user)
    db_sess.commit()

    return jsonify({
        'id': user.id,
        'message': 'User created successfully'
    }), 201


@api.route('/notebooks', methods=['GET'])
def get_notebooks():
    db_sess = create_session()
    notebooks = db_sess.query(Notebook).all()

    return jsonify({
        'notebooks': [{
            'id': nb.id,
            'model': nb.model,
            'company': nb.company,
            'price': nb.price,
            'description': nb.description,
            'image_url': nb.get_image_url(),
            'created_at': nb.created_at.isoformat(),
            'user_id': nb.user_id
        } for nb in notebooks]
    })


@api.route('/notebooks/<int:notebook_id>', methods=['GET'])
def get_notebook(notebook_id):
    db_sess = create_session()
    notebook = db_sess.query(Notebook).get(notebook_id)
    if not notebook:
        return jsonify({'error': 'Notebook not found'}), 404

    return jsonify({
        'id': notebook.id,
        'model': notebook.model,
        'company': notebook.company,
        'price': notebook.price,
        'description': notebook.description,
        'image_url': notebook.get_image_url(),
        'created_at': notebook.created_at.isoformat(),
        'user_id': notebook.user_id
    })


@api.route('/notebooks', methods=['POST'])
@login_required_api
def create_notebook(user):
    data = request.get_json()
    if not all(key in data for key in ['model', 'company', 'price']):
        return jsonify({'error': 'Missing required fields'}), 400

    notebook = Notebook(
        model=data['model'],
        company=data['company'],
        price=data['price'],
        description=data.get('description', ''),
        user_id=user.id
    )

    db_sess = create_session()
    db_sess.add(notebook)
    db_sess.commit()

    return jsonify({
        'id': notebook.id,
        'message': 'Notebook created successfully'
    }), 201


@api.route('/notebooks/<int:notebook_id>', methods=['PUT'])
@login_required_api
def update_notebook(user, notebook_id):
    db_sess = create_session()
    notebook = db_sess.query(Notebook).get(notebook_id)
    if not notebook:
        return jsonify({'error': 'Notebook not found'}), 404

    if notebook.user_id != user.id:
        return jsonify({'error': 'Not authorized to update this notebook'}), 403

    data = request.get_json()
    notebook.model = data.get('model', notebook.model)
    notebook.company = data.get('company', notebook.company)
    notebook.price = data.get('price', notebook.price)
    notebook.description = data.get('description', notebook.description)

    db_sess.commit()
    return jsonify({'message': 'Notebook updated successfully'})


@api.route('/notebooks/<int:notebook_id>', methods=['DELETE'])
@login_required_api
def delete_notebook(user, notebook_id):
    db_sess = create_session()
    notebook = db_sess.query(Notebook).get(notebook_id)
    if not notebook:
        return jsonify({'error': 'Notebook not found'}), 404

    if notebook.user_id != user.id:
        return jsonify({'error': 'Not authorized to delete this notebook'}), 403

    db_sess.delete(notebook)
    db_sess.commit()
    return jsonify({'message': 'Notebook deleted successfully'})


@api.route('/users/notebooks', methods=['GET'])
@login_required_api
def get_user_notebooks(user):
    db_sess = create_session()
    notebooks = db_sess.query(Notebook).filter(Notebook.user_id == user.id).all()

    return jsonify({
        'notebooks': [{
            'id': nb.id,
            'model': nb.model,
            'company': nb.company,
            'price': nb.price,
            'description': nb.description,
            'image_url': nb.get_image_url(),
            'created_at': nb.created_at.isoformat()
        } for nb in notebooks]
    })
