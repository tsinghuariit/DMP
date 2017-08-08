# -*- coding: utf-8 -*-  


from .event_log import judge
import pandas as pd
from pandas.io.json import json_normalize
import json
import os
import requests
from . import app
import hashlib
CATES = [
    {
        'name': u'所属院系或单位',
        'id': 'department',
        'items': [
            {
                'name': u'清华大学信息科学技术学院',
                'id': 'dep1'
            },
            {
                'name': u'清华大学数据科学研究院',
                'id': 'dep2'
            },
            {
                'name': u'清华大数据产业联合会',
                'id': 'dep3'
            },
            {
                'name': u'清华数据创新基地(清数D-Lab)',
                'id': 'dep4'
            }
        ]
    },
    {
        'name': u'数据空间分类',
        'id': 'kind',
        'items': [
            {
                'name': u'研究者',
                'id': 'kind1'
            },
            {
                'name': u'研究项目',
                'id': 'kind2'
            },
            {
                'name': u'组织和机构',
                'id': 'kind3'
            },
        ]
    },
    {
        'name': u'专家学者',
        'id': 'expert',
        'items': [
            {
                'name': u'两院院士',
                'id': 'expert1'
            },
            {
                'name': u'长江学者',
                'id': 'expert2'
            },
            {
                'name': u'千人计划',
                'id': 'expert3'
            },
            {
                'name': u'青年千人计划',
                'id': 'expert4'
            }
        ]
    },
    {
        'name': u'学科分类',
        'id': 'subject',
        'items': [
            {
                'name': u'信息科学与技术',
                'id': 'subject1'
            },
            {
                'name': u'生物医学',
                'id': 'subject2'
            },
            {
                'name': u'经济管理',
                'id': 'subject3'
            },
            {
                'name': u'数学',
                'id': 'subject4'
            },
            {
                'name': u'物理',
                'id': 'subject5'
            },
            {
                'name': u'材料',
                'id': 'subject6'
            },
            {
                'name': u'城市',
                'id': 'subject7'
            },
            {
                'name': u'政务',
                'id': 'subject8'
            }
        ]
    },
    {
        'name': u'类型分类',
        'id': 'datatype',
        'items': [
            {
                'name': u'科学计算',
                'id': 'datatype1'
            },
            {
                'name': u'研究报告',
                'id': 'datatype2'
            },
            {
                'name': u'专项调查',
                'id': 'datatype3'
            },
            {
                'name': u'统计年鉴',
                'id': 'datatype4'
            }
        ]
    },
    {
        'name': u'授权分类',
        'id': 'authority',
        'items': [
            {
                'name': u'公开',
                'id': 'authority1'
            },
            {
                'name': u'私密',
                'id': 'authority2'
            },
            {
                'name': u'有限授信',
                'id': 'authority3'
            }
        ]
    }
]

CATES_MAP = {}
for c in CATES:
    for i in c['items']:
        CATES_MAP[i['id']] = i['name']

