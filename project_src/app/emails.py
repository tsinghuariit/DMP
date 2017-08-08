#coding:utf-8
from flask import render_template
from flask_mail import Message
from app import mail
from .decorators import async
from config import ADMINS
from app import app


@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(app, msg)


def follower_notification(followed, follower):
    send_email("[microblog] %s is now following you!" % follower.nickname,
               ADMINS[0],
               [followed.email],
               render_template("follower_email.txt",
                               user=followed, follower=follower),
               render_template("follower_email.html",
                               user=followed, follower=follower))

def captcha_email(user_email,captcha):
    send_email(u"%s正在修改密码，请验证你的邮箱"% user_email,
              ADMINS[0],
               [user_email],
               render_template("captcha_email.txt", user_email=user_email, captcha=captcha),
               render_template("captcha_email.html",user_email=user_email,captcha=captcha))
