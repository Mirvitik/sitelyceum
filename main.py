# в файл .env в переменную PASSWORD вставьте ключ, который я прислал в чате для работы email рассылки
import random
from werkzeug.security import generate_password_hash
from flask import Flask, request, render_template, redirect, send_from_directory, session
import os
from dotenv import load_dotenv
import datetime
from data import db_session
from data.users import User
from data.notebooks import Notebook
from forms.notebookform import NotebookForm
from mail_sender import send_mail
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from flask_restful import abort
from forms.loginform import LoginForm
from forms.regform import RegForm
from forms.codeform import CodeForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LfTle8qAAAAAEDmrvrsjVkNClyDNl7-p6m1OzDU'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LfTle8qAAAAADmIekuS60zE3LrpnHlkwM1x9FiF'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)

login_manager = LoginManager()
login_manager.init_app(app)
load_dotenv()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    items = db_sess.query(Notebook).all()
    session['items'] = [el.to_dict(only=('id', 'model', 'company', 'price', 'description')) for el in items]
    db_sess.close()
    return render_template('index.html', items=session['items'])


@app.route('/mail', methods=['GET'])  # пример email рассылки. Вставьте почту в поле
def get_form():
    return render_template('mail_me.html')


@app.route('/mail', methods=['POST'])
def post_form():
    email = request.values.get('email')
    if send_mail(email, 'test', 'test_text', ['1.png']):
        print('yes')
        return f'Письмо отправлено на адрес {email}'
    return f'Во время отправки письма на адрес {email}'


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit() and bool(db_sess.query(User).filter(User.email == form.email.data).first()):
        if bool(db_sess.query(User).filter(User.email == form.email.data).first()):
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user.check_password(form.password.data):
                print(db_sess.query(User).filter(User.email == form.email.data).first())
                login_user(db_sess.query(User).filter(User.email == form.email.data).first(),
                           remember=form.remember_me.data)
                db_sess.close()
                return redirect('/success')
            else:
                db_sess.close()
                return render_template('login.html', title='Авторизация', form=form,
                                       message='Неверный логин или пароль')
        else:
            db_sess.close()
            return render_template('login.html', title='Авторизация', form=form, message='Неверный логин или пароль')
    db_sess.close()
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    form = RegForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit() and form.password.data == form.password2.data:
        if db_sess.query(User).filter(User.email == form.email.data).first() is not None:
            return render_template('reg.html', form=form, title='Зарегистрируйся бесплатно',
                                   message='Пользователь с такой почтой уже зарегистрирован')
        if request.method == 'POST':
            # check if the post request has the file part
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                # if user does not select file, browser also
                # submit a empty part without filename
                if file.filename != '':
                    maxid = db_sess.query(User).order_by(
                        User.id.desc()).first()
                    if maxid is None:
                        maxid = 1
                    else:
                        maxid += 1
                    if file.filename.endswith('png'):
                        file.save(os.path.join('static/img/avatars', f'{maxid}.png'))
                    elif file.filename.endswith('jpeg'):
                        file.save(os.path.join('static/img/avatars', f'{maxid}.jpeg'))
                    elif file.filename.endswith('jpg'):
                        file.save(os.path.join('static/img/avatars', f'{maxid}.jpeg'))
        session['code'] = ''.join(
            map(str, [random.randint(0, 9) for _ in range(6)]))  # создаём код верификации в session
        send_mail(form.email.data, 'code', session['code'], [])
        session['remember'] = form.remember_me.data
        session['email'] = form.email.data
        session['surname'] = form.surname.data
        session['name'] = form.name.data
        session['hashed_password'] = generate_password_hash(form.password.data)
        logout_user()
        return redirect('/codeverify')
    return render_template('reg.html', form=form, title='Зарегистрируйся бесплатно')


@app.route('/codeverify', methods=['GET', 'POST'])  # пользователь вводит код из имейла
def codeverify():
    form = CodeForm()
    if form.validate_on_submit() and form.code.data == session['code']:
        db_sess = db_session.create_session()
        user = User(surname=session['surname'],
                    name=session['name'],
                    email=session['email'],
                    hashed_password=session['hashed_password']
                    )
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=session['remember'])
        return redirect('/')
    return render_template('code.html', form=form)


@app.route('/notebook_add', methods=['GET', 'POST'])
@login_required
def notebook_add():
    form = NotebookForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        notebook = Notebook(model=form.model.data,
                            company=form.company.data,
                            price=form.price.data,
                            description=form.description.data,
                            user_id=current_user.id)
        current_user.notebooks.append(notebook)
        db_sess.merge(current_user)
        db_sess.commit()
        items = db_sess.query(Notebook).all()
        session['items'] = [el.to_dict(only=('id', 'model', 'company', 'price', 'description')) for el in items]
        db_sess.close()
        return redirect('/')
    return render_template('notebookadd.html', form=form)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/news')
def news():
    return render_template('news.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/profile/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()

    if not user:
        return render_template('404.html'), 404  # User not found

    return render_template('profile.html', user=user)


@app.route('/profile/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()

    if not user:
        return render_template('404.html'), 404  # User not found

    form = RegForm()  # Assuming RegForm is used for updating user info

    if request.method == 'POST' and form.validate_on_submit():
        user.name = form.name.data
        user.surname = form.surname.data
        user.email = form.email.data

        if form.password.data:
            user.hashed_password = generate_password_hash(form.password.data)

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file.filename != '':
                maxid = db_sess.query(User).order_by(User.id.desc()).first()
                if maxid is None:
                    maxid = 1
                else:
                    maxid += 1
                if file.filename.endswith('png'):
                    file.save(os.path.join('static/img/avatars', f'{maxid}.png'))
                elif file.filename.endswith('jpeg') or file.filename.endswith('jpg'):
                    file.save(os.path.join('static/img/avatars', f'{maxid}.jpeg'))

        db_sess.commit()
        return redirect(f'/profile/{user.id}')

    # Pre-fill the form with current user's data
    form.name.data = user.name
    form.surname.data = user.surname
    form.email.data = user.email

    return render_template('edit_profile.html', title='Edit Profile', form=form, user=user)


if __name__ == '__main__':
    db_session.global_init('db/users.db')
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=5000)