DATASETS = [
    {
        'metadata': [
            {
                'id': 'udi',
                'name': u'数据集唯一标识',
                'value': 'udi:tsing-dep1/pm2.5-2015'
            },
            {
                'id': 'title',
                'name': u'标题',
                'value': u'全国主要城市空气质量数据PM2.5'
            },
            {
                'id': 'published',
                'name': u'发布日期',
                'value': '2016-05-16'
            },
            {
                'id': 'datasource',
                'name': u'数据资源',
                'value': ['/static/echart/demo/pm2.5.json']
            },
            {
                'id': 'author',
                'name': u'作者',
                'value': u'王老师'
            },
            {
                'id': 'contact',
                'name': u'联系方式',
                'value': u'wls@tsinghua.edu.cn'
            },
            {
                'id': 'desc',
                'name': u'描述',
                'value': u'该数据集包含2015年全国环境监测数据PM2.5的地区分布'
            },
            {
                'id': 'department',
                'name': u'所属单位',
                'value': 'dep1'
            },
            {
                'id': 'authority',
                'name': u'数据授权',
                'value': 'authority1'
            },
            {
                'id': 'kind',
                'name': u'数据空间分类',
                'value': 'kind1'
            },
            {
                'id': 'expert',
                'name': u'专家学者',
                'value': 'expert2'
            },
            {
                'id': 'subject',
                'name': u'学科分类',
                'value': 'subject1'
            },
            {
                'id': 'datatype',
                'name': u'类型分类',
                'value': 'datatype1'
            }
        ]
    },
    {
        'metadata': [
            {
                'id': 'udi',
                'name': u'数据集唯一标识',
                'value': 'udi:tsing-dep1/hg-2015'
            },
            {
                'id': 'title',
                'name': u'标题',
                'value': u'2002全国宏观经济指标'
            },
            {
                'id': 'published',
                'name': u'发布日期',
                'value': '2016-05-26'
            },
            {
                'id': 'datasource',
                'name': u'数据资源',
                'value': ['/static/echart/demo/mix-timeline-finance.json']
            },
            {
                'id': 'author',
                'name': u'作者',
                'value': u'李老师'
            },
            {
                'id': 'contact',
                'name': u'联系方式',
                'value': u'lls@tsinghua.edu.cn'
            },
            {
                'id': 'desc',
                'name': u'描述',
                'value': u'该数据集包含2002年全国宏观经济指标'
            },
            {
                'id': 'department',
                'name': u'所属单位',
                'value': 'dep2'
            },
            {
                'id': 'authority',
                'name': u'数据授权',
                'value': 'authority1'
            },
            {
                'id': 'kind',
                'name': u'数据空间分类',
                'value': 'kind3'
            },
            {
                'id': 'expert',
                'name': u'专家学者',
                'value': 'expert1'
            },
            {
                'id': 'subject',
                'name': u'学科分类',
                'value': 'subject2'
            },
            {
                'id': 'datatype',
                'name': u'类型分类',
                'value': 'datatype1'
            }
        ]
    },
    {
        'metadata': [
            {
                'id': 'udi',
                'name': u'数据集唯一标识',
                'value': 'udi:tsing-dep2/399e8'
            },
            {
                'id': 'title',
                'name': u'标题',
                'value': u'2015年上证指数'
            },
            {
                'id': 'published',
                'name': u'发布日期',
                'value': '2016-03-26'
            },
            {
                'id': 'datasource',
                'name': u'数据资源',
                'value': ['/static/echart/demo/candlestick-sh-2015.json']
            },
            {
                'id': 'author',
                'name': u'作者',
                'value': u'李老师'
            },
            {
                'id': 'contact',
                'name': u'联系方式',
                'value': u'lls@tsinghua.edu.cn'
            },
            {
                'id': 'desc',
                'name': u'描述',
                'value': u''
            },
            {
                'id': 'department',
                'name': u'所属单位',
                'value': 'dep3'
            },
            {
                'id': 'authority',
                'name': u'数据授权',
                'value': 'authority1'
            },
            {
                'id': 'kind',
                'name': u'数据空间分类',
                'value': 'kind1'
            },
            {
                'id': 'expert',
                'name': u'专家学者',
                'value': 'expert2'
            },
            {
                'id': 'subject',
                'name': u'学科分类',
                'value': 'subject1'
            },
            {
                'id': 'datatype',
                'name': u'类型分类',
                'value': 'datatype1'
            }
        ]
    },
    {
        'metadata': [
            {
                'id': 'udi',
                'name': u'数据集唯一标识',
                'value': 'udi:tsing-dep3/778839'
            },
            {
                'id': 'title',
                'name': u'标题',
                'value': u'某地区蒸发量和降水量数据'
            },
            {
                'id': 'published',
                'name': u'发布日期',
                'value': '2016-03-26'
            },
            {
                'id': 'datasource',
                'name': u'数据资源',
                'value': ['/static/echart/demo/bar1.json']
            },
            {
                'id': 'author',
                'name': u'作者',
                'value': u'李老师'
            },
            {
                'id': 'contact',
                'name': u'联系方式',
                'value': u'lls@tsinghua.edu.cn'
            },
            {
                'id': 'desc',
                'name': u'描述',
                'value': u''
            },
            {
                'id': 'department',
                'name': u'所属单位',
                'value': 'dep3'
            },
            {
                'id': 'authority',
                'name': u'数据授权',
                'value': 'authority1'
            },
            {
                'id': 'kind',
                'name': u'数据空间分类',
                'value': 'kind1'
            },
            {
                'id': 'expert',
                'name': u'专家学者',
                'value': 'expert2'
            },
            {
                'id': 'subject',
                'name': u'学科分类',
                'value': 'subject1'
            },
            {
                'id': 'datatype',
                'name': u'类型分类',
                'value': 'datatype1'
            }
        ]
    },
    {
        'metadata': [
            {
                'id': 'udi',
                'name': u'数据集唯一标识',
                'value': 'udi:ts-2030/sz-2015'
            },
            {
                'id': 'title',
                'name': u'标题',
                'value': u'北京空气质量指数API'
            },
            {
                'id': 'published',
                'name': u'发布日期',
                'value': '2016-03-26'
            },
            {
                'id': 'datasource',
                'name': u'数据资源',
                'value': ['/static/echart/demo/line-aqi.json']
            },
            {
                'id': 'author',
                'name': u'作者',
                'value': u'李老师'
            },
            {
                'id': 'contact',
                'name': u'联系方式',
                'value': u'lls@tsinghua.edu.cn'
            },
            {
                'id': 'desc',
                'name': u'描述',
                'value': u''
            },
            {
                'id': 'department',
                'name': u'所属单位',
                'value': 'dep3'
            },
            {
                'id': 'authority',
                'name': u'数据授权',
                'value': 'authority1'
            },
            {
                'id': 'kind',
                'name': u'数据空间分类',
                'value': 'kind1'
            },
            {
                'id': 'expert',
                'name': u'专家学者',
                'value': 'expert2'
            },
            {
                'id': 'subject',
                'name': u'学科分类',
                'value': 'subject1'
            },
            {
                'id': 'datatype',
                'name': u'类型分类',
                'value': 'datatype1'
            }
        ]
    },
    {
        'metadata': [
            {
                'id': 'udi',
                'name': u'数据集唯一标识',
                'value': 'udi:tsing-20388/8930039'
            },
            {
                'id': 'title',
                'name': u'标题',
                'value': u'深圳月最低生活费用组成数据'
            },
            {
                'id': 'published',
                'name': u'发布日期',
                'value': '2016-03-26'
            },
            {
                'id': 'datasource',
                'name': u'数据资源',
                'value': ['/static/echart/demo/bar-waterfall.json']
            },
            {
                'id': 'author',
                'name': u'作者',
                'value': u'李老师'
            },
            {
                'id': 'contact',
                'name': u'联系方式',
                'value': u'lls@tsinghua.edu.cn'
            },
            {
                'id': 'desc',
                'name': u'描述',
                'value': u''
            },
            {
                'id': 'department',
                'name': u'所属单位',
                'value': 'dep3'
            },
            {
                'id': 'authority',
                'name': u'数据授权',
                'value': 'authority1'
            },
            {
                'id': 'kind',
                'name': u'数据空间分类',
                'value': 'kind1'
            },
            {
                'id': 'expert',
                'name': u'专家学者',
                'value': 'expert2'
            },
            {
                'id': 'subject',
                'name': u'学科分类',
                'value': 'subject1'
            },
            {
                'id': 'datatype',
                'name': u'类型分类',
                'value': 'datatype1'
            }
        ]
    },
]


