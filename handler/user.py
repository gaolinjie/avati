#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 meiritugua.com

import uuid
import uuid
import hashlib
import Image
import StringIO
import time
import json
import re
import urllib2
import tornado.web
import lib.jsonp
import pprint
import math
import datetime 
import os

from base import *
from lib.variables import *
from form.user import *
from lib.variables import gen_random
from lib.xss import XssCleaner
from lib.utils import find_mentions
from lib.reddit import hot
from lib.utils import pretty_date

from lib.mobile import is_mobile_browser

import qiniu.conf
import qiniu.io
import qiniu.rs

qiniu.conf.ACCESS_KEY = "hmHRMwms0cn9OM9PMETYwsXMLG93z3FiBmCtPu7y"
qiniu.conf.SECRET_KEY = "nCDM7Tuggre39RiqXaDmjo8sZn6MLGmckUaCrOJU"


def do_login(self, user_id):
    user_info = self.user_model.get_user_by_uid(user_id)
    user_id = user_info["uid"]
    self.session["uid"] = user_id
    self.session["username"] = user_info["username"]
    self.session["email"] = user_info["email"]
    self.session["password"] = user_info["password"]
    self.session.save()
    self.set_secure_cookie("user", str(user_id))

def do_logout(self):
    # destroy sessions
    self.session["uid"] = None
    self.session["username"] = None
    self.session["email"] = None
    self.session["password"] = None
    self.session.save()

    # destroy cookies
    self.clear_cookie("user")

