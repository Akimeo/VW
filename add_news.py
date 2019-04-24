from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[
                        DataRequired('Заполните это поле')])
    content = TextAreaField('Текст новости', validators=[
                            DataRequired('Заполните это поле')])
    submit = SubmitField('Добавить')
