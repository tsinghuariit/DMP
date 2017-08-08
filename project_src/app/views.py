# coding=utf-8

import logging
import os
import random
import re
import time
import urllib
from datetime import datetime

from flask import (abort, flash, g, jsonify, redirect, render_template,
                   request, send_from_directory, session, url_for)
from flask_babel import gettext
from flask_login import current_user, login_required, login_user, logout_user
from flask_sqlalchemy import get_debug_queries
from guess_language import guessLanguage
from sqlalchemy.sql import or_
from sqlalchemy import desc
from werkzeug.utils import secure_filename

from app import app, babel, db, lm
from config import (DATABASE_QUERY_TIMEOUT, LANGUAGES, MAX_SEARCH_RESULTS,
                    PC_GEETEST_ID, PC_GEETEST_KEY, POSTS_PER_PAGE)
from data import *
from geetest import GeetestLib

from .emails import captcha_email, follower_notification
from .forms import (ContactForm, DatasetForm, EditForm, EmailCaptcha,
                    GetbackPasswd, LoginForm, PostForm, RegistrationForm,
                    SearchForm, SmsCaptcha, EditDatasetForm, flash_form_errors,
                    GroupForm, InvitationCode)
from .models import Category, Contact, Dataset, DatasetHistory, Post, User, Application,Group,GroupApplication,EventLog,GroupInvitation
from .sms import rand_sms_captcha, send_sms
from .translate import microsoft_translate

from event_log import EventLogs,get_now_str,get_all_logs,get_dataset_logs
from . import options

import os
import random
import time
import json
import logging
import urllib


@lm.token_loader
def get_auth_token():
    return User.query.get(int(id))


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = get_locale()


@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= DATABASE_QUERY_TIMEOUT:
            app.logger.warning(
                "SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" %
                (query.statement, query.parameters, query.duration,
                 query.context))
    return response


@app.errorhandler(403)
def not_allow_error(error):
    return render_template('403.html'), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def home():
    EventLogs.view_home()
    return render_template('dmp-index.html')


@app.route('/core', methods=['GET', 'POST'])
def core():
    return render_template('home.html')


@app.route('/dmp')
def dmp():
    return render_template('dmp-index.html')


@app.route('/dmp/features')
def dmp_features():
    return render_template('dmp-features.html')

@app.route('/admin')
def admin():
    return render_template('base-admin.html')


@app.route('/bcp')
def bcp():
    return render_template('bcp.html')


@app.route('/dataset')
@app.route('/datasets')
def dataset():
    return redirect('/datasets/search')


@app.route('/datasets/search')
@app.route('/datasets/search', methods=['GET', 'POST'])
@app.route('/datasets/search/<int:page>', methods=['GET', 'POST'])
def dataset_search(page=1):
    parent_cates = Category.query.filter(
        Category.parent_id == 0).order_by(Category.type).all()
    cates = Category.query.filter(
        Category.parent_id > 0).order_by(desc(Category.sort)).all()
    cates_map = {}
    category_count(cates)
    for c in cates:
        cates_map[str(c.id)] = c.name

    cate_url = request.args.get('cate', '')
    cate_args = cate_url.split(',') if cate_url else []

    cate_parent_map = {
        10001: u'authority',
        11001: u'subject',
        12001: u'datatype',
        13001: u'expert',
        14001: u'kind',
        15001: u'org'
    }

    cate_obj = {}
    cate_parent_ids = []

    for a in cate_args:
        if a:
            p, c = a.split(':')
            cate_obj[cate_parent_map[int(p)]] = c
            cate_parent_ids.append(int(p))

    if cate_parent_ids:
        parent_cates = [p for p in parent_cates if p.id not in cate_parent_ids]

    search = request.args.get('search', '').encode('utf-8')
    sort = request.args.get('sort', 'updated')
    datasets = Dataset.query.filter(Dataset.title.like('%'+ search.decode('utf-8') + '%'))
    for k in cate_obj:
        if cate_obj[k]:
            datasets = datasets.filter(
                getattr(Dataset, k + '_id') == cate_obj[k])

    datasets = datasets.order_by(desc(
        sort if sort in ['published', 'updated'] else 'updated'))
    pagination = datasets.paginate(page, POSTS_PER_PAGE, False)
    datasets = datasets.paginate(page, POSTS_PER_PAGE, False)
    EventLogs.view_dataset_list(page_num=page,sort_type=sort,cate=cate_args,keywords=search,dataset_num=1)
    return render_template('dataset-search.html',
                           cates=cates,
                           parent_cates=parent_cates,
                           datasets=datasets,
                           cate_obj=cate_obj,
                           cate_url=cate_url,
                           cate_args=cate_args,
                           search=search,
                           sort=sort,
                           cates_map=cates_map,
                           pagination=pagination)


def category_count(category_list):
    for l in category_list:
        cate = Category.query.filter(Category.id == l.id).first()
        if str(l.parent_id) == '10001':
            cate.sort=Dataset.query.filter(Dataset.authority_id == l.id).count()
            db.session.add(cate)
        elif str(l.parent_id) == '11001':
            cate.sort = Dataset.query.filter(Dataset.subject_id == l.id).count()
        elif str(l.parent_id) == '12001':
            cate.sort = Dataset.query.filter(Dataset.datatype_id == l.id).count()
        elif str(l.parent_id) == '13001':
            cate.sort = Dataset.query.filter(Dataset.expert_id == l.id).count()
        elif str(l.parent_id) == '14001':
            cate.sort = Dataset.query.filter(Dataset.kind_id == l.id).count()
        elif str(l.parent_id) == '15001':
            cate.sort = Dataset.query.filter(Dataset.org_id == l.id).count()
    db.session.commit()



@app.route('/datasets/item/<path:id>')
@app.route('/datasets/item/<path:id>/meta')
def dataset_item_meta(id):
    dataset = Dataset.query.filter_by(udi=id).first()

    #统计数据集访问量
    if dataset.views == None:
        dataset.views = 1
    dataset.views += 1
    if dataset.signature == None:
        file_path = os.path.join(
            app.config['UPLOAD_FOLDER'], dataset.datasource
        )
        dataset.signature = ds_sha2(file_path)
    db.session.add(dataset)
    db.session.commit()
    EventLogs.view_dataset_detail(dataset_id=id,sub_uri='meta')
    fileFull = dataset.datasource.split('/').pop()
    fileName = dataset.datasource.split('/').pop().split('.').pop(0)
    fileExt = dataset.datasource.split('/').pop().split('.').pop()
    ext = app.config['DATASET_FILE_EXTENSION']
    return render_template('dataset-meta.html', dataset=dataset, fileFull=fileFull, fileName=fileName, fileExt=fileExt, ext=ext)


@app.route('/datasets/item/<path:id>/notify')
def dataset_item_notify(id):
    dataset = Dataset.query.filter_by(udi=id).first()
    # EventLogs.view_dataset_detail(dataset_id=id, sub_uri='notify')
    fileFull = dataset.datasource.split('/').pop()
    fileName = dataset.datasource.split('/').pop().split('.').pop(0)
    fileExt = dataset.datasource.split('/').pop().split('.').pop()
    ext = app.config['DATASET_FILE_EXTENSION']
    return render_template('dataset-notify.html', dataset=dataset, fileFull=fileFull, fileName=fileName, fileExt=fileExt, ext=ext)


