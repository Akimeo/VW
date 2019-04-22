from flask import Flask, jsonify, make_response, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
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


class News(Resource):
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


class NewsList(Resource):
    def get(self):
        headers = {'Content-Type': 'text/html'}
        return make_response(
            render_template('index.html', title='ВВаркрафте',
                            username='admin', news=NewsModel.query.all()),
            200, headers)

    def post(self):
        args = news_parser.parse_args()
        news = NewsModel(title=args['title'],
                         content=args['content'],
                         user_id=args['user_id'])
        db.session.add(news)
        db.session.commit()
        return jsonify({'success': 'OK'})


class User(Resource):
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


class UsersList(Resource):
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


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    api.add_resource(NewsList, '/', '/news')
    api.add_resource(News, '/news/<int:news_id>')
    api.add_resource(UsersList, '/users')
    api.add_resource(User, '/user/<int:user_id>')
    db.drop_all()
    db.create_all()
    user1 = UsersModel(
        user_name='admin',
        password_hash='admin')
    user2 = UsersModel(
        user_name='user',
        password_hash='user')
    news1 = NewsModel(
        title='SSBU',
        content='No Items, Fox Only, Final Destination',
        user_id=1)
    news2 = NewsModel(
        title='title',
        content='content',
        user_id=2)
    db.session.add(user1)
    db.session.add(user2)
    db.session.add(news1)
    db.session.add(news2)
    db.session.commit()
    app.run(port=8080, host='127.0.0.1')
