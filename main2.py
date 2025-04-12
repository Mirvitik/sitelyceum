from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import secrets
from data import db_session
from data.db_session import SqlAlchemyBase
from mail_sender import send_mail
from functools import wraps
import os
from data.users import User
from data.notebooks import Notebook
from api import api

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.register_blueprint(api, url_prefix='/api/v1')

RECAPTCHA_SITE_KEY = "6LfTle8qAAAAAEDmrvrsjVkNClyDNl7-p6m1OzDU"
RECAPTCHA_SECRET_KEY = "6LfTle8qAAAAADmIekuS60zE3LrpnHlkwM1x9FiF"

os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'notebooks'), exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def init_db():
    db_session.global_init("db/database.db")
    db_sess = db_session.create_session()

    from data.users import User
    from data.notebooks import Notebook
    SqlAlchemyBase.metadata.create_all(db_sess.bind)
    db_sess.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    notebooks = db_sess.query(Notebook).all()
    db_sess.close()
    return render_template('main.html', notebooks=notebooks)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == email).first()
        db_sess.close()

        if user and check_password_hash(user.password_hash, password):
            if not user.email_verified:
                flash('Пожалуйста, подтвердите ваш email перед входом', 'warning')
                verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
                session['verification_code'] = verification_code
                session['verification_email'] = email
                if send_mail(email, 'Подтверждение регистрации в LightWeb',
                             f'Ваш код подтверждения: {verification_code}', []):
                    flash('Код подтверждения отправлен на ваш email', 'info')
                    return redirect(url_for('verify_email'))
                else:
                    flash('Ошибка отправки кода подтверждения', 'danger')
                return redirect(url_for('verify_email'))

            session['user_id'] = user.id
            session['user_name'] = f"{user.first_name} {user.last_name}"
            session['email_verified'] = True

            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('profile'))

        flash('Неверный email или пароль', 'danger')

    return render_template('login2.html', recaptcha_site_key=RECAPTCHA_SITE_KEY)


@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        if 'resend' in request.form:
            email = session.get('verification_email')
            if not email:
                flash('Сессия истекла, пожалуйста, начните процесс заново', 'danger')
                return redirect(url_for('register'))
            verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            session['verification_code'] = verification_code
            if send_mail(email, 'Код подтверждения LightWeb',
                         f'Ваш код подтверждения: {verification_code}', []):
                flash('Код подтверждения отправлен повторно', 'info')
            else:
                flash('Ошибка отправки кода подтверждения', 'danger')
            return redirect(url_for('verify_email'))

        verification_code = request.form.get('verification-code')
        stored_code = session.get('verification_code')
        if verification_code == stored_code:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == session.get('verification_email')).first()
            if user:
                user.email_verified = True
                db_sess.commit()
                session['email_verified'] = True
                session.pop('verification_code', None)
                session.pop('verification_email', None)
                flash('Email успешно подтвержден! Теперь вы можете войти в систему', 'success')
                return redirect(url_for('login'))
        flash('Неверный код подтверждения', 'danger')
    return render_template('verify_email.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first-name')
        last_name = request.form.get('last-name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if not all([first_name, last_name, email, phone, password, confirm_password]):
            flash('Пожалуйста, заполните все поля', 'danger')
        elif password != confirm_password:
            flash('Пароли не совпадают', 'danger')
        else:
            db_sess = db_session.create_session()
            try:
                if db_sess.query(User).filter(User.email == email).first():
                    flash('Пользователь с таким email уже существует', 'danger')
                    return redirect(url_for('register'))

                verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
                session['verification_code'] = verification_code
                session['verification_email'] = email

                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    password_hash=generate_password_hash(password),
                    email_verified=False
                )
                db_sess.add(user)
                db_sess.commit()

                if send_mail(email, 'Подтверждение регистрации в LightWeb',
                             f'Ваш код подтверждения: {verification_code}', []):
                    flash('Код подтверждения отправлен на ваш email', 'info')
                    return redirect(url_for('verify_email'))
                else:
                    flash('Ошибка отправки кода подтверждения', 'danger')

            except Exception as e:
                db_sess.rollback()
                flash(f'Ошибка при регистрации: {str(e)}', 'danger')
            finally:
                db_sess.close()

    return render_template('reg2.html', recaptcha_site_key=RECAPTCHA_SITE_KEY)


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(session['user_id'])

    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone' in data:
        user.phone = data['phone']

    db_sess.commit()
    db_sess.close()

    return {'success': True}


