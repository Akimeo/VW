from requests import get, post, delete, put

print(get('http://localhost:8080/news').json())
print(get('http://localhost:8080/news/1').json())
print(get('http://localhost:8080/news/8').json())
print(get('http://localhost:8080/news/q').json())
print(post('http://localhost:8080/news',
           json={'title': 'Заголовок'}).json())
print(post('http://localhost:8080/news',
           json={'title': 'Заголовок',
                 'content': 'Текст новости',
                 'user_id': 1}).json())
print(delete('http://localhost:8080/news/8').json())
print(delete('http://localhost:8080/news/3').json())
print(get('http://localhost:8080/users').json())
print(get('http://localhost:8080/user/1').json())
print(get('http://localhost:8080/user/8').json())
print(get('http://localhost:8080/user/q').json())
print(post('http://localhost:8080/users',
           json={'user_name': 'Fox'}).json())
print(post('http://localhost:8080/users',
           json={'user_name': 'Fox',
                 'password_hash': 'NoItems'}).json())
print(delete('http://localhost:8080/user/8').json())
print(delete('http://localhost:8080/user/3').json())
print(get('http://localhost:8080/news').json())
print(
    put('http://localhost:8080/news/1',
        json={'title': 'Serfing the Web',
              'content':
              'No Plugins, Firefox Only, Final Destination'}).json())
print(
    put('http://localhost:8080/news/2',
        json={'content': 'title'}).json())
print(
    put('http://localhost:8080/news/21',
        json={'title': 'Serfing the Web',
              'content':
              'No Plugins, Firefox Only, Final Destination'}).json())
print(
    put('http://localhost:8080/news/1',
        json={}).json())
print(
    put('http://localhost:8080/news/1',
        json={'user_id': 21}).json())
print(get('http://localhost:8080/news').json())

print(get('http://localhost:8080/users').json())
print(
    put('http://localhost:8080/user/1',
        json={'user_name': 'Nefir',
              'password_hash': '123'}).json())
print(
    put('http://localhost:8080/user/2',
        json={'password_hash': '123'}).json())
print(
    put('http://localhost:8080/user/21',
        json={'user_name': 'Nefir',
              'password_hash': '123'}).json())
print(
    put('http://localhost:8080/user/1',
        json={}).json())
print(
    put('http://localhost:8080/user/1',
        json={'user_id': 21}).json())
print(
    put('http://localhost:8080/user/2',
        json={'user_name': 'Nefir'}).json())
print(get('http://localhost:8080/users').json())
