#!/usr/bin/env python
# -*- coding:utf-8 -*-
# python 2.7.10

"""
记录用户行为日志模块
"""


__author__ = 'AJ Kippa'


from kafka import KafkaProducer
import datetime
import functools
import json
from . import app,options,db
from flask import (abort, flash, g, jsonify, redirect, render_template,
                   request, send_from_directory, session, url_for)
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user
import logging
from logging.handlers import RotatingFileHandler
from .models import EventLog,Dataset,DatasetHistory,User
from sqlalchemy import desc

def judge(method):
    """
    通过判断是否线上环境来确定是否记录日志
    :param method:
    :return:
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if options.production:
            method(self, *args, **kwargs)
        else:
            pass
    return wrapper


def get_now_str():
    '''
    获取系统当前时间
    :return: 字符串类型，精确到毫秒
    '''
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def get_now_datetime():
    '''
    获取系统当前时间
    :return: 字符串类型，精确到毫秒
    '''
    return datetime.datetime.now()

class EventLogs(object):
    """
    用户行为事件类
    """
    def __init__(self):
        """
        初始化，基础事件的基本属性
        """
        if options.production:
            from config_web import USER_LOG_PATH
            self.log_path = USER_LOG_PATH
            # self.ip_address = ''
            try:
                # X-Real-IP 字段在nginx配置文件里面配置
                self.ip_address = request.headers['X-Real-IP']
            except:
                self.ip_address = request.remote_addr
        else:

            from config import USER_LOG_PATH
            self.ip_address = request.remote_addr or ''
            self.log_path = USER_LOG_PATH
        # 未登录用户id记为-1
        self.user_id = -1 if not current_user.is_active else g.user.id
        self.nickname = '' if not current_user.is_active else g.user.nickname
        self.event_name = ''
        self.event_time = get_now_str()
        self.referrer = request.referrer or ''
        self.user_agent = request.user_agent or ''
        self.base_url = request.base_url or ''
        self.logs = {
            "user_id": str(self.user_id),
            "nickname": str(self.nickname),
            'ip_address': self.ip_address,
            'event_time':self.event_time,
            'referrer':self.referrer,
            'user_agent':str(self.user_agent),
            'base_url':self.base_url
        }
        # 50M*100 大概可以存储一千万条用户数据
        self.handler = RotatingFileHandler(self.log_path, maxBytes=50 * 1024 * 1024, backupCount=100)
        self.handler.setLevel(logging.INFO)

    def _logging(self):
        """输出日志"""
        app.logger.addHandler(self.handler)
        _log = {
            'USER-LOG':self.logs
        }
        app.logger.info('%s'%json.dumps(_log))
        #注意写完要移除，不然会重复写入
        app.logger.removeHandler(self.handler)


    @classmethod
    @judge
    def view_home(cls):
        """
        访问首页
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'view_home_page'
        cls._logging(e)

    @classmethod
    @judge
    def view_about(cls,sub_uri=''):
        """
        访问关于我们
        :param sub_uri:关于页面下的具体tab
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'view_about'
        e.logs['sub_uri'] = sub_uri
        cls._logging(e)

    @classmethod
    @judge
    def view_join(cls):
        """
        访问加入我们页面
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'view_join'
        cls._logging(e)

    @classmethod
    @judge
    def view_feedback(cls,is_succeed=False,cellphone='',email='',report=''):
        """
        访问意见反馈页面
        :param is_succeed: 意见反馈是否提交了
        :param cellphone: 手机号
        :param email: 邮件
        :param report: 反馈内容
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'view_feedback'
        e.logs['is_succeed'] = is_succeed
        e.logs['cellphone'] = cellphone
        e.logs['email'] = email
        e.logs['report'] = report
        cls._logging(e)

    @classmethod
    @judge
    def view_contact(cls):
        """
        访问加入我们页面
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'view_contact'
        cls._logging(e)

    @classmethod
    @judge
    def view_dataset_list(cls,page_num=1,sort_type=None,cate=None,keywords=None,dataset_num=0):
        """
        访问数据集列表
        :param page_num: 页面number
        :param sort_type: 排序方式
        :param cate: 选择的数据分类
        :param keywords: 查询关键字
        :param dataset_num: 展示的总数据集number
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'view_dataset_list'
        e.logs['page_num'] = page_num
        e.logs['sort_type'] = sort_type
        e.logs['cate'] = ' '.join(cate)
        e.logs['keywords'] = keywords
        e.logs['dataset_num'] = dataset_num
        cls._logging(e)

    @classmethod
    @judge
    def view_dataset_detail(cls,dataset_id,sub_uri='meta',is_downloaded=False,uid_for_dataset=''):
        """
        访问数据集详情
        :param dataset_id: 数据集的ID
        :param sub_uri: 数据集详情页的具体tab
        :param uid_for_dataset: 数据集的用户
        :param is_downloaded: 是否点击了下载
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'view_dataset_detail'
        e.logs['dataset_id'] = dataset_id
        e.logs['sub_uri'] = sub_uri
        e.logs['is_downloaded'] = is_downloaded
        if is_downloaded and str(e.logs['user_id']) != str(uid_for_dataset):
            # 如果下载了数据集
            event_log = EventLog(
                from_user_id=e.logs['user_id'],
                to_user_id=uid_for_dataset,
                event_name='download_dataset',
                event_time=get_now_datetime(),
                dataset_id=e.logs['dataset_id']
            )
            db.session.add(event_log)
            db.session.commit()
        cls._logging(e)

    @classmethod
    @judge
    def dataset_preview(cls, dataset_id, uid_for_dataset=''):
        """
        数据集预览
        :param dataset_id: 数据集的ID
        :param uid_for_dataset: 数据集的用户
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'dataset_preview'
        e.logs['dataset_id'] = dataset_id
        if str(e.logs['user_id']) != str(uid_for_dataset):
            event_log = EventLog(
                from_user_id=e.logs['user_id'],
                to_user_id=uid_for_dataset,
                event_name='dataset_preview',
                event_time=get_now_datetime(),
                dataset_id=e.logs['dataset_id']
            )
            from sqlalchemy import desc
            dataset = EventLog.query.filter_by(dataset_id=dataset_id).order_by(desc('event_time')).first()
            time = get_now_datetime() - dataset.event_time
            if not str(time).split('.')[0] == '0:00:00':
                db.session.add(event_log)
                db.session.commit()
        cls._logging(e)

    @classmethod
    @judge
    def update_dataset(cls, dataset_id='',is_updated = False,is_deleted = False,updated_time='',deleted_time=''):
        """
        访问更新数据集页面
        :param dataset_id: 数据集ID
        :param is_updated: 是否点击了更新按钮
        :param is_deleted:  是否点击了删除按钮
        :param updated_time: 点击更新按钮时间
        :param deleted_time: 点击删除按钮时间
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'update_dataset'
        e.logs['dataset_id'] = dataset_id
        e.logs['is_updated'] = is_updated
        e.logs['updated_time'] = updated_time
        e.logs['is_deleted'] = is_deleted
        e.logs['deleted_time'] = deleted_time
        cls._logging(e)

    @classmethod
    @judge
    def create_dataset(cls, dataset_id='',is_created=False,created_time = ''):
        """
        访问创建数据集页面
        :param dataset_id: 数据集ID
        :param is_created: 是否点击了创建
        :param created_time: 创建时间
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'create_dataset'
        e.logs['dataset_id'] = dataset_id
        e.logs['is_created'] = is_created
        e.logs['created_time'] = created_time
        cls._logging(e)

    @classmethod
    @judge
    def user_register(cls,is_succeed=False, register_time='',cellphone='',email=''):
        """
        访问用户注册页面
        :param is_succeed: 是否注册成功
        :param register_time: 注册成功时间
        :param cellphone: 手机号
        :param email: 邮箱
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'user_register'
        e.logs['cellphone'] = cellphone
        e.logs['email'] = email
        e.logs['is_succeed'] = is_succeed
        e.logs['register_time'] = register_time
        cls._logging(e)

    @classmethod
    @judge
    def user_login(cls, is_succeed=False, login_time='', cellphone='', email=''):
        """
        访问用户登录页面
        :param is_succeed: 是否登录成功
        :param login_time: 登录成功时间
        :param cellphone: 手机号
        :param email: 邮箱
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'user_login'
        e.logs['cellphone'] = cellphone
        e.logs['email'] = email
        e.logs['is_succeed'] = is_succeed
        e.logs['login_time'] = login_time
        cls._logging(e)

    @classmethod
    @judge
    def user_logout(cls):
        """
        退出登录
        """
        e = EventLogs()
        e.logs['event_name'] = 'user_logout'
        cls._logging(e)

    @classmethod
    @judge
    def follow_dataset(cls, dataset_id='',uid_for_dataset=''):
        """
        关注数据集
        :param dataset_id: 数据集ID
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'follow_dataset'
        e.logs['dataset_id'] = dataset_id
        cls._logging(e)
        # 如果关注了数据集
        if str(e.logs['user_id']) != str(uid_for_dataset):
            event_log = EventLog(
                from_user_id=e.logs['user_id'],
                to_user_id=uid_for_dataset,
                event_name=e.logs['event_name'],
                event_time=get_now_datetime(),
                dataset_id=e.logs['dataset_id']
            )
            db.session.add(event_log)
            db.session.commit()

    @classmethod
    @judge
    def unfollow_dataset(cls, dataset_id=''):
        """
        取消关注数据集
        :param dataset_id: 数据集ID
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'unfollow_dataset'
        e.logs['dataset_id'] = dataset_id
        cls._logging(e)

    @classmethod
    @judge
    def follow_user(cls, to_user_id=''):
        """
        关注用户
        :param to_user_id: 被关注的用户ID
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'follow_user'
        e.logs['to_user_id'] = to_user_id
        cls._logging(e)
        #存数据库
        if str(e.logs['user_id']) != str(to_user_id):
            event_log = EventLog(
                from_user_id = e.logs['user_id'],
                to_user_id=to_user_id,
                event_name = e.logs['event_name'],
                event_time=get_now_datetime()
            )
            db.session.add(event_log)
            db.session.commit()


    @classmethod
    @judge
    def unfollow_user(cls, to_user_id=''):
        """
        取消关注用户
        :param to_user_id: 被取消关注的用户ID
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'unfollow_user'
        e.logs['to_user_id'] = to_user_id
        cls._logging(e)

    @classmethod
    @judge
    def user_center(cls, to_user_id='',sub_uri=''):
        """
        访问用户空间页
        :param to_user_id: 被访问的用户ID
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'user_center'
        e.logs['to_user_id'] = to_user_id
        e.logs['sub_uri'] = sub_uri
        cls._logging(e)

    @classmethod
    @judge
    def create_group(cls, group_id = '',group_name='', group_introduction='',is_created=False):
        """
        创建群组
        :param to_user_id: 被访问的用户ID
        :return:
        """
        e = EventLogs()
        e.logs['event_name'] = 'create_group'
        e.logs['group_name'] = group_name
        e.logs['group_id'] = group_id
        e.logs['group_introduction'] = group_introduction
        e.logs['is_created'] = is_created
        cls._logging(e)

