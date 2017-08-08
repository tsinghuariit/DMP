# -*- coding: utf-8 -*-
# coding=utf-8
'''pip install yunpian-sdk-python '''
from yunpian.SmsOperator import SmsOperator
import sys
import json
import random
from app import app
__author__ = 'ruidong.wang@tsingdata.com'
reload(sys)
sys.setdefaultencoding('utf-8')
APIKEY = '06a354c33f3f7582862ebdff9404ccb8'
'''同一手机号一天只可以发送三次验证码'''
def send_sms(mobile,captcha):
    smsOperator = SmsOperator(APIKEY)
    result = smsOperator.single_send({'mobile': mobile, 'text': '【清数科技】您的验证码是%s'%captcha})
    app.logger.info(result)
    return json.dumps(result.content, ensure_ascii=False)


def rand_sms_captcha():
    captcha = random.randint(100000,1000000)
    return captcha
