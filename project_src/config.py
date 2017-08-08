# -*- coding: utf8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))

SITE_NAME = 'CORE'

TEST = 'debug'

USER_LOG_PATH = 'user_log.log'

UPLOAD_FOLDER = basedir + '/tmp/'
ALLOWED_IMG_EXTENSIONS = ['png','jpg','jpeg','gif','PNG','JPG','JPEG','GIF']
DATASET_FILE_EXTENSION = {'data':['csv','json','xlsx','CSV','JSON','XLSX'],
'doc':['doc','docx','pages','DOC','DOCX','PAGES'],
'sheet':['numbers','NUMBERS','xls','XLS'],
'ppt':['ppt','pptx','key','PPT','PPTX','KEY'],
'zip':['zip','rar','7z','iso','tar','ZIP','RAR','7Z','ISO','TAR'],
'img':['jpg','jpeg','png','gif','bmp','svg','webp','JPG','JPEG','PNG','GIF','BMP','SVG','WEBP'],
'pdf':['pdf','PDF'],
'code':['htm','html','xhtml','xml','js','py','md','HTM','HTML','XHTML','XML','JS','PY','MD']}

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

OPENID_PROVIDERS = [
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}]

os.environ.setdefault('DATABASE_URL', 'mysql://root:123456@192.168.88.61:3306/core')

if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = ('sqlite:///' + os.path.join(basedir, 'app.db') +
                               '?check_same_thread=False')
else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_RECORD_QUERIES = True
WHOOSH_BASE = os.path.join(basedir, 'search.db')

# slow database query threshold (in seconds)
DATABASE_QUERY_TIMEOUT = 0.5

# email server
MAIL_SERVER = 'mail.hugedata.com.cn'  # your mailserver
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME ='core@hugedata.com.cn'
MAIL_PASSWORD = '123456'

# available languages
LANGUAGES = {
    'en': 'English',
    'es': 'Español'
}

# microsoft translation service
MS_TRANSLATOR_CLIENT_ID = ''  # enter your MS translator app id here
MS_TRANSLATOR_CLIENT_SECRET = ''  # enter your MS translator app secret here

# administrator list
ADMINS = ['core@hugedata.com.cn']

# pagination
POSTS_PER_PAGE = 10
MAX_SEARCH_RESULTS = 50


#geetest极验验证
# PC_GEETEST_ID = '0a001db07af5a7d59c4c9e3433483895'
# PC_GEETEST_KEY = 'eef611b28513b931046aa36f7ca68b6d'
PC_GEETEST_ID = '8863b9014464367e34416c3127c3900b'
PC_GEETEST_KEY = '89990195ddffdbf2fd3a9df451d45f38'

CORE_API = "http://127.0.0.1:8888"
CORE_SECRET_KEY = "FbU5H93Rc8oQjV1ffZ5kIohEkMSzsAx84Zt3ECbJZAowboSY9ff0F5m7bzOlrDL"
CORE_APP_ID = "8adbeb47-42b0-48f0-8c51-2928b650ecfd"
CORE_PREFIX_ID = "thudmp"

# 邀请码
INVITATION_CODE='170429'