class SigninHandler(BaseHandler):
    def get(self, template_variables = {}):
        do_logout(self)
        self.render("user/signin.html", **template_variables)

    def post(self, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = SigninForm(self)

        if not form.validate():
            self.get({"errors": form.errors})
            return

        # continue while validate succeed
        
        secure_password = hashlib.sha1(form.password.data).hexdigest()
        secure_password_md5 = hashlib.md5(form.password.data).hexdigest()
        user_info = self.user_model.get_user_by_email_and_password(form.email.data, secure_password)
        user_info = user_info or self.user_model.get_user_by_email_and_password(form.email.data, secure_password_md5)
        
        if(user_info):
            do_login(self, user_info["uid"])
            # update `last_login`
            updated = self.user_model.set_user_base_info_by_uid(user_info["uid"], {"last_login": time.strftime('%Y-%m-%d %H:%M:%S')})
            redirect_path = self.get_argument("next", "/")
            print redirect_path
            self.redirect(redirect_path)
            return

        template_variables["errors"] = {"invalid_email_or_password": [u"邮箱或者密码不正确"]}
        self.get(template_variables)

class SignoutHandler(BaseHandler):
    def get(self):
        do_logout(self)
        # redirect
        self.redirect(self.get_argument("next", "/"))

class SignupHandler(BaseHandler):
    def get(self, template_variables = {}):
        do_logout(self)
        self.render("user/signup.html", **template_variables)

    def post(self, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = SignupForm(self)

        if not form.validate():
            self.get({"errors": form.errors})
            return

        # validate duplicated

        duplicated_email = self.user_model.get_user_by_email(form.email.data)
        duplicated_username = self.user_model.get_user_by_username(form.username.data)

        if(duplicated_email or duplicated_username):
            template_variables["errors"] = {}

            if(duplicated_email):
                template_variables["errors"]["duplicated_email"] = [u"所填邮箱已经被注册过"]

            if(duplicated_username):
                template_variables["errors"]["duplicated_username"] = [u"所填用户名已经被注册过"]

            self.get(template_variables)
            return

        # validate reserved

        if(form.username.data in self.settings.get("reserved")):
            template_variables["errors"] = {}
            template_variables["errors"]["reserved_username"] = [u"用户名被保留不可用"]
            self.get(template_variables)
            return

        # continue while validate succeed

        secure_password = hashlib.sha1(form.password.data).hexdigest()

        user_info = {
            "email": form.email.data,
            "password": secure_password,
            "username": form.username.data,
            "intro": "",
            "created": time.strftime('%Y-%m-%d %H:%M:%S')
        }

        if(self.current_user):
            return
        
        user_id = self.user_model.add_new_user(user_info)
        
        if(user_id):
            follow_info = {
                "author_id": user_id,
                "obj_id": user_id,
                "obj_type": "u",
                "created": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.follow_model.add_new_follow(follow_info)

            do_login(self, user_id)

            # send register success mail to user

            #mail_title = u"mifan.tv 注册成功通知"
            #mail_content = self.render_string("user/register_mail.html")
            #send(mail_title, mail_content, form.email.data)

        self.redirect(self.get_argument("next", "/"))

class UserHandler(BaseHandler):
    def get(self, username, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info

        if(user_info):
            view_user = self.user_model.get_user_by_username(username)
            template_variables["view_user"] = view_user
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, view_user.uid, 'u')

            template_variables["feeds"] = self.feed_model.get_user_all_feeds(view_user.uid, user_info.uid)

            feeds1 = self.feed_model.get_user_all_feeds_by_type(view_user.uid, user_info.uid, 1)
            feeds2 = self.feed_model.get_user_all_feeds_by_type(view_user.uid, user_info.uid, 2)
            feeds7 = self.feed_model.get_user_all_feeds_by_type(view_user.uid, user_info.uid, 7)
            feeds8 = self.feed_model.get_user_all_feeds_by_type(view_user.uid, user_info.uid, 8)

            template_variables["feeds1"] = feeds1
            template_variables["feeds2"] = feeds2
            template_variables["feeds7"] = feeds7
            template_variables["feeds8"] = feeds8

            template_variables["feeds1_len"] = len(feeds1["list"])
            template_variables["feeds2_len"] = len(feeds2["list"])
            template_variables["feeds7_len"] = len(feeds7["list"])
            template_variables["feeds8_len"] = len(feeds8["list"])

            self.render("user.html", **template_variables)
        else:
            self.redirect("/login")

class SettingHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, template_variables = {}):
        user_info = self.get_current_user()
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        self.render("user/setting.html", **template_variables)

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = SettingForm(self)

        if not form.validate():
            self.get({"errors": form.errors})
            return

        # continue while validate succeed

        user_info = self.current_user
        update_result = self.user_model.set_user_base_info_by_uid(user_info["uid"], {
            "sign": form.sign.data,
            "gender": form.gender.data,
            "location": form.location.data,
            "business": form.business.data,
            "edu": form.edu.data,
            "company": form.company.data,
            "website": form.website.data,
            "intro": form.intro.data,
            "updated": time.strftime('%Y-%m-%d %H:%M:%S')
        })

        self.redirect("/u/" + form.username.data)

class SettingAvatarHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, template_variables = {}):
        user_info = self.get_current_user()
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        self.render("user/setting_avatar.html", **template_variables)

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        if(not "avatar" in self.request.files):
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_avatar"] = [u"请先选择要上传的头像"]
            self.get(template_variables)
            return

        user_info = self.current_user
        user_id = user_info["uid"]
        avatar_name = "%s" % uuid.uuid5(uuid.NAMESPACE_DNS, str(user_id))
        avatar_raw = self.request.files["avatar"][0]["body"]
        avatar_buffer = StringIO.StringIO(avatar_raw)
        avatar = Image.open(avatar_buffer)

        usr_home = os.path.expanduser('~')
        avatar.save(usr_home+"/www/avati/static/tmp/avatar/b_%s.png" % avatar_name, "PNG")

        policy = qiniu.rs.PutPolicy("avati-avatar:b_%s.png" % avatar_name)
        uptoken = policy.token()
        data=open(usr_home+"/www/avati/static/tmp/avatar/b_%s.png" % avatar_name)
        ret, err = qiniu.io.put(uptoken, "b_"+avatar_name+".png", data)  
        os.remove(usr_home+"/www/avati/static/tmp/avatar/b_%s.png" % avatar_name)

        avatar_name = "http://avati-avatar.qiniudn.com/b_"+avatar_name
        result = self.user_model.set_user_avatar_by_uid(user_id, "%s.png-avatar" % avatar_name)
        template_variables["success_message"] = [u"用户头像更新成功"]
        # update `updated`
        updated = self.user_model.set_user_base_info_by_uid(user_id, {"updated": time.strftime('%Y-%m-%d %H:%M:%S')})
        self.redirect("/setting/avatar")

class SettingCoverHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, template_variables = {}):
        user_info = self.get_current_user()
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        if(not user_info):
            self.redirect("/login")

        self.render("user/setting_cover.html", **template_variables)

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        if(not "cover" in self.request.files):
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_cover"] = [u"请先选择要上传的封面"]
            self.get(template_variables)
            return

        user_info = self.current_user
        user_id = user_info["uid"]

        cover_name = "%s" % uuid.uuid5(uuid.NAMESPACE_DNS, str(user_info.uid))
        cover_raw = self.request.files["cover"][0]["body"]
        cover_buffer = StringIO.StringIO(cover_raw)
        cover = Image.open(cover_buffer)
     
        usr_home = os.path.expanduser('~')
        cover.save(usr_home+"/www/avati/static/tmp/cover/b_%s.png" % cover_name, "PNG")

        policy = qiniu.rs.PutPolicy("avati-cover:b_%s.png" % cover_name)
        uptoken = policy.token()
        data=open(usr_home+"/www/avati/static/tmp/cover/b_%s.png" % cover_name)
        ret, err = qiniu.io.put(uptoken, "b_"+cover_name+".png", data)  
        os.remove(usr_home+"/www/avati/static/tmp/cover/b_%s.png" % cover_name)

        cover_name = "http://avati-cover.qiniudn.com/b_"+cover_name
        result = self.user_model.set_user_cover_by_uid(user_id, "%s.png-cover" % cover_name)
        template_variables["success_message"] = [u"频道头像更新成功"]
        # update `updated`
        updated = self.user_model.set_user_base_info_by_uid(user_id, {"updated": time.strftime('%Y-%m-%d %H:%M:%S')})

        self.redirect("/setting/cover")

class SettingPasswordHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, template_variables = {}):
        user_info = self.get_current_user()
        template_variables["user_info"] = user_info
        self.render("user/setting_password.html", **template_variables)

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = SettingPasswordForm(self)

        if not form.validate():
            self.get({"errors": form.errors})
            return

        # validate the password

        user_info = self.current_user
        user_id = user_info["uid"]
        secure_password = hashlib.sha1(form.password_old.data).hexdigest()
        secure_new_password = hashlib.sha1(form.password.data).hexdigest()

        if(not user_info["password"] == secure_password):
            template_variables["errors"] = {}
            template_variables["errors"]["error_password"] = [u"当前密码输入有误"]
            self.get(template_variables)
            return

        # continue while validate succeed

        update_result = self.user_model.set_user_password_by_uid(user_id, secure_new_password)
        template_variables["success_message"] = [u"您的用户密码已更新"]
        # update `updated`
        updated = self.user_model.set_user_base_info_by_uid(user_id, {"updated": time.strftime('%Y-%m-%d %H:%M:%S')})
        self.redirect("/setting")

class ForgotPasswordHandler(BaseHandler):
    def get(self, template_variables = {}):
        do_logout(self)
        self.render("user/forgot_password.html", **template_variables)

    def post(self, template_variables = {}):
        template_variables = {}

        # validate the fields

        form = ForgotPasswordForm(self)

        if not form.validate():
            self.get({"errors": form.errors})
            return


        # validate the post value

        user_info = self.user_model.get_user_by_email_and_username(form.email.data, form.username.data)

        if(not user_info):
            template_variables["errors"] = {}
            template_variables["errors"]["invalid_email_or_username"] = [u"所填用户名和邮箱有误"]
            self.get(template_variables)
            return

        # continue while validate succeed
        # update password

        new_password = uuid.uuid1().hex
        new_secure_password = hashlib.sha1(new_password).hexdigest()
        update_result = self.user_model.set_user_password_by_uid(user_info["uid"], new_secure_password)

        # send password reset link to user

        mail_title = u"mifan.tv 找回密码"
        template_variables = {"email": form.email.data, "new_password": new_password};
        template_variables["success_message"] = [u"新密码已发送至您的注册邮箱"]
        mail_content = self.render_string("user/forgot_password_mail.html", **template_variables)
        send(mail_title, mail_content, form.email.data)

        self.get(template_variables)

class SignoutHandler(BaseHandler):
    def get(self):
        do_logout(self)
        # redirect
        self.redirect(self.get_argument("next", "/"))

class SocialHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, template_variables = {}):
        user_info = self.get_current_user()
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        if user_info:
            self.render("user/social.html", **template_variables)

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        user_info = self.get_current_user()

        # validate the fields

        form = SocialForm(self)

        if not form.validate():
            self.get({"errors": form.errors})
            return

        # continue while validate succeed

        user_info = self.current_user
        update_result = self.user_model.set_user_base_info_by_uid(user_info["uid"], {
            "weibo": form.weibo.data,
            "qzone": form.qzone.data,
            "douban": form.douban.data,
            "renren": form.renren.data,
            "updated": time.strftime('%Y-%m-%d %H:%M:%S')
        })

        self.redirect("/u/" + user_info.username)