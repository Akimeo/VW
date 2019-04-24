from flask import Flask, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from add_news import AddNewsForm
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError


def user_check(form, field):
    if form.username.data:
        check = UsersModel.query.filter_by(
            user_name=form.username.data).first()
        if check:
            if not check_password_hash(check.password_hash, field.data):
                raise ValidationError(
                    'Пользователь не существует или неверный пароль')
        else:
            raise ValidationError(
                'Пользователь не существует или неверный пароль')


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[
                           DataRequired('Заполните это поле')])
    password = PasswordField(
        'Пароль', validators=[
            DataRequired('Заполните это поле'), user_check])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


def name_check(form, field):
    if UsersModel.query.filter_by(user_name=field.data).first():
        raise ValidationError('Имя недоступно')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[
                           DataRequired('Заполните это поле'), name_check])
    password = PasswordField(
        'Пароль', validators=[
            DataRequired('Заполните это поле')])
    submit = SubmitField('Зарегистрироваться')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class UsersModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), unique=False, nullable=False)


class NewsModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=False, nullable=False)
    content = db.Column(db.String(1000), unique=False, nullable=False)
    user_id = db.Column(db.Integer, unique=False, nullable=False)


@app.route('/')
@app.route('/index')
def index():
    if 'username' not in session:
        return redirect('/login')
    if session['news_sort_type'] == 'id':
        news = list(NewsModel.query.filter_by(
            user_id=session['user_id']).order_by(NewsModel.id).all())
    else:
        news = list(NewsModel.query.filter_by(
            user_id=session['user_id']).order_by(NewsModel.title).all())
    return render_template(
        'index.html', title='ВВаркрафте',
        username=session['username'], news=news)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = UsersModel(
            user_name=form.username.data,
            password_hash=generate_password_hash(form.password.data))
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('registration.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session['username'] = form.username.data
        session['user_id'] = UsersModel.query.filter_by(
            user_name=session['username']).first().id
        session['news_sort_type'] = 'id'
        return redirect('/index')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    session.pop('username', 0)
    session.pop('user_id', 0)
    session.pop('news_sort_type')
    return redirect('/login')


@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if 'username' not in session:
        return redirect('/login')
    form = AddNewsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new = NewsModel(title=title, content=content,
                        user_id=session['user_id'])
        db.session.add(new)
        db.session.commit()
        return redirect('/index')
    return render_template('add_news.html', title='Добавление новости',
                           form=form, username=session['username'])


@app.route('/sort_news/<sort_type>', methods=['GET'])
def sort_news(sort_type):
    if 'username' not in session:
        return redirect('/login')
    session['news_sort_type'] = sort_type
    return redirect('/index')


@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    new = NewsModel.query.filter_by(id=news_id).first()
    db.session.delete(new)
    db.session.commit()
    return redirect('/index')


@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect('/login')
    if session['username'] != 'admin':
        return 'Доступ закрыт'
    data = list(map(lambda x: [x.user_name, str(len(
        NewsModel.query.filter_by(user_id=x.id).all()))],
        UsersModel.query.all()))
    return render_template(
        'admin.html', title='Информация о пользователях',
        username='admin', data=data)


if __name__ == '__main__':
    db.create_all()
    app.run(port=8080, host='127.0.0.1')