@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        flash('Файл не выбран', 'danger')
        return redirect(url_for('profile'))

    file = request.files['avatar']
    if file.filename == '':
        flash('Файл не выбран', 'danger')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        filename = f"user_{session['user_id']}.{file.filename.rsplit('.', 1)[1].lower()}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', filename)
        file.save(filepath)

        db_sess = db_session.create_session()
        user = db_sess.query(User).get(session['user_id'])
        user.avatar = filename
        db_sess.commit()
        db_sess.close()

        flash('Аватар успешно обновлен', 'success')
    else:
        flash('Недопустимый формат файла', 'danger')

    return redirect(url_for('profile'))


@app.route('/add_notebook', methods=['GET', 'POST'])
@login_required
def add_notebook():
    if request.method == 'POST':
        model = request.form.get('model')
        company = request.form.get('company')
        price = request.form.get('price')
        description = request.form.get('description')
        file = request.files.get('image')

        if not all([model, company, price]):
            flash('Пожалуйста, заполните все обязательные поля', 'danger')
            return redirect(url_for('add_notebook'))

        try:
            db_sess = db_session.create_session()
            notebook = Notebook(
                model=model,
                company=company,
                price=int(price),
                description=description,
                user_id=session['user_id']
            )
            db_sess.add(notebook)
            db_sess.commit()
            # Обработка изображения
            if file and allowed_file(file.filename):
                filename = f"notebook_{notebook.id}.{file.filename.rsplit('.', 1)[1].lower()}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'notebooks', filename)
                file.save(filepath)
                notebook.image_path = filename

            db_sess.commit()
            flash('Ноутбук успешно добавлен', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при добавлении ноутбука: {str(e)}', 'danger')
        finally:
            db_sess.close()

    return render_template('add_notebook.html')


@app.route('/edit_notebook/<int:notebook_id>', methods=['GET', 'POST'])
@login_required
def edit_notebook(notebook_id):
    db_sess = db_session.create_session()
    notebook = db_sess.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == session['user_id']
    ).first()

    if not notebook:
        flash('Ноутбук не найден', 'danger')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        notebook.model = request.form.get('model')
        notebook.company = request.form.get('company')
        notebook.price = int(request.form.get('price'))
        notebook.description = request.form.get('description')

        file = request.files.get('image')
        if file and allowed_file(file.filename):
            # Удаляем старое изображение, если оно есть
            if notebook.image_path:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], 'notebooks', notebook.image_path)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Сохраняем новое изображение
            filename = f"notebook_{notebook.id}.{file.filename.rsplit('.', 1)[1].lower()}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'notebooks', filename)
            file.save(filepath)
            notebook.image_path = filename

        db_sess.commit()
        flash('Ноутбук успешно обновлен', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_notebook.html', notebook=notebook)


@app.route('/delete_notebook/<int:notebook_id>', methods=['POST'])
@login_required
def delete_notebook(notebook_id):
    db_sess = db_session.create_session()
    notebook = db_sess.query(Notebook).filter(
        Notebook.id == notebook_id,
        Notebook.user_id == session['user_id']
    ).first()

    if notebook:
        db_sess.delete(notebook)
        db_sess.commit()
        flash('Ноутбук успешно удален', 'success')
    else:
        flash('Ноутбук не найден или у вас нет прав на его удаление', 'danger')

    db_sess.close()
    return redirect(url_for('profile'))


@app.route('/profile')
@login_required
def profile():
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(session['user_id'])
    notebooks = db_sess.query(Notebook).filter(Notebook.user_id == session['user_id']).all()
    db_sess.close()
    return render_template('profile_full.html', user=user, notebooks=notebooks)


# Добавим метод для получения изображений
@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404_.html'), 404


@app.route('/resend_code', methods=['POST'])
def resend_code():
    if 'verification_email' not in session:
        return {'success': False, 'message': 'Сессия истекла'}, 400

    email = session['verification_email']
    verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    session['verification_code'] = verification_code

    if send_mail(email, 'Код подтверждения LightWeb',
                 f'Ваш код подтверждения: {verification_code}', []):
        return {'success': True}
    else:
        return {'success': False, 'message': 'Ошибка отправки email'}, 500


if __name__ == '__main__':
    init_db()
    if not os.path.exists('db'):
        os.makedirs('db')
    app.run(debug=True)
