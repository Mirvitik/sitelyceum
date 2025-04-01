# в файл .env в переменную PASSWORD вставьте ключ, который я прислал в чате для работы email рассылки
import random

from flask import Flask, request, render_template, redirect, send_from_directory, session
import os
from dotenv import load_dotenv
import datetime
from data import db_session
from data.users import User
from mail_sender import send_mail
from flask_login import LoginManager, login_required, logout_user, login_user
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
    return render_template('index.html')


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
    if form.validate_on_submit() and bool(db_sess.query(User).filter(User.email == form.email.data,
                                                                     User.hashed_password == form.password.data).first()):
        print(db_sess.query(User).filter(User.email == form.email.data).first())
        login_user(db_sess.query(User).filter(User.email == form.email.data).first(), remember=form.remember_me.data)
        return redirect('/success')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    form = RegForm()
    if form.validate_on_submit() and form.password.data == form.password2.data:
        session['code'] = ''.join(
            map(str, [random.randint(0, 9) for _ in range(6)]))  # создаём код верификации в session
        send_mail(form.email.data, 'code', session['code'], [])
        session['remember'] = form.remember_me.data
        session['email'] = form.email.data
        user = User(surname=form.surname.data,
                    name=form.name.data,
                    email=form.email.data,
                    hashed_password=form.password.data
                    )
        db_sess = db_session.create_session()
        db_sess.add(user)
        db_sess.commit()
        logout_user()
        return redirect('/codeverify')
    return render_template('reg.html', form=form, title='Зарегистрируйся бесплатно')


@app.route('/codeverify', methods=['GET', 'POST'])
def codeverify():
    form = CodeForm()
    if form.validate_on_submit() and form.code.data == session['code']:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == session['email']).first()
        login_user(user, remember=session['remember'])
        return redirect('/')
    return render_template('code.html', form=form)


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
    return "Page not found. Go back and try again.", 404


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


if __name__ == '__main__':
    db_session.global_init('db/users.db')
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=5000)
