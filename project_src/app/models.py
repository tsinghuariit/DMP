# coding=utf-8
from hashlib import md5
import re
from app import db
from app import app
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from flask_login import UserMixin, login_required
import sys
from datetime import datetime
import urllib
if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = True
    import flask_whooshalchemy

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

following_datasets = db.Table(
    'following_datasets',
    db.Column('dataset_udi',db.String(300),db.ForeignKey('dataset.udi')),
    db.Column('follower_id',db.Integer,db.ForeignKey('user.id'))
)

# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)
class GroupInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer)
    invited_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    inviter = db.relationship('User',backref=db.backref('groups_invited', lazy='dynamic'),foreign_keys=[invited_id])
    group_id = db.Column(db.Integer,db.ForeignKey('group.id'))
    group = db.relationship('Group',backref=db.backref('group_invitations', lazy='dynamic'),foreign_keys=[group_id])
    created_at = db.Column(db.DateTime)



class GroupApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer)
    applier_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    applier = db.relationship('User',backref=db.backref('groups_applied', lazy='dynamic'),foreign_keys=[applier_id])
    manager_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    manager = db.relationship('User',backref=db.backref('group_applications', lazy='dynamic'),foreign_keys=[manager_id])
    group_id = db.Column(db.Integer,db.ForeignKey('group.id'))
    group = db.relationship('Group',backref=db.backref('applications', lazy='dynamic'),foreign_keys=[group_id])
    def init_apply(self):
        if str(self.group.auth_type) == '10004':
            self.status=3
        elif str(self.group.auth_type) == '10006':
            self.status=2
        else :
            self.status=4
        return self


    def __init__(self,user_id,group):
        if str(group.auth_type) == '10005':
            self.status=3
        elif str(group.auth_type) == '10004':
            self.status=2
        else :
            self.status=4
        self.applier_id = user_id
        self.manager_id = group.manager_id
        self.group_id=group.id

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auth_type = db.Column(db.Integer, db.ForeignKey('category.id'))
    authority = db.relationship('Category',
                                backref=db.backref(
                                    'authority_groups', lazy='dynamic'),
                                foreign_keys=[auth_type])
    name = db.Column(db.String(120))
    introduction = db.Column(db.String(500))

    manager_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    manager = db.relationship('User',backref=db.backref('managedGroups', lazy='dynamic'),foreign_keys=[manager_id])
    avatarsource = db.Column(db.String(1024))

    def __init__(self,creater,name,introduction='',auth_type=0,avatarsource=''):
        self.manager_id=creater.id
        self.manager = creater
        self.name = name
        self.introduction = introduction
        self.auth_type=auth_type
        self.avatarsource=avatarsource

    def __repr__(self):  # pragma: no cover
        return '<Group %r>' % (self.name)
    def user_nums(self):
        return self.applications.filter_by(status=3).count()
    def all_datasets(self):
        return Dataset.query.join(GroupApplication,
        GroupApplication.applier_id==Dataset.author_id).filter(GroupApplication.group_id==self.id,GroupApplication.status==3)
    def dataset_nums(self):
        return self.all_datasets().count()
    def all_datasets_main_subject(self):
        subject_dict = {}
        for dataset in self.all_datasets():
            ca_name = Category.query.filter(Category.id == dataset.subject_id).first().name
            subject_dict[ca_name] = Dataset.query.filter(Dataset.subject_id == dataset.subject_id ).count()
        sorted(subject_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
        return subject_dict

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer)
    applier_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    applier = db.relationship('User',backref=db.backref('applications_applied', lazy='dynamic'))
    author_id = db.Column(db.Integer)
    author = db.relationship('User',backref=db.backref('applications', lazy='dynamic'))
    dataset_udi = db.Column(db.String(300),db.ForeignKey('dataset.udi'))
    dataset = db.relationship('Dataset',backref=db.backref('applications', lazy='dynamic'))

    def __init__(self,user_id,dataset_udi,author_id):
        self.status = 2
        self.user_id = user_id
        self.dataset_udi = dataset_udi
        self.author_id=author_id


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    cellphone = db.Column(db.String(30), index=True, unique=True)
    password = db.Column(db.String(30), index=True)
    avatarsource = db.Column(db.String(1024))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    followed = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')
    datasets_following = db.relationship('Dataset',
                               secondary=following_datasets,
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic'
                               )
    active = db.Column(db.Boolean(), default=True)
    invitation_active = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    org_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    org = db.relationship('Category',
                          backref=db.backref('org_user', lazy='dynamic'),
                          foreign_keys=[org_id])
    expert_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    expert = db.relationship('Category',
                             backref=db.backref('expert_user', lazy='dynamic'),
                             foreign_keys=[expert_id])
    professional_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    professional = db.relationship('Category',
                                   backref=db.backref(
                                       'professional_user', lazy='dynamic'),
                                   foreign_keys=[professional_id])

    @staticmethod
    def make_valid_nickname(nickname):
        return re.sub('[^a-zA-Z0-9_\.]', '', nickname)

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    @staticmethod
    def make_valid_cellphone(cellphone):
        if cellphone is None:
            return False
        else:
            if User.query.filter_by(cellphone=cellphone).first() is None:
                return cellphone
            else:
                return False

    @staticmethod
    def make_valid_email(email):
        if User.query.filter_by(email=email).first() is None:
            return email
        else:
            return False

    @property
    def is_authenticated(self):
        return self.active

    @property
    def is_active(self):
        return self.active

    @property
    def is_anonymous(self):
        return False

    def has_role(self, *args):
        return set(args).issubset({role.name for role in self.roles})

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def get_auth_token(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0


    def is_following_dataset(self, dataset):
        return self.datasets_following.filter(
            following_datasets.c.dataset_udi == dataset.udi).count() > 0

    def follow_dataset(self, dataset):
        if not self.is_following_dataset(dataset):
            self.datasets_following.append(dataset)
            return self

    def unfollow_dataset(self, dataset):
        if self.is_following_dataset(dataset):
            self.datasets_following.remove(dataset)
            return self

    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
            follow).order_by(
            Post.timestamp.desc())

    def followed_users(self, user):
        return self.followers.filter()

    def follower_users(self, user):
        return self.followed.filter()

    def apply_dataset_status(self,dataset):
        if self.id == dataset.author_id:
            return 0
        elif str(dataset.authority_id) == '10004':
            return -1
        elif str(dataset.authority_id) != '10006':
            return -2
        elif self.applications.filter(
                Application.dataset_udi == dataset.udi).count() <= 0:
            return 1
        else:
            return self.applications.filter(
                Application.dataset_udi == dataset.udi).first().status

    def apply(self,dataset,author):
        if self.apply_dataset_status(dataset) == 1:
            application = Application(self.id,dataset.udi,author.id)
            self.applications.append(application)
        return self
    def applied(self,author):
        return self.applications_applied.filter(Application.author_id==author.id)

    def dataset_creat_count(self):
        return Dataset.query.filter_by(author_id=self.id).count()

    def in_group(self,group):
        if group.manager_id == self.id:
            return 0 #no need to apply
        elif (str(group.auth_type)=='10006' or str(group.auth_type)=='10004') and self.groups_applied.filter(GroupApplication.group_id==group.id).count()==0:
            return 1 #could apply
        elif self.groups_applied.filter(GroupApplication.status==1,GroupApplication.group_id==group.id).count()>0:
            return 1
        # elif str(group.auth_type)=='10004' and self.groups_applied.filter(GroupApplication.group_id==group.id).count()>0:
        #     return 3
        elif self.groups_applied.filter(GroupApplication.status==2,GroupApplication.group_id==group.id).count()>0:
            return 2 #applying
        elif self.groups_applied.filter(GroupApplication.status==3,GroupApplication.group_id==group.id).count()>0:
            return 3 #apply sucess
        else:
            return 4 #apply failed



    def __repr__(self):  # pragma: no cover
        return '<User %r>' % (self.nickname)