@app.route('/datasets/item/<path:id>/preview')
def dataset_item_preview(id):
    dataset = Dataset.query.filter_by(udi=id).first()
    EventLogs.view_dataset_detail(dataset_id=id, sub_uri='preview')
    fileFull = dataset.datasource.split('/').pop()
    fileName = dataset.datasource.split('/').pop().split('.').pop(0)
    fileExt = dataset.datasource.split('/').pop().split('.').pop()
    ext = app.config['DATASET_FILE_EXTENSION']
    return render_template('dataset-preview.html', dataset=dataset, fileFull=fileFull, fileName=fileName, fileExt=fileExt, ext=ext)


@app.route('/datasets/item/<path:id>/analysis')
def dataset_item_analysis(id):
    dataset = Dataset.query.filter_by(udi=id).first()
    EventLogs.view_dataset_detail(dataset_id=id, sub_uri='analysis')
    return render_template('dataset-analysis.html', dataset=dataset)


@app.route('/datasets/item/<path:id>/download')
def dataset_item_download(id):
    dataset = Dataset.query.filter_by(udi=id).first()
    dataset_his = DatasetHistory.query.filter_by(
        udi=id).order_by(DatasetHistory.his_id.desc()).all()
    EventLogs.view_dataset_detail(dataset_id=id, sub_uri='download')
    fileFull = dataset.datasource.split('/').pop()
    fileName = dataset.datasource.split('/').pop().split('.').pop(0)
    fileExt = dataset.datasource.split('/').pop().split('.').pop()
    logs_data = get_dataset_logs(dataset_id=id)
    for log in logs_data[:5]:
        for i in log:
            print i," : ",log[i]
        print '*'*10
    ext = app.config['DATASET_FILE_EXTENSION']
    return render_template('dataset-download.html', dataset=dataset, dataset_his=dataset_his, fileFull=fileFull, fileName=fileName, fileExt=fileExt, ext=ext, logs_data=logs_data)


@app.route('/datasets/item/<path:id>/rq')
def dataset_item_rq_anay(id):
    dataset = Dataset.query.filter_by(udi=id).first()
    uploads = os.path.join(
        app.config['UPLOAD_FOLDER'], dataset.datasource
    )
    EventLogs.view_dataset_detail(dataset_id=id,sub_uri='rq')
    return redirect('/demo/raqsoft/guide/jsp/analyse.jsp?dfxParams=csvFile='+uploads)


@app.route('/datasets/item/<path:id>/auth')
@login_required
def dataset_item_auth(id):
    dataset = Dataset.query.filter_by(udi=id).first()
    apply_waiting=dataset.get_waiting_applications()
    applied=dataset.get_applied_applications()
    EventLogs.view_dataset_detail(dataset_id=id, sub_uri='auth')
    return render_template('dataset-auth.html',dataset=dataset,applied=applied,apply_waiting=apply_waiting)

@app.route('/datasets/item/<path:id>/download/<string:path>/<string:prefix>/<string:surfix>/<string:timestamp>/<string:filename>/version/<int:version>', methods=['GET', 'POST'])
@app.route('/datasets/item/<path:id>/download/<string:path>/<string:prefix>/<string:surfix>/<string:timestamp>/<string:filename>', methods=['GET', 'POST'])
@login_required
def dataset_download(id, path, prefix, surfix, timestamp, filename, version=None):
    dataset = Dataset.query.filter_by(udi=id).first()
    if not dataset or not dataset.is_authorized(g.user):
        return abort(403)
    if version:
        dataset_his = DatasetHistory.query.filter(
            DatasetHistory.udi == id, DatasetHistory.his_version == version).first()
        if not dataset_his:
            return abort(404)
    uploads = os.path.join(
        app.config['UPLOAD_FOLDER'], path, prefix, surfix, timestamp
    )
    EventLogs.view_dataset_detail(dataset_id=id, sub_uri='downlaoded',is_downloaded=True,uid_for_dataset=dataset.author_id)
    return send_from_directory(directory=uploads, filename=filename,as_attachment=True)


@app.route('/raw')
def raw_index():
    return render_template('raw/index.html')

@app.route('/raw/colors')
def raw_colors_template():
    return render_template('raw/colors.html')

@app.route('/raw/dimensions')
def raw_dimensions_template():
    return render_template('raw/dimensions.html')


@app.route('/register/set/password', methods=['GET', 'POST'])
def register_set_password():
    form = RegistrationForm()
    cellphone = session['cellphone']
    if request.method == 'POST':
        nickname = form.email.data.split('@')[0]
        return validate_register(dict(nickname=nickname, email=form.email.data, password=form.password.data, cellphone=cellphone, confirm=form.confirm.data))
    EventLogs.user_register(is_succeed=False)
    return render_template('register.html', form=form,cellphone=cellphone)


@app.route('/register/success', methods=['GET'])
def register_success():
    return render_template('register-success.html')


@app.route('/rest/get/code', methods=["GET"])
def get_code():
    gt = GeetestLib(PC_GEETEST_ID, PC_GEETEST_KEY)
    status = gt.pre_process()
    session[gt.GT_STATUS_SESSION_KEY] = status
    response_str = gt.get_response_str()
    return response_str


def validate_register(resp):
    form = SmsCaptcha()
    if resp['password'] is None or resp['password'] == "":
        flash(gettext(u'密码不能不为空.'))
        return redirect(url_for('register_set_password'))
    if not User.make_valid_cellphone(resp['cellphone']):
        flash(gettext(u'手机号不能为空或手机号已被注册'))
        return redirect(url_for('register_set_password'))
    if not User.make_valid_email(email=resp['email']):
        flash(gettext(u'邮箱不能为空或邮箱已被注册'))
        return redirect(url_for('register_set_password'))
    if resp['password'] != resp['confirm']:
        flash(gettext(u'两次密码输入不一致'))
        return redirect(url_for('register_set_password'))
    if not re.match(r'^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$', resp['email']):
        flash(gettext(u'您的电子邮件格式不正确！'))
        return redirect(url_for('register'))
    if not re.match(r'(13\d|14[57]|15[^4,\D]|17[678]|18\d)\d{8}|170[059]\d{7}', resp['cellphone']) or len(resp['cellphone']) != 11:
        flash(gettext(u'您的手机号格式不正确！'))
        return redirect(url_for('register_set_password'))
    user = User(nickname=resp['nickname'], cellphone=resp['cellphone'], email=resp['email'], password=resp['password'])
    db.session.add(user)
    db.session.commit()
    login_user(user)
    EventLogs.user_register(is_succeed=True, cellphone=resp['cellphone'], email=resp['cellphone'], register_time=get_now_str())
    EventLogs.user_login(is_succeed=True, email=resp['email'], cellphone=resp['cellphone'])
    return redirect(url_for('register_success'))



