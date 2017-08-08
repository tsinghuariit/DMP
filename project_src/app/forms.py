# coding=utf-8
from flask import flash
from flask_babel import gettext
from flask_wtf import Form
from wtforms import StringField, BooleanField, TextAreaField, PasswordField, \
    validators
from flask_wtf.file import FileField, FileRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length
from .models import User, Category


def flash_form_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash("%s" % error)


class LoginForm(Form):
    user_id = StringField('user_id', validators=[DataRequired(u'请输入登录账户')])
    password = PasswordField('password', validators=[DataRequired(u'请输入密码')])
    remember_me = BooleanField('remember_me', default=False)


class RegistrationForm(Form):
    user_id = StringField('user_id', validators=[DataRequired(u'请输入登录账户')])
    email = StringField('email', validators=[DataRequired(u'请输入邮箱')])
    password = PasswordField(u'password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message=u'两次密码输入不一致')
    ])
    confirm = PasswordField(u'confirm')
    cellphone = StringField('cellphone', validators=[DataRequired()])
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])


class EditForm(Form):
    nickname = StringField('nickname', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])
    cellphone = StringField('cellphone', validators=[DataRequired()])
    now_passwd = PasswordField('now_passwd', validators=[DataRequired])
    new_passwd = PasswordField('new_passwd', validators=[DataRequired])
    confirm_passwd = PasswordField('confirm_passwd', validators=[DataRequired])
    org = QuerySelectField(query_factory=lambda: filtered_categories(1),
                           allow_blank=True)
    expert = QuerySelectField(query_factory=lambda: filtered_categories(5),
                              allow_blank=True)
    professional = QuerySelectField(query_factory=lambda: filtered_categories(7),
                                    allow_blank=True)
    avatar = FileField()
    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        if self.nickname.data != User.make_valid_nickname(self.nickname.data):
            self.nickname.errors.append(gettext(
                'This nickname has invalid characters. '
                'Please use letters, numbers, dots and underscores only.'))
            return False
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user is not None:
            self.nickname.errors.append(gettext(
                'This nickname is already in use. '
                'Please choose another one.'))
            return False
        return True


def filtered_categories(t):
    return Category.query.filter(Category.type == t, Category.parent_id > 0).order_by(Category.id).all()


class GroupForm(Form):

    name = StringField('name', validators=[DataRequired()])
    introduction = TextAreaField('introduction', validators=[DataRequired()])
    authority = QuerySelectField(query_factory=lambda: filtered_categories(2),
                                 allow_blank=False)
    avatar = FileField()

class DatasetForm(Form):

    title = StringField('title', validators=[DataRequired(message=u'请填写标题')])
    # contact = StringField('contact', validators=[DataRequired()])
    desc = TextAreaField('desc')
    authority = QuerySelectField(query_factory=lambda: filtered_categories(2),
                                 allow_blank=False)
    subject = QuerySelectField(query_factory=lambda: filtered_categories(3),
                               allow_blank=True,validators=[DataRequired(message=u'请选择学科分类.')])
    datatype = QuerySelectField(query_factory=lambda: filtered_categories(4),
                                allow_blank=True,validators=[DataRequired(message=u'请选择类型分类.')])
    expert = QuerySelectField(query_factory=lambda: filtered_categories(5),
                              allow_blank=True,validators=[DataRequired(message=u'请选择专家学者.')])
    kind = QuerySelectField(query_factory=lambda: filtered_categories(6),
                            allow_blank=True,validators=[DataRequired(message=u'请选择数据空间分类.')])
    org = QuerySelectField(query_factory=lambda: filtered_categories(1),
                           allow_blank=True,validators=[DataRequired(message=u'请选择您的单位.')])
    datasource = FileField(validators=[FileRequired(message= u'请上传你的数据集文件！')])

    # def __init__(self, original_nickname, *args, **kwargs):
    #     Form.__init__(self, *args, **kwargs)
    #     self.original_nickname = original_nickname

    # def validate(self):
    #     if not Form.validate(self):
    #         return False
    #     return True
class EditDatasetForm(Form):

    title = StringField('title', validators=[DataRequired()])
    # contact = StringField('contact', validators=[DataRequired()])
    desc = TextAreaField('desc')
    authority = QuerySelectField(query_factory=lambda: filtered_categories(2),
                                 allow_blank=False)
    subject = QuerySelectField(query_factory=lambda: filtered_categories(3),
                               allow_blank=False)
    datatype = QuerySelectField(query_factory=lambda: filtered_categories(4),
                                allow_blank=False)
    expert = QuerySelectField(query_factory=lambda: filtered_categories(5),
                              allow_blank=False)
    kind = QuerySelectField(query_factory=lambda: filtered_categories(6),
                            allow_blank=False)
    org = QuerySelectField(query_factory=lambda: filtered_categories(1),
                           allow_blank=False)
    datasource = FileField()


class PostForm(Form):
    post = StringField('post', validators=[DataRequired()])


class SearchForm(Form):
    search = StringField('search', validators=[DataRequired()])


class ContactForm(Form):
    cellphone = StringField('cellphone', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    report = TextAreaField('report')


class GetbackPasswd(Form):
    new_passwd = PasswordField('orign_password', validators=[DataRequired()])
    confirm_passwd = PasswordField('new_passwd', validators=[DataRequired()])


class EmailCaptcha(Form):
    email = StringField('email', validators=[DataRequired()])
    captcha = StringField('captcha', validators=[DataRequired()])


class SmsCaptcha(Form):
    cellphone = StringField('cellphone', validators=[DataRequired])
    captcha = StringField('captcha', validators=[DataRequired])

class InvitationCode(Form):
    invitation_code = StringField('invitation_code',validators=[DataRequired])