class Post(db.Model):
    __searchable__ = ['body']

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):  # pragma: no cover
        return '<Post %r>' % (self.body)


class Dataset(db.Model):
    __searchable__ = []

    udi = db.Column(db.String(140), primary_key=True)
    title = db.Column(db.String(140))
    # published = db.Column(db.DateTime)
    # updated = db.Column(db.DateTime)

    published = db.Column(db.DateTime, default=datetime.now)
    updated = db.Column(db.DateTime, default=datetime.now,
                        onupdate=datetime.now)

    datasource = db.Column(db.String(1024))

    signature = db.Column(db.String(1024))

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User',
                             backref=db.backref('datasets', lazy='dynamic'))

    contact = db.Column(db.String(40))

    desc = db.Column(db.String(1024))

    views = db.Column(db.Integer,default=0)

    authority_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    authority = db.relationship('Category',
                                backref=db.backref(
                                    'authority_datasets', lazy='dynamic'),
                                foreign_keys=[authority_id])

    kind_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    kind = db.relationship('Category',
                           backref=db.backref('kind_datasets', lazy='dynamic'),
                           foreign_keys=[kind_id])

    expert_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    expert = db.relationship('Category',
                             backref=db.backref(
                                 'expert_datasets', lazy='dynamic'),
                             foreign_keys=[expert_id])

    subject_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    subject = db.relationship('Category',
                              backref=db.backref(
                                  'subject_datasets', lazy='dynamic'),
                              foreign_keys=[subject_id])

    datatype_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    datatype = db.relationship('Category',
                               backref=db.backref(
                                   'datatype_datasets', lazy='dynamic'),
                               foreign_keys=[datatype_id])

    org_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    org = db.relationship('Category',
                          backref=db.backref('org_datasets', lazy='dynamic'),
                          foreign_keys=[org_id])

    def __repr__(self):  # pragma: no cover
        return '<Dataset %r>' % (self.title)

    def is_authorized(self, user):
        return str(self.authority_id) == '10004' or self.author_id == user.id or user.apply_dataset_status(self)==3

    def is_editable(self, user):
        return user.id == self.author_id

    def is_deleteable(self, user):
        return user.id == self.author_id

    def get_waiting_applications(self):
        return self.applications.filter(Application.status == 2)

    def get_applied_applications(self):
        return self.applications.filter(Application.status > 2)

    def nofile(self):
        return False

    def urlsource(self):
        url = self.udi#urllib.pathname2url('/datasets/item/'+self.udi+'/download/'+)
        url=url.replace('/','%2F')
        return url