@app.route('/register/captcha/sms',  methods=['GET', 'POST'])
def register_send_captcha_sms():
    form = SmsCaptcha()
    if request.method == 'POST':
        cellphone = request.form['cellphone']
        if cellphone == '':
            flash(u'手机号不能为空！')
            return render_template('register_send_sms.html', form=form)
        if not User.make_valid_cellphone(cellphone):
            flash(u'你的手机号已注册，请登录')
            return redirect(url_for('login'))
        
        #新加内容
        session['cellphone'] = cellphone
        return render_template('register_validate_sms.html', form=form)
    
    #新加内容
    return render_template('register_send_sms.html', form=form)   
        #取消验证码校验以及发送验证码过程
#         captcha = rand_sms_captcha()
#         gt = GeetestLib(PC_GEETEST_ID, PC_GEETEST_KEY)
#         challenge = request.form[gt.FN_CHALLENGE]
#         validate = request.form[gt.FN_VALIDATE]
#         seccode = request.form[gt.FN_SECCODE]
#         status = session[gt.GT_STATUS_SESSION_KEY]
#         if status:
#             result = gt.success_validate(challenge, validate, seccode)
#         else:
#             result = gt.failback_validate(challenge, validate, seccode)
#         if result:
#             send_sms(cellphone, captcha)
#             session['captcha'] = captcha
#             session['cellphone'] = cellphone
#             return render_template('register_validate_sms.html', form=form)
#         else:
#             flash(gettext(u'验证码不正确！'))
#             return render_template('register_send_sms.html', form=form)
#     return render_template('register_send_sms.html', form=form)


@app.route('/register/captcha/sms/validate', methods=['GET', 'POST'])
def register_validate_captcha_sms():
    form = SmsCaptcha()
    if request.method == 'POST':
        
        #新加内容
        return redirect(url_for('register_set_password'))
    
    #取消验证码校验过程
#         if str(session['captcha']) == str(form.captcha.data):
#             return redirect(url_for('register_set_password'))
#         else:
#             flash(u'验证码错误')
#             return  render_template('register_validate_sms.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        return validate_login({
            "user_id": user_id,
            "email": user_id,
            "cellphone": user_id,
            "password": password,
            "remember_me": form.remember_me.data
        })
    EventLogs.user_login()
    return render_template('login.html',
                           title=u'请登录',
                           form=form)


def validate_login(resp):
    if resp['user_id'] is None or resp['user_id'] == "" or resp['password'] is None or resp['password'] == "":
        flash(gettext('Invalid login. Please try again.'))
        return redirect(url_for('login'))
    user = User.query.filter(
        or_(User.email == resp['email'], User.cellphone == resp['cellphone'])).first()
    if user is None:
        flash(gettext(u"账号不存在！请检查重试！"))
        return redirect(url_for('login'))
    user = User.query.filter(or_(User.email == resp['email'], User.cellphone == resp[
                             'cellphone']), User.password == resp['password']).first()
    if user is None:
        flash(gettext(u'密码错误！'))
        return redirect(url_for('login'))
    remember_me = False
    if 'remember_me' in resp:
        remember_me = resp['remember_me']
    login_user(user, remember=remember_me)
    EventLogs.user_login(is_succeed=True,email=resp['email'],cellphone=resp['cellphone'])
    return redirect(request.args.get('next') or url_for('dataset'))


@app.route('/logout')
@login_required
def logout():
    EventLogs.user_logout()
    logout_user()
    return redirect(url_for('dataset'))


@app.route('/forget')
def forget():
    return render_template('forget.html')


@app.route('/about')
def about():
    EventLogs.view_about()
    return render_template('about-core.html')


@app.route('/about/lab')
def about_lab():
    EventLogs.view_about(sub_uri='lab')
    return render_template('about-lab.html')


@app.route('/about/center')
def about_center():
    EventLogs.view_about(sub_uri='center')
    return render_template('about-center.html')


@app.route('/about/team')
def about_team():
    EventLogs.view_about(sub_uri='team')
    return render_template('about-team.html')

@app.route('/join')
def join():
    EventLogs.view_join()
    return render_template('join.html')

def generate_udi():
    return app.config["CORE_PREFIX_ID"] + '/' + str(int((time.time() - 3600 * 24 * 365 * 44) * 100))


@app.route('/datasets/add', methods=['GET', 'POST'])
@login_required
def dataset_add():
    user = User.query.filter_by(id=g.user.id).first()
    if not user.invitation_active:
        return redirect(url_for('invitation_code_query'))
    form = DatasetForm()
    if form.validate_on_submit():
        udi = generate_udi()
        f = form.datasource.data
        filedir = os.path.join(
            app.config['UPLOAD_FOLDER'], 'files', udi, str(time.time()))
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        filename = filedir.split(
            app.config['UPLOAD_FOLDER'])[-1] + '/' + secure_filename(f.filename)
        file_path = os.path.join(
            app.config['UPLOAD_FOLDER'], filename
        )
        f.save(file_path)
        hash_obj = ds_sha2(file_path)
        dataset = Dataset(
            udi=udi,
            title=request.form['title'],
            datasource=filename,
            author_id=g.user.id,
            contact='',
            desc=request.form['desc'],
            signature = hash_obj,
            authority_id=request.form['authority'],
            kind_id=request.form['kind'],
            expert_id=request.form['expert'],
            subject_id=request.form['subject'],
            datatype_id=request.form['datatype'],
            org_id=request.form['org']
        )
        db.session.add(dataset)
        db.session.commit()
        EventLogs.create_dataset(dataset_id=udi,is_created=True)

        CoreAPI.create_dataset(udi.split("/")[1],hash_obj)
        flash(gettext('数据集已成功提交保存'))
        return redirect(url_for('dataset_item_meta',id=udi))
    elif request.method == "POST":
        flash_form_errors(form)
    EventLogs.create_dataset()
    return render_template('dataset-add.html', form=form, action="Add")


@app.route('/invitation/code/query',methods=['GET','POST'])
@login_required
def invitation_code_query():
    form = InvitationCode()
    user = User.query.filter_by(id=g.user.id).first()
    if request.method == 'POST':
        invitation_code = request.form['invitation_code']
        gt = GeetestLib(PC_GEETEST_ID, PC_GEETEST_KEY)
        challenge = request.form[gt.FN_CHALLENGE]
        validate = request.form[gt.FN_VALIDATE]
        seccode = request.form[gt.FN_SECCODE]
        status = session[gt.GT_STATUS_SESSION_KEY]
        if status:
            result = gt.success_validate(challenge, validate, seccode)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        if result:
            if invitation_code == app.config['INVITATION_CODE']:
                user.invitation_active = True
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('dataset_add'))
            else:
                flash(u'你的邀请码无效')
                return render_template('invitation_code_quert.html', form=form)
        else:
            flash(gettext(u'验证码不正确！'))
            return render_template('invitation_code_quert.html', form=form)

    return render_template('invitation_code_quert.html', form=form)


