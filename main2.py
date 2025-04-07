import datetime
import os
from flask import Flask, request, render_template, redirect, send_from_directory, session


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LfTle8qAAAAAEDmrvrsjVkNClyDNl7-p6m1OzDU'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LfTle8qAAAAADmIekuS60zE3LrpnHlkwM1x9FiF'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)


@app.route('/')
@app.route('/index')
def index():
    return render_template('main.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=5000)
