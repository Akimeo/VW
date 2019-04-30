from flask import Flask, redirect, render_template, session, request, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     SelectField, TextAreaField)
from wtforms.validators import (DataRequired, ValidationError, EqualTo,
                                StopValidation)
from flask_wtf.file import FileField, FileRequired, FileAllowed
from os.path import join, exists, abspath, dirname
from datetime import datetime
from json import loads, dumps
from time import time, ctime
import logging


logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vwb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/static/img'
apath = dirname(abspath(__file__))
forbidden_names = ['admin', 'default', 'Zaicol']
MAX_FILE_SIZE = 1024 * 1024 * 8 * 4 + 1
fracs = {
    'Альянс': 'A', 'Орда': 'H'
}
db = SQLAlchemy(app)


def user_check(form, field):
    if form.username.data:
        check = UsersModel.query.filter_by(
            user_name=form.username.data).first()
        if check:
            if not check_password_hash(check.password_hash, field.data):
                raise ValidationError(
                    'Неверный пароль')
        else:
            raise ValidationError('Такого пользователя не существует')


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
        raise ValidationError('Пользователь с таким логином уже существует')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[
                           DataRequired('Заполните это поле'), name_check])
    password = PasswordField(
        'Пароль', validators=[
            DataRequired('Заполните это поле')])
    password_rep = PasswordField('Подтверждение пароля',
                                 validators=[
                                     DataRequired('Заполните это поле'),
                                     EqualTo('password', 'Пароли не совпадают')
                                 ])
    fraction = SelectField('Фракция', choices=[(
        None, "-"), ("Альянс", "Альянс"), ("Орда", "Орда")])
    submit = SubmitField('Зарегистрироваться')


class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[
                        DataRequired('Заполните это поле')])
    content = TextAreaField('Текст новости', validators=[
                            DataRequired('Заполните это поле')])
    submit = SubmitField('Добавить')


def size_check(form, field):
    file = field.data
    file_bytes = file.read(MAX_FILE_SIZE)
    if len(file_bytes) == MAX_FILE_SIZE:
        raise StopValidation('Превышен максиммальный размер файла')


class AvatarForm(FlaskForm):
    avatar = FileField('Новый аватар', validators=[
                       FileRequired('Необходимо выбрать файл'),
                       FileAllowed(['jpg', 'png', 'gif'],
                                   'Расширение файла не является допустимым'),
                       size_check])
    submit_av = SubmitField('Сохранить')


def exist_check(form, field):
    if UsersModel.query.filter_by(user_name=field.data).first():
        raise ValidationError('Пользователь с таким логином уже существует')
    elif field.data in forbidden_names and session['user_id'] != 1:
        raise ValidationError('Использование данного имени запрещено')


class ChangeUsernameForm(FlaskForm):
    new_name = StringField('Новый логин', validators=[
                           DataRequired('Введите новый логин'),
                           exist_check])
    submit_us = SubmitField('Сохранить')


def oldpass_check(form, field):
    user = UsersModel.query.filter_by(id=session["user_id"]).first()
    if not check_password_hash(user.password_hash, field.data):
        raise ValidationError('Неверный пароль')


class ChangePasswordForm(FlaskForm):
    old_pass = PasswordField('Старый пароль', validators=[
        DataRequired('Введите старый пароль'),
        oldpass_check])
    password = PasswordField('Новый пароль', validators=[
        DataRequired('Введите новый пароль')])
    password_rep = PasswordField('Подтверждение пароля', validators=[
        DataRequired('Повторно введите новый пароль'),
        EqualTo('password', 'Пароли не совпадают')])
    submit_pass = SubmitField('Сохранить')


class UsersModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), unique=False, nullable=False)
    # hidden posts
    hdp = db.Column(db.String(), unique=False, nullable=True, default='[]')
    fraction = db.Column(db.String(6), unique=False, nullable=False)
    regdate = db.Column(db.DateTime, unique=False, nullable=False)
    coguild = db.Column(db.String(), unique=False, nullable=True, default='[]')
    av_type = db.Column(db.String(4), unique=False,
                        nullable=False, default='png')

    def getHDP(self):
        return list(map(int, loads(self.hdp)))


class NewsModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=False, nullable=False)
    content = db.Column(db.String(1000), unique=False, nullable=False)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    user_name = db.Column(db.String(50), unique=False, nullable=False)
    date = db.Column(db.String(50), unique=False, nullable=False)
    fraction = db.Column(db.String(1), unique=False, nullable=False)
    bgpic = db.Column(db.String(15), unique=False, nullable=False)

    def __repr__(self):
        return "<class NewsModel {} {} {}>".format(self.id,
                                                   self.title, self.user_id)


def getAvat(user, avtype='png', username=False):
    if username:
        user_id = user
    else:
        user_id = str(user.id)
    if exists(join(apath, 'static', 'img', user_id + '_av.' + avtype)) or \
       exists(join('static', 'img', user_id + '_av.' + avtype)):
        return join('static', 'img', user_id + '_av.' + avtype)
    else:
        return join('static', 'img',
                    fracs[user.fraction] + '_default_av.png')


def getHiddenNews():
    hdp = UsersModel.query.filter_by(id=session["user_id"]).first().getHDP()
    news = list(NewsModel.query.all())
    ts = news[:]
    for item in ts:
        if item.id not in hdp:
            news.remove(item)
    if session['news_sort_type']:
        news.sort(key=lambda n: n.id, reverse=session["reverse"])
    else:
        news.sort(key=lambda n: n.title, reverse=session["reverse"])
    return news


def getNews(user=False):
    if 'news_sort_type' not in session:
        session["news_sort_type"] = False
    hdp = UsersModel.query.filter_by(id=session["user_id"]).first().getHDP()
    if user:
        news = NewsModel.query.filter_by(user_id=user)
        news = news.filter(NewsModel.id not in hdp)
    else:
        news = NewsModel.query.filter(NewsModel.id not in hdp)
    news = list(news.filter(NewsModel.id not in hdp))
    ts = news[:]
    for n in ts:
        if n.id in hdp:
            logging.debug('Remove: ' + str(n.id))
            news.remove(n)
    if session['news_sort_type']:
        news.sort(key=lambda n: n.id, reverse=session["reverse"])
    else:
        news.sort(key=lambda n: n.title, reverse=session["reverse"])
    news_link = {}
    for n in news:
        news_link[n.id] = {}
        if n.user_id == session["user_id"]:
            news_link[n.id]['link'] = 'delete_news'
            news_link[n.id]['desc'] = 'Удалить новость'
        else:
            news_link[n.id]['link'] = 'hide_news'
            news_link[n.id]['desc'] = 'Скрыть новость'
    return news, news_link


@app.route('/')
@app.route('/index')
def index():
    if 'username' not in session:
        return redirect('/login')
    news, news_link = getNews()
    return render_template(
        'index.html', title='ВВаркрафте',
        username=session['username'], news=news, nl=news_link)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if "username" in session:
        return redirect('/0')
    session["logo"] = "D"
    session['bgpic'] = "secondary"
    form = RegistrationForm()
    if form.validate_on_submit():
        user = UsersModel(
            user_name=form.username.data,
            password_hash=generate_password_hash(form.password.data),
            fraction=form.fraction.data,
            regdate=datetime.now())
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if "username" in session:
        return redirect('/0')
    form = LoginForm()
    session["logo"] = "D"
    session['bgpic'] = "secondary"
    session["apath"] = apath
    if form.validate_on_submit():
        user = UsersModel.query.filter_by(
            user_name=form.username.data).first()
        session['username'] = user.user_name
        session['user_id'] = user.id
        session['news_sort_type'] = False
        session['reverse'] = False
        session["pic"] = getAvat(user, user.av_type)
        if user.fraction == "Альянс":
            session["logo"] = "A"
            session['bgpic'] = 'info'
        elif user.fraction == "Орда":
            session["logo"] = "H"
            session['bgpic'] = 'danger'
        return redirect('/index')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    ses_p = ['username', 'user_id', 'news_sort_type', 'reverse', 'pic', 'logo',
             'bgpic']
    for item in ses_p:
        try:
            session.pop(item)
        except Exception:
            pass
    return redirect('/login')


@app.route('/avatar/<int:user_id>', methods=['GET'])
def avatar(user_id):
    user = UsersModel.query.filter_by(id=user_id).first()
    avat = getAvat(user, user.av_type)
    return send_file(avat)