@app.route('/datasets/edit/<path:id>', methods=['GET', 'POST'])
@login_required
def dataset_edit(id):
    dataset = Dataset.query.filter(
        Dataset.udi == id, Dataset.author_id == g.user.id).first()

    if not dataset.is_editable(g.user):
        return abort(403)
    form = EditDatasetForm(obj=dataset)
    if form.validate_on_submit():
        udi = dataset.udi
        f = form.datasource.data
        if f:
            filedir = os.path.join(
                app.config['UPLOAD_FOLDER'], 'files', udi, str(time.time()))
            if not os.path.exists(filedir):
                os.makedirs(filedir)
            filename = filedir.split(
                app.config['UPLOAD_FOLDER'])[-1] + '/' + secure_filename(f.filename)
            file_path = os.path.join(
                app.config['UPLOAD_FOLDER'], filename
            )
            f.save(file_path)
            hash_obj = ds_sha2(file_path)
        else:
            filename = dataset.datasource
            file_path = os.path.join(
                app.config['UPLOAD_FOLDER'], filename
            )
            hash_obj = ds_sha2(file_path)

        dataset_his = DatasetHistory(dataset)
        db.session.add(dataset_his)

        dataset.title = request.form['title']
        dataset.datasource = filename
        dataset.contact = ''
        dataset.signature = hash_obj
        dataset.desc = request.form['desc']
        dataset.authority_id = request.form['authority']
        dataset.kind_id = request.form['kind']
        dataset.expert_id = request.form['expert']
        dataset.subject_id = request.form['subject']
        dataset.datatype_id = request.form['datatype']
        db.session.add(dataset)
        db.session.commit()
        flash(gettext('数据集已成功保存修改'))
        EventLogs.update_dataset(dataset_id=id,is_updated=True)
        return redirect(url_for('dataset_item_meta', id=id))
    else:
        flash_form_errors(form)
    EventLogs.update_dataset(dataset_id=id)
    return render_template('dataset-edit.html', form=form, action="Edit", dataset=dataset)


@app.route('/dataset/delete', methods=['POST'])
@login_required
def dataset_delete():
    if request.method == 'POST':
        id = request.form['id']
        dataset = Dataset.query.filter(Dataset.udi == id,Dataset.author_id==g.user.id).first()
        if dataset:
            dataset_history = DatasetHistory(dataset)
            db.session.add(dataset_history)
            db.session.delete(dataset)
            db.session.commit()
            EventLogs.update_dataset(dataset_id=id, is_updated=True,is_deleted=True)
            return 'successful!'
        else:
            return 'error!'


@app.route('/user/<int:id>/dataset')
@app.route('/user/<int:id>/dataset/<int:page>')
def user_dataset(id, page=1):
    user = User.query.filter_by(id=id).first()
    datasets = Dataset.query.filter_by(author_id=user.id)
    datasets = datasets.order_by(desc('published'))
    datasets = datasets.paginate(page, POSTS_PER_PAGE, False)
    EventLogs.user_center(to_user_id=id,sub_uri='dataset')
    return render_template('user-dataset.html', user=user, datasets=datasets, CATES_MAP=CATES_MAP)



@app.route('/user/<int:id>/activity')
@app.route('/user/<int:id>/activity/<int:page>')
@login_required
def user_activity(id, page=1):
    user = User.query.filter_by(id=id).first()
    logs_data,views = get_all_logs(to_user_id=id)
    if user is None:
        flash(gettext(u'用户不存在！'))
        return redirect(url_for('home'))
    EventLogs.user_center(to_user_id=id, sub_uri='activity')
    return render_template('user-activity.html', user=user,logs_data=logs_data,views=views)


@app.route('/user/<int:id>/group')
@app.route('/user/<int:id>/group/<int:page>')
@login_required
def user_group(id, page=1):
    user = User.query.filter_by(id=id).first()
    EventLogs.user_center(to_user_id=id, sub_uri='group')
    return render_template('user-group.html', user=user)

@app.route('/user/<int:id>/joinedgroup')
@app.route('/user/<int:id>/joinedgroup/<int:page>')
@login_required
def user_joinedgroup(id, page=1):
    user = User.query.filter_by(id=id).first()
    if user.id != current_user.id:
        flash("no authority!")
        return redirect(url_for('home'))
    groups_applied = Group.query.join(GroupApplication,GroupApplication.group_id==Group.id).filter(GroupApplication.applier_id==g.user.id,GroupApplication.status!=3)
    groups_joined = Group.query.join(GroupApplication,GroupApplication.group_id==Group.id).filter(GroupApplication.applier_id==g.user.id,GroupApplication.status==3)
    EventLogs.user_center(to_user_id=id, sub_uri='group')
    return render_template('user-joinedgroup.html', user=user,groups_applied=groups_applied,groups_joined=groups_joined)

@app.route('/user/<int:id>/datasetfav')
@app.route('/user/<int:id>/datasetfav/<int:page>')
@login_required
def user_datasetfav(id, page=1):
    user = User.query.filter_by(id=id).first()
    datasets = user.datasets_following
    datasets = datasets.paginate(page, POSTS_PER_PAGE, False)
    EventLogs.user_center(to_user_id=id, sub_uri='datasetfav')
    return render_template('user-datasetfav.html', user=user, datasets=datasets, CATES_MAP=CATES_MAP)


@app.route('/user/<int:id>/following')
@app.route('/user/<int:id>/following/<int:page>')
@login_required
def user_following(id, page=1):
    user = User.query.filter_by(id=id).first()
    users = user.follower_users(user)
    users = users.paginate(page, POSTS_PER_PAGE, False)
    EventLogs.user_center(to_user_id=id, sub_uri='following')
    return render_template('user-following.html', user=user, users=users, CATES_MAP=CATES_MAP)


@app.route('/user/<int:id>/follower')
@app.route('/user/<int:id>/follower/<int:page>')
@login_required
def user_follower(id, page=1):
    user = User.query.filter_by(id=id).first()
    users = user.followed_users(user)
    users = users.paginate(page, POSTS_PER_PAGE, False)
    EventLogs.user_center(to_user_id=id, sub_uri='follower')
    return render_template('user-follower.html', user=user, users=users, CATES_MAP=CATES_MAP)

@app.route('/user/<int:id>/auth')
@app.route('/user/<int:id>/auth/<int:page>')
@login_required
def user_auth(id, page=1):
    user = User.query.filter_by(id=id).first()
    users = User.query.join(Application,Application.applier_id==User.id).filter(Application.author_id==id)
    users = users.paginate(page, POSTS_PER_PAGE, False)
    if users == None:
        users = []
    EventLogs.user_center(to_user_id=id, sub_uri='auth')
    return render_template('user-auth.html', user=user, users=users, CATES_MAP=CATES_MAP)

@app.route('/user/<int:id>/authby')
@app.route('/user/<int:id>/authby/<int:page>')
@login_required
def user_authby(id, page=1):
    user = User.query.filter_by(id=id).first()
    datasets = Dataset.query.join(Application,Application.dataset_udi==Dataset.udi).filter(Application.applier_id==id,Application.status==3)
    datasets = datasets.paginate(page, POSTS_PER_PAGE, False)
    noauth=False
    if datasets == None:
        datasets = []
        noauth=True
    EventLogs.user_center(to_user_id=id, sub_uri='authby')
    return render_template('user-authby.html', user=user, datasets=datasets, CATES_MAP=CATES_MAP,noauth=noauth)