class DatasetHistory(db.Model):
    __searchable__ = []

    his_id = db.Column(db.Integer, primary_key=True)
    his_version = db.Column(db.Integer)
    his_created = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # his_created = db.Column(db.DateTime)
    udi = db.Column(db.String(140))
    signature = db.Column(db.String(1024))
    title = db.Column(db.String(140))
    published = db.Column(db.DateTime)
    updated = db.Column(db.DateTime)

    datasource = db.Column(db.String(1024))

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    contact = db.Column(db.String(40))

    desc = db.Column(db.String(1024))

    authority_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    kind_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    expert_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    subject_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    datatype_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    org_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    def __repr__(self):  # pragma: no cover
        return '<Dataset %r>' % (self.title)

    def __init__(self, dataset):
        his = DatasetHistory.query.filter_by(udi=dataset.udi).order_by(
            DatasetHistory.his_id.desc()).first()
        if his:
            self.his_version = his.his_version + 1
        else:
            self.his_version = 1

        self.udi = dataset.udi
        self.title = dataset.title
        self.published = dataset.published
        self.updated = dataset.updated
        self.signature = dataset.signature
        self.datasource = dataset.datasource
        self.author_id = dataset.author_id
        self.contact = dataset.contact
        self.desc = dataset.desc
        self.authority_id = dataset.authority_id
        self.kind_id = dataset.kind_id
        self.expert_id = dataset.expert_id
        self.subject_id = dataset.subject_id
        self.datatype_id = dataset.datatype_id
        self.org_id = dataset.org_id

class EventLog(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    #级联删除
    from_user_id = db.Column(db.Integer,db.ForeignKey('user.id',ondelete="CASCADE"))
    to_user_id = db.Column(db.Integer,db.ForeignKey('user.id',ondelete="CASCADE"))
    dataset_id = db.Column(db.String(300),db.ForeignKey('dataset.udi',ondelete="CASCADE"))
    event_name = db.Column(db.String(225))
    event_time = db.Column(db.DateTime)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    description = db.Column(db.String(560))
    sort = db.Column(db.Integer)
    is_custom = db.Column(db.Integer)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    type = db.Column(db.Integer)
    parrent = db.relationship('Category', remote_side=[id], backref='children')

    # def __init__(self, name):
    #     self.name = name
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)

    def __repr__(self):
        return self.name


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cellphone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    report = db.Column(db.String(1024))


if enable_search:
    flask_whooshalchemy.whoosh_index(app, Post)
