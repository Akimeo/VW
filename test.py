from os.path import dirname, abspath, exists


a = dirname(abspath(__file__))
print(a)
print(abspath(dirname(__file__)))
print(abspath(__file__))
print(dirname(__file__))
print(exists(a + '/static/img/admin_av.gif'))