# 支持文件类型
# 用16进制字符串的目的是可以知道文件头是多少字节
# 各种文件头的长度不一样，少半2字符，长则8字符
import struct
def typeList():
    return {
        "5B75726C": 'csv',
        'D0CF11E0': 'xlsx'
    }


# 字节码转16进制字符串
def bytes2hex(bytes):
    num = len(bytes)
    hexstr = u""
    for i in range(num):
        t = u"%x" % bytes[i]
        if len(t) % 2:
            hexstr += u"0"
        hexstr += t
    return hexstr.upper()


# 获取文件类型
def filetype(filename):
    binfile = open(filename, 'rb')  # 必需二制字读取
    tl = typeList()
    ftype = 'unknown'
    for hcode in tl.keys():
        numOfBytes = len(hcode) / 2  # 需要读多少字节
        binfile.seek(0)  # 每次读取都要回到文件头，不然会一直往后读取
        hbytes = struct.unpack_from("B" * numOfBytes, binfile.read(numOfBytes))  # 一个 "B"表示一个字节
        f_hcode = bytes2hex(hbytes)
        if f_hcode == hcode:
            ftype = tl[hcode]
            break
    binfile.close()
    return ftype

class DataApi(object):


    @staticmethod
    def _get_csv_data(file_path):
        data_frame = pd.read_csv(file_path)
        return data_frame

    @staticmethod
    def _get_excel_data(file_path):
        data_frame = pd.read_excel(file_path)
        return data_frame

    @staticmethod
    def _get_json_data(file_path):
        with open(file_path,'r') as f:
            data = json.loads(f.read())
        data_frame = json_normalize(data)
        return data_frame

    @staticmethod
    def read_dataset(file_path):
        data_frame = None
        assert type(file_path) == type(unicode())
        if not os.path.exists(file_path):
            return data_frame
            # raise IOError('No such file or directory: %s' % file_path)
        file_type = file_path.split('/')[-1].split('.')[-1]
        if file_type == 'json':
            data_frame = DataApi._get_json_data(file_path)
        elif file_type == 'xlsx':
            data_frame = DataApi._get_excel_data(file_path)
        elif file_type == 'csv':
            data_frame = DataApi._get_csv_data(file_path)
        else:
            pass
        return data_frame