@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if 'username' not in session:
        return redirect('/login')
    retpage = request.args.get('from', '/index')
    form = AddNewsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        time_ = ctime(time())
        new = NewsModel(title=title, content=content,
                        user_id=session['user_id'], date=time_,
                        user_name=session['username'],
                        fraction=session["logo"],
                        bgpic=session["bgpic"])
        db.session.add(new)
        db.session.commit()
        return redirect(retpage)
    return render_template('add_news.html', title='Добавление новости',
                           form=form, username=session['username'])


@app.route('/addtoguild/<int:user_id>', methods=['GET'])
def addtoguild(user_id):
    if 'username' not in session:
        return redirect('/login')
    if user_id == 0 or user_id == session["user_id"]:
        return redirect('/wid0')
    retpage = request.args.get('from', '/index')
    us_add = UsersModel.query.filter_by(id=user_id).first()
    if not us_add:
        return redirect('/wid0')
    user = UsersModel.query.filter_by(id=session["user_id"]).first()
    if user.fraction == us_add.fraction:
        user.coguild = dumps(list(set(loads(user.coguild) + [user_id])))
        us_add.coguild = dumps(list(set(loads(us_add.coguild) + [user.id])))
        db.session.commit()
    return redirect(retpage)


@app.route('/removefromguild/<int:user_id>', methods=['GET'])
def removefromguild(user_id):
    if 'username' not in session:
        return redirect('/login')
    if user_id == 0 or user_id == session["user_id"]:
        return redirect('/wid0')
    retpage = request.args.get('from', '/index')
    us_add = UsersModel.query.filter_by(id=user_id).first()
    if not us_add:
        return redirect('/wid0')
    user = UsersModel.query.filter_by(id=session["user_id"]).first()
    us_cg = loads(user.coguild)
    us_add_cd = loads(us_add.coguild)
    if user_id in us_cg:
        us_cg.remove(user_id)
        us_add_cd.remove(user.id)
        user.coguild = dumps(us_cg)
        us_add.coguild = dumps(us_add_cd)
        db.session.commit()
    return redirect(retpage)


@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    retpage = request.args.get('from', '/index')
    new = NewsModel.query.filter_by(id=news_id).first()
    if new.user_id == session["user_id"] or session["username"] == 'admin':
        users = UsersModel.query.filter(UsersModel.hdp is not None).all()
        for user in users:
            h = loads(user.hdp)
            if news_id in h:
                h.remove(news_id)
            user.hdp = dumps(h)
        db.session.delete(new)
        db.session.commit()
    return redirect(retpage)


@app.route('/hide_news/<int:news_id>', methods=['GET'])
def hide_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    retpage = request.args.get('from', '/index')
    user = UsersModel.query.filter_by(id=session["user_id"]).first()
    logging.debug(user.user_name)
    if user.hdp:
        user.hdp = loads(user.hdp) + [news_id]
    else:
        user.hdp = [news_id]
    user.hdp = dumps(list(set(user.hdp)))
    logging.debug(user.hdp)
    db.session.commit()
    return redirect(retpage)


@app.route('/hidden')
def hidden():
    if 'username' not in session:
        return redirect('/login')
    news = getHiddenNews()
    lenNews = len(news)
    return render_template(
        'hidden.html', title='Спрятанные новости',
        news=news, lenNews=lenNews)


