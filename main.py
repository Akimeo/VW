from flask import (Flask, jsonify, make_response, request,
                   session, render_template, redirect)
from flask_sqlalchemy import SQLAlchemy
from flask_restful import reqparse, abort, Api, Resource
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField,
                     SubmitField, TextAreaField)
from wtforms.validators import DataRequired, InputRequired, ValidationError
from time import time, ctime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vwb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)

news_parser = reqparse.RequestParser()
news_parser.add_argument('title', required=True)
news_parser.add_argument('content', required=True)
news_parser.add_argument('user_id', required=True, type=int)

put_news_parser = reqparse.RequestParser()
put_news_parser.add_argument('title')
put_news_parser.add_argument('content')

users_parser = reqparse.RequestParser()
users_parser.add_argument('user_name', required=True)
users_parser.add_argument('password_hash', required=True)

put_user_parser = reqparse.RequestParser()
put_user_parser.add_argument('user_name')
put_user_parser.add_argument('password_hash')


news_html_parser = reqparse.RequestParser()
news_html_parser.add_argument('method')


class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class LoginForm(FlaskForm):
    username = StringField('Логин',
                           validators=[InputRequired('Введите логин')])
    password = PasswordField('Пароль',
                             validators=[InputRequired('Введите пароль')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

    def validate_password(form, field):
        namer = UsersModel.query.filter_by(username=form.username.data).first()
        if namer:
            if namer.password != field.data:
                raise ValidationError('Неправильный пароль!')


class UsersModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), unique=False, nullable=False)


class NewsModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=False, nullable=False)
    content = db.Column(db.String(1000), unique=False, nullable=False)
    user_id = db.Column(db.Integer, unique=False, nullable=False)


def abort_if_user_not_found(user_id):
    if not UsersModel.query.filter_by(id=user_id).first():
        abort(404, message="User {} not found".format(user_id))


def abort_if_news_not_found(news_id):
    if not NewsModel.query.filter_by(id=news_id).first():
        abort(404, message="News {} not found".format(news_id))


class News_API(Resource):
    def get(self, news_id):
        abort_if_news_not_found(news_id)
        news = NewsModel.query.filter_by(id=news_id).first()
        return jsonify({'news': {'title': news.title,
                                 'content': news.content,
                                 'user_id': news.user_id}})

    def delete(self, news_id):
        abort_if_news_not_found(news_id)
        news = NewsModel.query.filter_by(id=news_id).first()
        db.session.delete(news)
        db.session.commit()
        return jsonify({'success': 'OK'})

    def put(self, news_id):
        abort_if_news_not_found(news_id)
        args = put_news_parser.parse_args()
        news = NewsModel.query.filter_by(id=news_id).first()
        if args['title']:
            news.title = args['title']
        if args['content']:
            news.content = args['content']
        db.session.commit()
        return jsonify({'success': 'OK'})


class NewsList_API(Resource):
    def get(self):
        news = {}
        for item in NewsModel.query.all():
            news[item.id] = {'title': item.title,
                             'content': item.content,
                             'user_id': item.user_id}
        return jsonify({'news': news})

    def post(self):
        args = news_parser.parse_args()
        news = NewsModel(title=args['title'],
                         content=args['content'],
                         user_id=args['user_id'])
        db.session.add(news)
        db.session.commit()
        return jsonify({'success': 'OK'})


