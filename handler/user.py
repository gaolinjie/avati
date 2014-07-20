#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 meiritugua.com

import uuid
import hashlib
import Image
import StringIO
import time
import json
import re
import urllib2
import urllib
import tornado.web
import lib.jsonp
import os.path

from base import *
from lib.sendmail import send
from lib.variables import gen_random
from lib.gravatar import Gravatar
from form.user import *
from lib.mobile import is_mobile_browser

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
            do_login(self, user_id)

            # send register success mail to user

            #mail_title = u"mifan.tv 注册成功通知"
            #mail_content = self.render_string("user/register_mail.html")
            #send(mail_title, mail_content, form.email.data)

        self.redirect(self.get_argument("next", "/"))

class UserHandler(BaseHandler):
    def get(self, template_variables = {}):
        self.render("user.html", **template_variables)