@app.route('/wid<int:user_id>', methods=['GET'])
def selfPage(user_id):
    if 'username' not in session:
        return redirect('/login')
    user = UsersModel.query.filter_by(id=session["user_id"]).first()
    if user_id == 0 and "user_id" in session:
        user_s = user
    else:
        user_s = UsersModel.query.filter_by(id=user_id).first()
        if not user_s:
            return redirect('/index')
    gld = loads(user.coguild)
    guilded = (user_id in gld)
    guildLen = len(gld)
    regdate = str(user_s.regdate).split('.')[0]
    pic = getAvat(user_s, user_s.av_type)
    news, nl = getNews(user_s.id)
    return render_template(
        "userpage.html",
        title="Страница пользователя " + user_s.user_name,
        pic=pic, news=news, nl=nl, user=user_s, newslen=len(news),
        regdate=regdate, add_allowed=(user_id == session["user_id"]),
        samefrac=(user.fraction == user_s.fraction), guilded=guilded,
        guildLen=guildLen)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        return redirect('/login')
    av_form = AvatarForm()
    us_form = ChangeUsernameForm()
    pass_form = ChangePasswordForm()
    user = UsersModel.query.filter_by(id=session["user_id"]).first()
    pic = getAvat(user, user.av_type)
    if av_form.submit_av.data and av_form.validate_on_submit():
        f = av_form.avatar.data
        user = UsersModel.query.filter_by(id=session["user_id"]).first()
        if f.filename.split('.')[-1] == 'gif':
            fnm = 'static/img/' + str(session["user_id"]) + "_av.gif"
            user.av_type = 'gif'
        else:
            fnm = 'static/img/' + str(session["user_id"]) + "_av.png"
            user.av_type = 'png'
        f.save(join(apath, fnm))
        db.session.commit()
        session["pic"] = getAvat(user, user.av_type)
        return redirect('/settings')
    if us_form.submit_us.data and us_form.validate_on_submit():
        user.user_name = us_form.new_name.data
        session["username"] = us_form.new_name.data
        db.session.commit()
        return redirect('/settings')
    if pass_form.submit_pass.data and pass_form.validate_on_submit():
        user.password_hash = generate_password_hash(pass_form.password.data)
        db.session.commit()
        return redirect('/settings')
    return render_template('settings.html', title='Настройки', av_form=av_form,
                           us_form=us_form, pass_form=pass_form, pic=pic)


@app.route('/show_news/<int:news_id>', methods=['GET'])
def show_news(news_id):
    if 'username' not in session:
        return redirect('/login')
    user = UsersModel.query.filter_by(id=session["user_id"]).first()
    if user.hdp:
        try:
            user.hdp = loads(user.hdp)
            user.hdp.remove(news_id)
        except Exception:
            pass
    else:
        user.hdp = []
    user.hdp = dumps(list(set(user.hdp)))
    db.session.commit()
    return redirect('/hidden')


@app.route('/sitemap', methods=['GET'])
def sitemap():
    if 'username' not in session:
        return redirect('/login')
    return render_template('sitemap.html', title='Карта сайта')


@app.route('/sort_news/<sort_type>', methods=['GET'])
def sort_news(sort_type):
    if 'username' not in session:
        return redirect('/login')
    retpage = request.args.get('from', '/index')
    if sort_type == "title":
        session['news_sort_type'] = True
    elif sort_type == "id":
        session['news_sort_type'] = False
    elif sort_type == "straight":
        session['reverse'] = False
    elif sort_type == "reverse":
        session['reverse'] = True
    return redirect(retpage)


@app.route('/terms')
def terms():
    if 'username' not in session:
        return redirect('/login')
    return render_template(
        'terms.html', title='Пользователькое соглашение')


@app.route('/user_list')
def user_list():
    if 'username' not in session:
        return redirect('/login')
    data = list(map(lambda x: [x.user_name, x.id, x.fraction, str(len(
        NewsModel.query.filter_by(user_id=x.id).all()))],
        UsersModel.query.all()))
    return render_template(
        'user_list.html', title='Информация о пользователях', data=data)


@app.route('/guild')
def guild():
    if 'username' not in session:
        return redirect('/login')
    cgls = loads(UsersModel.query.filter_by(
        id=session["user_id"]).first().coguild)
    cglslist = []
    nl = {}
    for idd in cgls:
        us = UsersModel.query.filter_by(id=idd).first()
        cglslist.append(us)
        nl[us] = str(len(NewsModel.query.filter_by(user_id=idd).all()))
    data = list(map(lambda x: [x.user_name, x.id, str(len(loads(x.coguild))),
                               nl[x]],
                    cglslist))
    return render_template(
        'user_list.html', title='Информация о пользователях', data=data)


@app.errorhandler(404)
def e404(e):
    return render_template('404.html'), 404


def makeDefUsers(rest=False):
    if rest:
        db.drop_all()
        db.create_all()
        user = UsersModel(
            user_name='admin',
            password_hash=generate_password_hash('admin'),
            fraction='Альянс',
            regdate=datetime.now())
        user2 = UsersModel(
            user_name='qwe',
            password_hash=generate_password_hash('rty'),
            fraction='Орда',
            regdate=datetime.now())
        db.session.add(user)
        db.session.add(user2)
        db.session.commit()
    else:
        db.create_all()


if __name__ == '__main__':
    makeDefUsers(True)
    app.run(port=8000, host='127.0.0.1')