@app.route('/user/<int:id>')
@app.route('/user/<int:id>/<int:page>')
@login_required
def user(id, page=1):
    user = User.query.filter_by(id=id).first()
    if user is None:
        flash(gettext(u'用户不存在！'))
        return redirect(url_for('home'))
    datasets = Dataset.query.filter_by(author_id=user.id)
    #统计datasets访问总量
    views = 0
    for dataset in datasets:
        if dataset.views == None:
            dataset.views = 1
        views += dataset.views
    return render_template('user-activity.html',
                           user=user,
                           datasets=datasets,views=views)

@app.route('/avatar/<path:id>/<string:path>/<string:filename>/', methods=['GET', 'POST'])
@login_required
def avatar_show(id, path, filename):
    avatar_img = os.path.join(
        app.config['UPLOAD_FOLDER'], 'avatar', id, path
    )
    return send_from_directory(directory=avatar_img, filename=filename)


@app.route('/edit')
@app.route('/edit/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditForm(g.user.id)
    if form.is_submitted():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        g.user.cellphone = form.cellphone.data
        if request.form['org'] != '__None':
            g.user.org_id = request.form['org']
        if request.form['expert'] != '__None':
            g.user.expert_id = request.form['expert']
        if request.form['professional'] != '__None':
            g.user.professional_id = request.form['professional']
        avatar_f=request.files['avatar']
        # f_size=len(avatar_f.read())
        # if f_size > 500 *1024: #上传头像不能超过500KB
        #     abort(413)
        if avatar_f:
            flag = '.' in avatar_f.filename and avatar_f.filename.rsplit('.',1)[1] in app.config['ALLOWED_IMG_EXTENSIONS']
            if not flag:
                flash(u'只允许上传png,jpg,jpeg,gif格式的文件')
                return redirect(url_for('edit_profile'))
            filedir = os.path.join(
                app.config['UPLOAD_FOLDER'],'avatar',str(g.user.id),str(time.time())
            )
            if not os.path.exists(filedir):
                os.makedirs(filedir)
            filename = filedir.split(
                app.config['UPLOAD_FOLDER'])[-1]  + '/' + secure_filename(avatar_f.filename)
            avatar_f.save(os.path.join(
                app.config['UPLOAD_FOLDER'], filename
            ))
            g.user.avatarsource ="/" + filename
            g.user.avatarsource=g.user.avatarsource.replace('\\', '/')
        if not re.match(r'(13\d|14[57]|15[^4,\D]|17[678]|18\d)\d{8}|170[059]\d{7}', g.user.cellphone) or len(g.user.cellphone) != 11:
            flash(gettext(u'您的手机号格式不正确！'))
            return redirect(url_for('edit_profile'))
        db.session.add(g.user)
        db.session.commit()
        flash(gettext(u'保存成功.'))
        return redirect(url_for('edit_profile'))
    elif request.method != "POST":
        avatar_img =g.user.avatarsource
        form.nickname.data = g.user.nickname
        form.cellphone.data = g.user.cellphone
        form.about_me.data = g.user.about_me
        form.org_id = g.user.org_id
        form.expert_id = g.user.expert_id
        form.professional_id = g.user.professional_id
        org = Category.query.filter_by(id=g.user.org_id).first()
        expert = Category.query.filter_by(id=g.user.expert_id).first()
        professional = Category.query.filter_by(id=g.user.professional_id).first()
    return render_template('edit-profile.html',avatar_img=avatar_img, form=form, org=org,
                            expert=expert, professional=professional)


@app.route('/edit/password', methods=['GET', 'POST'])
@login_required
def edit_password():
    form = EditForm(g.user.id)
    if form.is_submitted():
        if form.new_passwd.data == form.now_passwd.data:
            flash(gettext(u'新密码与旧密码相同！请重新输入新密码！'))
            return redirect(url_for('edit_password'))
        if form.new_passwd.data == form.confirm_passwd.data:
            if g.user.password == form.now_passwd.data:
                g.user.password = form.new_passwd.data
                db.session.add(g.user)
                db.session.commit()
                flash(gettext(u'密码修改成功!'))
                return redirect(url_for('edit_password'))
            else:
                flash(gettext(u'现密码错误！'))
                return redirect(url_for('edit_password'))
        else:
            flash(u'两次密码输入不一致')
            return redirect(url_for('edit_password'))

    return render_template('edit-password.html', form=form)


@app.route('/follow', methods=['POST'])
@login_required
def follow():
    if request.method =='POST':
        id=request.form['id']
        user = User.query.filter_by(id=id).first()
        if user is None:
            flash(u'用户不存在!')
            return 'error'
        if user == g.user:
            flash(gettext(u'你不能关注你自己!'))
            return 'error'
        u = g.user.follow(user)
        if u is None:
            flash(gettext('Cannot follow %s.' % user.nickname))
            return 'error'
        db.session.add(u)
        db.session.commit()
        flash(gettext(u'你已经关注了%s!' % user.nickname))
        EventLogs.follow_user(to_user_id=id)
        return 'successful'
    else:
        abort(403)


@app.route('/unfollow', methods=['POST'])
@login_required
def unfollow():
    if request.method == 'POST':
        id = request.form['id']
        user = User.query.filter_by(id=id).first()
        if user is None:
            flash(u'用户 %s 不存在！' % user.nickname)
            return 'error'
        u = g.user.unfollow(user)
        if u is None:
            flash(gettext('不能关注 %s.' % user.nickname))
            return 'error'
        db.session.add(u)
        db.session.commit()
        flash(gettext('你已取消关注 %s' % user.nickname))
        EventLogs.unfollow_user(to_user_id=id)
        return 'successful'
    else:
        abort(403)

@app.route('/follow_dataset', methods=['POST'])
@login_required
def follow_dataset():
    if request.method == 'POST':
        id = request.form['id']
        dataset = Dataset.query.filter_by(udi=id).first()
        if dataset is None:
            flash(u'数据集不存在！')
            return 'error'
        ''' couldn't follow one's own dataset'''
        if dataset.author_id == g.user.id:
            flash(gettext(u'你不能关注自己的数据集!'))
            return 'error'
        u = g.user.follow_dataset(dataset)
        if u is None:
            flash(gettext(u'数据集关注错误.'))
            return 'error'
        db.session.add(u)
        db.session.commit()
        flash(gettext(u'你已经关注数据集%s'%dataset.title))
        EventLogs.follow_dataset(dataset_id=id,uid_for_dataset=dataset.author_id)
        return 'successful'
    else:
        abort(403)

@app.route('/unfollow_dataset', methods=['POST'])
@login_required
def unfollow_dataset():
    if request.method == 'POST':
        id = request.form['id']
        dataset = Dataset.query.filter_by(udi=id).first()
        if dataset is None:
            flash(u'数据集不存在')
            return 'error'
        u = g.user.unfollow_dataset(dataset)
        if u is None:
            flash(gettext(u'取消关注数据集错误'))
            return 'error'
        db.session.add(u)
        db.session.commit()
        flash(gettext(u'你已经取消关注数据集'))
        EventLogs.unfollow_dataset(dataset_id=id)
        return 'successful'
    else:
        abort(403)

# @app.route('/delete/<int:id>')
# @login_required
# def delete(id):
#     post = Post.query.get(id)
#     if post is None:
#         flash('Post not found.')
#         return redirect(url_for('home'))
#     if post.author.id != g.user.id:
#         flash('You cannot delete this post.')
#         return redirect(url_for('home'))
#     db.session.delete(post)
#     db.session.commit()
#     flash('Your post has been deleted.')
#     return redirect(url_for('home'))
#
#
# @app.route('/search', methods=['POST'])
# @login_required
# def search():
#     if not g.search_form.validate_on_submit():
#         return redirect(url_for('home'))
#     return redirect(url_for('search_results', query=g.search_form.search.data))
#
#
# @app.route('/search_results/<query>')
# @login_required
# def search_results(query):
#     results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
#     return render_template('search_results.html',
#                            query=query,
#                            results=results)
#
#
# @app.route('/translate', methods=['POST'])
# @login_required
# def translate():
#     return jsonify({
#         'text': microsoft_translate(
#             request.form['text'],
#             request.form['sourceLang'],
#             request.form['destLang'])})

@app.route('/datasets/apply/<path:id>')
@login_required
def apply_for_authorization(id):
    dataset = Dataset.query.filter_by(udi=id).first()
    if dataset is None:
        flash('Dataset %s not found.' % id)
        return redirect(url_for('home'))
    status = g.user.apply_dataset_status(dataset)
    if dataset.author_id == g.user.id:
        flash(gettext('You needn\'t apply for your own dataset!'))
        return redirect(url_for('user', id=g.user.id))
    elif status>1:
        flash(gettext('You have applied it before '))
        return redirect(url_for('user', id=g.user.id))
    u = g.user.apply(dataset,dataset.author)
    if u is None:
        flash(gettext('Cannot apply %(id)s.', id=id))
        return redirect(url_for('user', id=g.user.id))
    db.session.add(u)
    db.session.commit()
    flash(gettext('You have applied authorization of %(id)s.',
                  id=id))
    return redirect(url_for('dataset_item_download',id=id))

@app.route('/auth/modify/<path:id>',methods=['POST'])
@login_required
def accept_application(id):
    application = Application.query.filter_by(id=id).first()
    new_status = request.form['status']
    if application is None:
        flash('Application %s not found.' % id)
        return redirect(url_for('home'))
    if application.author_id != g.user.id:
        flash(gettext('You cant\'t modify other\'s dataset!'))
        flash(gettext(application.author_id))
        return redirect(url_for('user_auth',id=application.author_id))
    saveApplicationStatus(application,new_status)
    flash(gettext('You have authorized %(user)s to access %(id)s.',
        user=application.author.nickname, id=id))
    return ''#redirect(url_for('dataset_item_meta',id=application.dataset_udi))

def saveApplicationStatus(apply, status):
    apply.status=status
    db.session.add(apply)
    db.session.commit()


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'GET':
        form = ContactForm()
        EventLogs.view_feedback()
        return render_template('feedback.html', form=form)
    else:
        form = ContactForm()
        cellphone = form.cellphone.data
        email = form.email.data
        report = form.report.data
        gt = GeetestLib(PC_GEETEST_ID, PC_GEETEST_KEY)
        challenge = request.form[gt.FN_CHALLENGE]
        validate = request.form[gt.FN_VALIDATE]
        seccode = request.form[gt.FN_SECCODE]
        status = session[gt.GT_STATUS_SESSION_KEY]
        if status:
            result = gt.success_validate(challenge, validate, seccode)
        else:
            EventLogs.view_feedback()
            result = gt.failback_validate(challenge, validate, seccode)
        if result:
            contact = Contact(cellphone=cellphone, email=email, report=report)
            db.session.add(contact)
            db.session.commit()
            EventLogs.view_feedback(is_succeed=True,email=email,cellphone=cellphone,report=report)
            return render_template('feedback-success.html')
        else:
            flash(gettext(u'验证码不正确！'))
            EventLogs.view_feedback()
            return redirect(url_for('feedback'))


@app.route('/contact')
def contact():
    EventLogs.view_contact()
    return render_template('contact.html')


@app.route('/rest/captcha/sms', methods=['POST'])
def send_captcha_sms():
    if request.method == 'POST':
        form = SmsCaptcha()
        cellphone = request.form['cellphone']
        captcha = rand_sms_captcha()
        gt = GeetestLib(PC_GEETEST_ID, PC_GEETEST_KEY)
        challenge = request.form[gt.FN_CHALLENGE]
        validate = request.form[gt.FN_VALIDATE]
        seccode = request.form[gt.FN_SECCODE]
        status = session[gt.GT_STATUS_SESSION_KEY]
        
        #新加内容
        session['cellphone'] = cellphone
        return render_template('getback_passwd_validate_sms.html', form=form)
        
        #取消短信验证码发送过程
#         if status:
#             result = gt.success_validate(challenge, validate, seccode)
#         else:
#             result = gt.failback_validate(challenge, validate, seccode)
#         if result:
#             send_sms(cellphone, captcha)
#             session['captcha'] = captcha
#             session['cellphone'] = cellphone
#             return render_template('getback_passwd_validate_sms.html', form=form)
#         else:
#             flash(gettext(u'验证码不正确！'))
#             return render_template('getback_passwd_sms.html', form=form)


@app.route('/captcha/sms/validate', methods=['GET', 'POST'])
def validate_captcha_sms():
    form = SmsCaptcha()
    if request.method == 'POST':
        
        #新加内容
        return redirect(url_for('sms_edit_passwd'))
    
#         if str(session['captcha']) == str(form.captcha.data):
#             return redirect(url_for('sms_edit_passwd'))
#         else:
#             return redirect(url_for('validate_captcha_sms'))

    return render_template('getback_passwd_sms.html', form=form)


@app.route('/rest/captcha/email', methods=["POST"])
def send_captcha_email():
    form = EmailCaptcha()
    if request.method == 'POST':
        captcha = rand_captcha()
        email = form.email.data
        captcha_email(email, captcha)
        session['email'] = email
        session['captcha'] = captcha
        return ''


@app.route('/captcha/email/validate', methods=['GET', 'POST'])
def validate_captcha_email():
    form = EmailCaptcha()
    if request.method == 'POST':
        if session['captcha'] == form.captcha.data:
            return redirect(url_for('email_edit_passwd'))
        else:
            return redirect(url_for('validate_captcha_email'))
    return render_template('getback_passwd_validate_email.html', form=form)


@app.route('/user/password/getback/sms', methods=['GET', 'POST'])
def sms_edit_passwd():
    form = GetbackPasswd()
    if 'cellphone' in session:
        if form.is_submitted():
            new_passwd = form.new_passwd.data
            confirm_passwd = form.confirm_passwd.data
            cellphone = session['cellphone']
            if new_passwd == confirm_passwd:
                user = User.query.filter_by(cellphone=cellphone).first()
                user.password = new_passwd
                db.session.commit()
                flash(gettext(u'密码修改成功！'))
                return redirect(url_for('login'))
            else:
                flash(gettext(u'两次输入的密码不一样'))
                return redirect(url_for('sms_edit_passwd'))
    else:
        flash(gettext(u'你刚才的访问受限！'))
        return redirect(url_for('validate_captcha_sms'))
    return render_template('getback_passwd_edit_sms.html', form=form)


@app.route('/user/password/getback/email', methods=['GET', 'POST'])
def email_edit_passwd():
    form = GetbackPasswd()
    if 'email' in session:
        if form.is_submitted():
            new_passwd = form.new_passwd.data
            confirm_passwd = form.confirm_passwd.data
            email = session['email']
            if new_passwd == confirm_passwd:
                user = User.query.filter_by(email=email).first()
                user.password = new_passwd
                db.session.commit()
                flash(gettext(u'密码修改成功！'))
                return redirect(url_for('login'))
            else:
                flash(gettext(u'两次输入的密码不一样'))
                return redirect(url_for('email_edit_passwd'))
    else:
        flash(gettext(u'你刚才的访问受限！'))
        return redirect(url_for('validate_captcha_email'))
    return render_template('getback_passwd_edit_email.html', form=form)


def rand_captcha():
    num = random.randint(100, 1000)
    capa = chr(random.randint(65, 90))
    capb = chr(random.randint(65, 90))
    low = chr(random.randint(97, 122))
    captcha = capa + str(num) + capb + low
    return captcha


@app.route('/notifications')
@login_required
def notifications_all():
    return render_template('notifications-all.html')

@app.route('/notifications/dataset')
@login_required
def notifications_dataset():
    return render_template('notifications-dataset.html')

@app.route('/notifications/group')
@login_required
def notifications_group():
    invitations = GroupInvitation.query.filter_by(invited_id=g.user.id)
    return render_template('notifications-group.html',invitations=invitations)

# @app.route('/group/<path:id>')
# def group(id):
#     group = Group.query.filter_by(id=id).first()
#     return render_template('group.html',group=group)

@app.route('/group/<path:id>')
@app.route('/group/<path:id>/dataset')
def group_dataset(id):
    group = Group.query.filter_by(id=id).first()
    group_main_subject = group.all_datasets_main_subject()
    datasets = group.all_datasets()
    # datasets_members = Dataset.query.join(GroupApplication,GroupApplication.applier_id==Dataset.author_id).filter(GroupApplication.group_id==id,GroupApplication.status==3)
    return render_template('group-dataset.html',group=group,datasets=datasets,group_main_subject=group_main_subject)

@app.route('/group/<path:id>/member')
@login_required
def group_member(id):
    group = Group.query.filter_by(id=id).first()
    group_main_subject = group.all_datasets_main_subject()
    users = User.query.join(GroupApplication,GroupApplication.applier_id==User.id).filter(GroupApplication.group_id==id,GroupApplication.status==3)
    applying_users = User.query.join(GroupApplication,GroupApplication.applier_id==User.id).filter(GroupApplication.group_id==id,GroupApplication.status!=3)
    return render_template('group-member.html',group=group,users=users,group_main_subject=group_main_subject,applying_users=applying_users)


@app.route('/group/member/add/<path:id>',methods=['GET'])
@login_required
def group_member_add(id):
    group = Group.query.filter_by(id=id).first()
    group_main_subject = group.all_datasets_main_subject()
    if group==None or group.manager_id!=g.user.id:
        flash('not manager of this group')
        return redirect(url_for("group_member",id=id))
    user_list = User.query.filter_by()#g.user.followers
    user_choosed = []
    return render_template('group-member-add.html',group=group,user_choosed=user_choosed,user_list=user_list,group_main_subject=group_main_subject)


@app.route('/group/member/add/search/<path:follow>/<path:key>',methods=['GET','POST'])
@login_required
def group_member_add_data(id):
    group = Group.query.filter_by(id=id).first()
    group_main_subject = group.all_datasets_main_subject()
    if group==None or group.manager_id!=g.user.id:
        flash('not manager of this group')
        return redirect(url_for("group_member",id=id))
    user_list = g.user.followers
    user_choosed = []
    return render_template('group-member-add.html',group=group,user_choosed=user_choosed,user_list=user_list,group_main_subject=group_main_subject)


@app.route('/group/member/remove/<path:id>/<path:userid>',methods=['POST','GET'])
@login_required
def group_member_remove(id,userid):
    group = Group.query.filter_by(id=id).first()
    if group==None or group.manager_id!=g.user.id:
        flash('not manager of this group')
        return redirect(url_for("group_member",id=id))
    apply = GroupApplication.query.filter_by(applier_id=userid,group_id=id).first()
    apply.status=1
    db.session.add(apply)
    db.session.commit()
    return redirect(url_for("group_dataset",id=id))

@app.route('/group/member/auth_manager/<path:id>/<path:userid>',methods=['POST','GET'])
@login_required
def group_member_auth_manager(id,userid):
    group = Group.query.filter_by(id=id).first()
    if group==None or group.manager_id != g.user.id:
        flash('not manager of this group')
        return redirect(url_for("group",id=id))
    group.manager_id = userid
    db.session.add(group)
    db.session.commit()
    return redirect(url_for("group_dataset",id=id))

@app.route('/group/member/exit/<path:id>',methods=['POST','GET'])
@login_required
def group_member_exit(id):
    group = Group.query.filter_by(id=id).first()
    apply = GroupApplication.query.filter_by(applier_id=g.user.id,group_id=id).first()
    apply.status=4
    db.session.add(apply)
    db.session.commit()
    return redirect(url_for("group_dataset",id=id))

@app.route('/group/member/invite/<path:group_id>/<path:user_id>',methods=['POST','GET'])
@login_required
def group_member_invite(user_id,group_id):
    group = Group.query.filter_by(id=group_id).first()
    if group.manager_id!=g.user.id:
        flash('not manager of this group')
        return redirect(url_for("group_dataset",id=group_id))
    invitation = GroupInvitation()
    invitation.group_id = group_id
    invitation.invited_id=user_id
    invitation.status=0
    invitation.created_at=datetime.utcnow()
    db.session.add(invitation)
    db.session.commit()
    return redirect(url_for("group_member_add",id=group_id))
@app.route('/group/member/invite/accept/<path:id>/',methods=['GET','POST'])
@login_required
def group_member_accept_invite(id):
    groupInvitation = GroupInvitation.query.filter_by(id=id).first()
    if groupInvitation==None:
        flash('no invitation')
        return redirect(url_for("group_dataset",id=groupInvitation.group_id))
    if groupInvitation.invited_id!=g.user.id:
        flash('not user of this invitation')
        return redirect(url_for("group_dataset",id=groupInvitation.group_id))
    groupInvitation.status=1
    db.session.add(invitation)
    db.session.commit()
    if GroupApplication.query.filter_by(applier_id=g.user.id,group_id=id).count()>0:
        application = GroupApplication.query.filter_by(applier_id=g.user.id,group_id=id).first()
        application.init_apply()
        application.status = 3
        db.session.add(application)
        db.session.commit()
    else:
        application = GroupApplication(g.user.id,group)
        application.status = 3
        db.session.add(application)
        db.session.commit()
    return "ok"
@app.route('/group/member/invite/reject/<path:id>/',methods=['GET','POST'])
@login_required
def group_member_reject_invite(id):
    groupInvitation = GroupInvitation.query.filter_by(id=id).first()
    if groupInvitation.invited_id!=g.user.id:
        flash('not user of this invitation')
        return redirect(url_for("group_dataset",id=groupInvitation.group_id))
    groupInvitation.status=2
    db.session.add(invitation)
    db.session.commit()
    return "ok"
@app.route('/group/member/apply/accept/<path:id>/',methods=['GET','POST'])
@login_required
def group_member_accept_apply(id):
    apply = Application.query.filter_by(id=id).first()
    if apply==None:
        flash('no apply')
        return redirect(url_for("group_dataset",id=apply.group_id))
    if apply.manager_id!=g.user.id:
        flash('not manager of this apply')
        return redirect(url_for("group_dataset",id=apply.group_id))
    apply.status=4
    db.session.add(apply)
    db.session.commit()
    return "ok"
@app.route('/group/member/apply/reject/<path:id>/',methods=['GET','POST'])
@login_required
def group_member_reject_apply(id):
    apply = GroupApplication.query.filter_by(id=id).first()
    if apply.manager_id!=g.user.id:
        flash('not manager of this apply')
        return redirect(url_for("group_dataset",id=apply.group_id))
    db.session.add(apply)
    db.session.commit()
    return "ok"

@app.route('/group/member/invite/members<path:group_id>/',methods=['POST'])
@login_required
def group_members_invite(user_id,group_id):
    group = Group.query.filter_by(id=group_id).first()
    if group.manager_id!=g.user.id:
        flash('not manager of this group')
        return redirect(url_for("group_dataset",id=group_id))
    for user_id in request.args.get('users'):
        group_member_invite(user_id,group_id)
    return "ok"

@app.route('/group/member/apply/<path:id>',methods=['POST','GET'])
@login_required
def group_member_apply(id):
    group = Group.query.filter_by(id=id).first()
    if str(group.auth_type)=='10006':
        flash('could apply selfish group')
        return redirect(url_for("group_dataset",id=id))
    if GroupApplication.query.filter_by(applier_id=g.user.id,group_id=id).count()>0:
        application = GroupApplication.query.filter_by(applier_id=g.user.id,group_id=id).first()
        application.init_apply()
        db.session.add(application)
        db.session.commit()
    else:
        application = GroupApplication(g.user.id,group)
        db.session.add(application)
        db.session.commit()
    return redirect(url_for("group_dataset",id=id))

@app.route('/group/edit/<path:id>',methods=['GET','POST'])
@login_required
def group_edit(id):
    group = Group.query.filter_by(id=id).first()
    group_main_subject = group.all_datasets_main_subject()
    if group.manager_id != g.user.id:
        flash('no authority!')
        return redirect(url_for('group_dataset',id=id))
    form = GroupForm(obj=group)
    if form.validate_on_submit():
        group.name = form.name.data
        group.introduction=request.form['introduction']
        group.auth_type=request.form['authority']
        avatar_f=request.files['avatar']
        if avatar_f:
            flag = '.' in avatar_f.filename and avatar_f.filename.rsplit('.',1)[1] in app.config['ALLOWED_IMG_EXTENSIONS']
            if not flag:
                flash(u'只允许上传png,jpg,jpeg,gif格式的文件')
                return redirect(url_for('edit_profile'))
            filedir = os.path.join(
                app.config['UPLOAD_FOLDER'],'avatar',str(g.user.id),str(time.time())
            )
            if not os.path.exists(filedir):
                os.makedirs(filedir)
            filename = filedir.split(
                app.config['UPLOAD_FOLDER'])[-1]  + '/' + secure_filename(avatar_f.filename)
            avatar_f.save(os.path.join(
                app.config['UPLOAD_FOLDER'], filename
            ))
            avatarsource ="/" + filename
            group.avatarsource=avatarsource.replace('\\', '/')
        db.session.add(group)
        db.session.commit()
        flash(gettext('数据集已成功提交保存'))
        return redirect(url_for('group_dataset',id=group.id))
    elif request.method == "POST":
        flash_form_errors(form)
        render_template('group-edit.html',form=form, action="Edit",group=group)
    group_main_subject = group.all_datasets_main_subject()
    return render_template('group-edit.html',form=form, action="Edit",group=group,group_main_subject=group_main_subject)

@app.route('/group/add',methods=['GET', 'POST'])
@login_required
def group_add():
    form = GroupForm()
#     group_main_subject = group.all_datasets_main_subject()
    if form.validate_on_submit():
        group = Group(
            name=request.form['name'],
            introduction=request.form['introduction'],
            auth_type=request.form['authority'],
            creater=g.user,
            avatarsource=''
        )
        avatar_f=request.files['avatar']
        if avatar_f:
            flag = '.' in avatar_f.filename and avatar_f.filename.rsplit('.',1)[1] in app.config['ALLOWED_IMG_EXTENSIONS']
            if not flag:
                flash(u'只允许上传png,jpg,jpeg,gif格式的文件')
                return redirect(url_for('edit_profile'))
            filedir = os.path.join(
                app.config['UPLOAD_FOLDER'],'avatar',str(g.user.id),str(time.time())
            )
            if not os.path.exists(filedir):
                os.makedirs(filedir)
            filename = filedir.split(
                app.config['UPLOAD_FOLDER'])[-1]  + '/' + secure_filename(avatar_f.filename)
            avatar_f.save(os.path.join(
                app.config['UPLOAD_FOLDER'], filename
            ))
            avatarsource ="/" + filename
            group.avatarsource=avatarsource.replace('\\', '/')
        db.session.add(group)
        db.session.commit()
        application = GroupApplication(g.user.id,group)
        application.status=3
        db.session.add(application)
        db.session.commit()
        flash(gettext('群组创建成功'))
        EventLogs.create_group(group_id=group.id,group_name=group.name,group_introduction=group.introduction,is_created=True)
        return redirect(url_for('group_dataset',id=group.id))
    elif request.method == "POST":
        flash_form_errors(form)
    EventLogs.create_group()
    return render_template('group-add.html',form=form, action="Add",group=None,group_main_subject=None)

@app.route('/rest/dataset/show', methods=['POST'])
def dataset_show():
    json_request= json.loads(request.data)
    id = json_request['udi']
    dataset = Dataset.query.filter_by(udi=id).first()
    title = dataset.title
    file_path = app.config['UPLOAD_FOLDER'] + dataset.datasource
    data_frame = DataApi.read_dataset(file_path)
    if data_frame is None:
        return json.dumps({'code': '500'})
    else:
        data_index = data_frame.index
        columns = data_frame.columns

        data = []
        data_json = json.loads(data_frame.to_json(orient='index'))
        for index, value in data_json.iteritems():
            data.append(value)
        data_dict = {
            'data': data,
            'title': title
        }
        EventLogs.dataset_preview(dataset_id=id, uid_for_dataset=dataset.author_id)
        return json.dumps(data_dict,encoding='utf-8')

@app.route('/test', methods=['GET'])
def user_log():
    import hashlib
    with open("/Users/Jason/Desktop/data/multivariate.csv", 'rb') as f:
        sha1obj = hashlib.md5()
        sha1obj.update(f.read())
        hash = sha1obj.hexdigest()
    return hash

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

dated_url_timestamp = str(time.time())
def dated_url_for(endpoint, **values):
    if endpoint == 'static' or endpoint == '.static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint.replace('.', ''), filename)
            values['q'] = dated_url_timestamp #int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