def get_all_logs(to_user_id=''):
    logs = EventLog.query.filter_by(to_user_id=to_user_id).order_by(desc('event_time'))
    def time_handler(time1,time2):
        tmp =  str(time1 - time2).split(',')
        if 'day' in tmp[0]:
            return tmp[0][0] + '天前'
        else:
            tmps = tmp[0].split(':')
            if int(tmps[0]):
                return tmps[0] + ' 小时前'
            elif int(tmps[1]):
                if tmps[1][0] == '0':
                    return tmps[1][1] + ' 分钟前'
                else:
                    return tmps[1] + ' 分钟前'
            else:
                return tmps[2].split('.')[0] + '秒前'
    logs_data = list()

    for item in logs:
        dataset = Dataset.query.filter_by(udi=item.dataset_id).first()
        if dataset:
            dataset_history = DatasetHistory.query.filter_by(udi=item.dataset_id).order_by(desc('his_created'))
            dataset_version = '当前版本'
            if dataset_history:
                if item.event_time < dataset.updated:
                    for i in dataset_history:
                        # print "his",i.his_created
                        # print "event", item.event_time

                        if item.event_time < i.his_created:
                            dataset_version = '版本 ' + str(i.his_version)
                            continue
            # print "version",dataset_version
            time_diff = time_handler(datetime.datetime.now(),item.event_time)
            u = User.query.filter_by(id=item.from_user_id).first()
            if item.event_name == 'follow_user':
                logs_data.append({
                    'user_id':u.id,
                    'nickname': u.nickname,
                    'dataset_version': dataset_version,
                    'event_name': item.event_name,
                    'time_diff': time_diff
                })
            elif item.event_name != "dataset_preview":
                dataset = Dataset.query.filter_by(udi=item.dataset_id).first()
                logs_data.append({
                    'user_id': u.id,
                    'nickname': u.nickname,
                    'dataset_version': dataset_version,
                    'dataset_id':dataset.udi,
                    'title': dataset.title,
                    'event_name': item.event_name,
                    'time_diff': time_diff
                })
            else:
                dataset = Dataset.query.filter_by(udi=item.dataset_id).first()
                logs_data.append({
                    'user_id': u.id,
                    'nickname': u.nickname,
                    'dataset_version': dataset_version,
                    'dataset_id': dataset.udi,
                    'title': dataset.title,
                    'event_name': item.event_name,
                    'time_diff': time_diff
                })
    datasets = Dataset.query.filter_by(author_id=to_user_id)
    # 统计datasets访问总量
    views = 0
    for dataset in datasets:
        if dataset.views == None:
            dataset.views = 1
        views += dataset.views
    return logs_data,views