class User_API(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        user = UsersModel.query.filter_by(id=user_id).first()
        return jsonify({'users': {'user_name': user.user_name,
                                  'password_hash': user.password_hash}})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        user = UsersModel.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': 'OK'})

    def put(self, user_id):
        abort_if_user_not_found(user_id)
        args = put_user_parser.parse_args()
        user = UsersModel.query.filter_by(id=user_id).first()
        if args['user_name']:
            another_user = UsersModel.query.filter_by(
                user_name=args['user_name']).first()
            if another_user and another_user.id != user.id:
                return jsonify({'error': 'Name not available'})
            user.user_name = args['user_name']
        if args['password_hash']:
            user.password_hash = args['password_hash']
        db.session.commit()
        return jsonify({'success': 'OK'})


class UsersList_API(Resource):
    def get(self):
        users = {}
        for item in UsersModel.query.all():
            users[item.id] = {'user_name': item.user_name,
                              'password_hash': item.password_hash}
        return jsonify({'users': users})

    def post(self):
        args = users_parser.parse_args()
        user = UsersModel(user_name=args['user_name'],
                          password_hash=args['password_hash'])
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': 'OK'})


class Index(Resource):
    def get(self):
        if "reverse" not in session:
            session["reverse"] = True
        if "sort_time" not in session:
            session["sort_time"] = True
        if 'username' not in session:
            return redirect('/login')
        news = list(NewsModel.query.filter_by(user_id=session['user_id']))
        if session["sort_time"]:
            news.sort(key=lambda item: item.id, reverse=session["reverse"])
        else:
            news.sort(key=lambda item: item.id, reverse=session["reverse"])
        return make_response(render_template('index.html',
                                             username=session['username'],
                                             news=news), 200)

    def post(self):
        if request.form.get('sort_met'):
            session["sort_time"] = int(request.form['sort_met'])
        if request.form.get('reversed'):
            session["reverse"] = bool(int(request.form['reversed']))
        return redirect('/index')


class News(Resource):
    def post(self, news_id):
        args = news_html_parser.parse_args()
        if args["method"] == 'delete':
            self.delete(news_id)
        return redirect('/index')

    def delete(self, news_id):
        if 'username' not in session:
            return redirect('/index')
        news = NewsModel.query.filter_by(id=news_id).first()
        db.session.delete(news)
        db.session.commit()
        return redirect('/index')


class NewsList(Resource):
    def post(self):
        if 'username' not in session:
            return redirect('/login')
        form = AddNewsForm()
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            nm = NewsModel(title=title, content=content,
                           user_id=session['user_id'])
            db.session.add(nm)
            db.session.commit()
            return redirect('/index')
        return make_response(render_template('add_news.html',
                                             title='Добавление новости',
                                             username=session['username'],
                                             form=form), 200)


class Login(Resource):
    def get(self):
        global ssn
        ssn["loginform"] = LoginForm()
        print(ssn)
        return make_response(render_template('login.html',
                                             form=ssn["loginform"],
                                             title='Авторизация'), 200)

    def post(self):
        print(ssn)
        form = ssn["loginform"]
        user_name = form.username.data
        password = form.password.data
        user_pass = UsersModel.query.filter_by(user_name=user_name).first()
        if user_pass and user_pass.password == password:
            session['username'] = user_name
            session['user_id'] = user_pass.id
            session['remember'] = form.remember_me.data
        return make_response(redirect('/index'), 200)


class Logout(Resource):
    def get(self):
        session.pop('username', 0)
        session.pop('user_id', 0)
        session.pop('remember', 0)
        return redirect('/login')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    ssn = {}
    api.add_resource(NewsList_API, '/api/news')
    api.add_resource(News_API, '/api/news/<int:news_id>')
    api.add_resource(UsersList_API, '/api/users')
    api.add_resource(User_API, '/api/user/<int:user_id>')
    api.add_resource(Index, '/', '/index')
    api.add_resource(NewsList, '/news')
    api.add_resource(News, '/news/<int:news_id>')
    api.add_resource(Login, '/login')
    api.add_resource(Logout, '/logout')
    db.drop_all()
    db.create_all()
    user1 = UsersModel(
        user_name='admin',
        password_hash='admin')
    news1 = NewsModel(
        title='SSBU',
        content='No Items, Fox Only, Final Destination',
        user_id=1)
    news2 = NewsModel(
        title='title',
        content='content',
        user_id=1)
    db.session.add(user1)
    db.session.add(news1)
    db.session.add(news2)
    db.session.commit()
    app.run(port=8000, host='127.0.0.1')
