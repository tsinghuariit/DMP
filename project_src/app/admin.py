# -*- coding: utf-8 -*-  
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user
from flask_security.utils import encrypt_password
from app import app, db
from models import User, Dataset, Role, Category


# Create customized model view class
class BaseModelView(ModelView):

    can_view_details = True
    create_modal = True
    edit_modal = True
    can_export = True

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


class UserModelView(BaseModelView):
    column_exclude_list = ['password',]
    column_searchable_list = (User.nickname, User.email)


class DatasetModelView(BaseModelView):
    column_labels = dict(
        nickname=u'用户名',
        email=u'邮箱',
        cellphone=u'手机号',
        about_me=u'简介',
        last_seen=u'上次登录',
        active=u'活跃',
        confirmed_at=u'上次修改')


class RoleModelView(BaseModelView):
    column_labels = dict(
        author=u'发布用户',
        authority=u'授权方式',
        kind=u'数据空间',
        expert=u'专家学者',
        subject=u'学科分类',
        datatype=u'类型分类',
        title=u'标题',
        published=u'发布日期',
        updated=u'修改日期',
        datsource=u'数据文件',
        contact=u'联系方式',
        desc=u'简介')


class CategoryView(BaseModelView):
    form_columns = ('parrent','id', 'name', 'description', 'sort', 'is_custom',
                     'type')
    #inline_models=(Category.id)
    form_excluded_columns = [
        'children',
    ]


admin = Admin(
    app, name=app.config['SITE_NAME'] + u'管理后台', template_mode='bootstrap3')

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for)


admin.add_view(UserModelView(User, db.session, u'用户管理'))
admin.add_view(DatasetModelView(Dataset, db.session, u'数据集管理'))
admin.add_view(RoleModelView(Role, db.session, u'权限管理'))
admin.add_view(CategoryView(Category, db.session, u'分类管理'))