class CoreAPI(object):
    CoreApi = app.config["CORE_API"]
    SecretKey = app.config["CORE_SECRET_KEY"]
    PrefixId = app.config["CORE_PREFIX_ID"]
    AppId = app.config["CORE_APP_ID"]

    @staticmethod
    def get_udi():

        SecretKey = CoreAPI.SecretKey
        PrefixId = CoreAPI.PrefixId
        AppId = CoreAPI.AppId
        api_url = CoreAPI.CoreApi +  "/v1/app/" + AppId + "/prefix/" + PrefixId + "?SecretKey=" + SecretKey
        r = requests.get(api_url)
        jsoninfo = r.json()
        print(jsoninfo)

    @staticmethod
    @judge
    def create_dataset(suffix_id,hash_md5):
        api_url = CoreAPI.CoreApi + "/v1/app/" + CoreAPI.AppId + "/prefix/" + CoreAPI.PrefixId + "/suffix/create?SecretKey=" + CoreAPI.SecretKey
        post_data = {
            "Index": "1",
            "Signature": hash_md5,
            "SuffixId": suffix_id,
            "Type": "URL",
            "Version": "1.0",
            "TTL": "ttl-",
            "Permission": "TEST",
            "Value": "http://core.sist.tsinghua.edu.cn/datasets/item/" + CoreAPI.PrefixId + "/" + suffix_id
        }

        post_data = json.dumps(post_data)
        r = requests.post(api_url,post_data)
        print(r.json())

    @staticmethod
    @judge
    def update_dataset(suffix_id, hash_md5):
        api_url = CoreAPI.CoreApi + "/v1/app/" + CoreAPI.AppId + "/prefix/" + CoreAPI.PrefixId + "/suffix/create?SecretKey=" + CoreAPI.SecretKey

        post_data = {
            "Index": "1",
            "Signature": hash_md5,
            "SuffixId": suffix_id,
            "Type": "URL",
            "Version": "1.0",
            "TTL": "ttl-",
            "Permission": "TEST",
            "Value": "http://core.sist.tsinghua.edu.cn/datasets/item/" + CoreAPI.PrefixId + "/" + suffix_id
        }

        post_data = json.dumps(post_data)
        r = requests.post(api_url, post_data)
        print(r.json())

def ds_md5(file_path):
    with open(file_path, 'rb') as f:
        md5_obj = hashlib.md5()
        md5_obj.update(f.read())
        hash = md5_obj.hexdigest()
    return hash

def ds_sha2(file_path):
    with open(file_path, 'rb') as f:
        hash_obj = hashlib.sha256()
        hash_obj.update(f.read())
        hash = hash_obj.hexdigest()
    return hash


if __name__ == '__main__':
    file_path = u'/Users/Jason/Downloads/计科.csv'
    excel_path = u'/Users/Jason/Downloads/marsdata.xlsx'
    json_path = u'/Users/Jason/Downloads/matsdata.json'
    # get_excel_data(excel_path)
    data_frame = DataApi.read_dataset(excel_path)
    columns = data_frame.columns
    print(columns)
    row1 = data_frame.ix[:,columns[0]]
    row2 = data_frame.ix[:,columns[1]]
    data = list()
    for i,j in zip(row1,row2):
        data.append({
            'name':i,
            'value':j
        })
    print(data)