def get_dataset_logs(dataset_id=''):
    logs = EventLog.query.filter_by(dataset_id=dataset_id).order_by(desc('event_time'))
    def time_handler(time1,time2):
        tmp =  str(time1 - time2).split(',')
        if 'day' in tmp[0]:
            return tmp[0][0] + '天前'
        else:
            tmps = tmp[0].split(':')
            if int(tmps[0]):
                return tmps[0] + ' 小时前'
            elif int(tmps[1]):
                if tmps[1][0] == '0':
                    return tmps[1][1] + ' 分钟前'
                else:
                    return tmps[1] + ' 分钟前'
            else:
                return tmps[2].split('.')[0] + '秒前'
    logs_data = list()

    for item in logs:
        dataset = Dataset.query.filter_by(udi=item.dataset_id).first()
        if dataset:
            dataset_history = DatasetHistory.query.filter_by(udi=item.dataset_id).order_by(desc('his_created'))
            dataset_version = '当前版本'
            if dataset_history:
                if item.event_time < dataset.updated:
                    for i in dataset_history:
                        # print "his",i.his_created
                        # print "event", item.event_time

                        if item.event_time < i.his_created:
                            dataset_version = '版本 ' + str(i.his_version)
                            continue
            # print "version",dataset_version
            time_diff = time_handler(datetime.datetime.now(),item.event_time)
            u = User.query.filter_by(id=item.from_user_id).first()
            print item.event_name
            if item.event_name == 'download_dataset':
                dataset = Dataset.query.filter_by(udi=item.dataset_id).first()
                logs_data.append({
                    'user_id': u.id,
                    'nickname': u.nickname,
                    'dataset_version': dataset_version,
                    'dataset_id': dataset.udi,
                    'title': dataset.title,
                    'event_name': item.event_name,
                    'time_diff': time_diff
                })
            elif item.event_name == "dataset_preview":
                dataset = Dataset.query.filter_by(udi=item.dataset_id).first()
                logs_data.append({
                    'user_id': u.id,
                    'nickname': u.nickname,
                    'dataset_version': dataset_version,
                    'dataset_id':dataset.udi,
                    'title': dataset.title,
                    'event_name': item.event_name,
                    'time_diff': time_diff
                })
            else:
                pass

    return logs_data