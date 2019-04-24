from flask import Flask, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from add_news import AddNewsForm
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     SelectField)
from wtforms.validators import DataRequired, ValidationError
import os.path
import logging
from PIL import Image


logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vwb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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


def pasRep_check(form, filed):
    if form.password.data != form.password_rep.data:
        raise ValidationError('Пароли не повторяются')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[
                           DataRequired('Заполните это поле'), name_check])
    password = PasswordField(
        'Пароль', validators=[
            DataRequired('Заполните это поле')])
    password_rep = PasswordField('Повторите пароль',
                                 validators=[
                                     DataRequired('Заполните это поле'),
                                     pasRep_check])
    fraction = SelectField('Фракция', choices=[(
        None, "-"), ("Альянс", "Альянс"), ("Орда", "Орда")])
    submit = SubmitField('Зарегистрироваться')


class UsersModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), unique=False, nullable=False)
    fraction = db.Column(db.String(6), unique=False, nullable=False)


class NewsModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=False, nullable=False)
    content = db.Column(db.String(1000), unique=False, nullable=False)
    user_id = db.Column(db.Integer, unique=False, nullable=False)


def getAvat(user):
    if os.path.exists('static/img/' + user.user_name + '_av.png'):
        return 'static/img/' + user.user_name + '_av.png'
    else:
        return 'static/img/default_av.png'


def resize(file):
    outfile = file.split('.')[0] + "_64x64.thumbnail"
    try:
        im = Image.open(file)
        im.thumbnail((64, 64), Image.ANTIALIAS)
        im.save(outfile, "JPEG")
    except IOError:
        print("cannot create thumbnail for '%s'" % file)


def getNews():
    if session['news_sort_type']:
        news = list(NewsModel.query.filter_by(
            user_id=session['user_id']).order_by(NewsModel.id).all())
    else:
        news = list(NewsModel.query.filter_by(
            user_id=session['user_id']).order_by(NewsModel.title).all())
    if session["reverse"]:
        news = reversed(news)
    return news


@app.route('/')
@app.route('/index')
def index():
    if 'username' not in session:
        return redirect('/login')
    return render_template(
        'index.html', title='ВВаркрафте',
        username=session['username'], news=getNews())


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = UsersModel(
            user_name=form.username.data,
            password_hash=generate_password_hash(form.password.data),
            fraction=form.fraction.data)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = UsersModel.query.filter_by(
            user_name=form.username.data).first()
        session['username'] = user.user_name
        session['user_id'] = user.id
        session['news_sort_type'] = 'id'
        session['reverse'] = False
        session["pic"] = getAvat(user)
        if user.fraction == "Альянс":
            session["logo"] = "A"
        elif user.fraction == "Орда":
            session["logo"] = "H"
        else:
            session["logo"] = "D"
        return redirect('/index')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    ses_p = ['username', 'user_id', 'news_sort_type', 'reverse', 'pic', 'logo']
    for item in ses_p:
        session.pop(item)
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
    if sort_type == "title":
        session['news_sort_type'] = True
    elif sort_type == "id":
        session['news_sort_type'] = False
    elif sort_type == "straight":
        session['reverse'] = False
    elif sort_type == "reverse":
        session['reverse'] = True
    return redirect('/index')


@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    new = NewsModel.query.filter_by(id=news_id).first()
    db.session.delete(new)
    db.session.commit()
    return redirect('/index')


@app.route('/user_list')
def user_list():
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


@app.route('/<int:user_id>', methods=['GET'])
def selfPage(user_id):
    user = UsersModel.query.filter_by(id=user_id).first()
    if not user:
        return "Пользователь не найден"
    pic = getAvat(user)
    return render_template(
        "userpage.html",
        title="Страница пользователя " + session["username"],
        pic=pic, news=getNews())


if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    try:
        admin = UsersModel(user_name='admin',
                           password_hash=generate_password_hash('admin'),
                           fraction="Альянс")
        db.session.add(admin)
        db.session.commit()
    except Exception as e:
        print(e)
    app.run(port=8080, host='127.0.0.1')
