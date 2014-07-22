#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2014 avati

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

from base import *
from lib.variables import *
from lib.variables import gen_random
from lib.xss import XssCleaner
from lib.utils import find_mentions
from lib.reddit import hot
from lib.utils import pretty_date

from lib.mobile import is_mobile_browser
from form.post import *

class IndexHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            self.render("index.html", **template_variables)
        else:
            self.redirect("/signin")

class PostHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            self.render("post.html", **template_variables)
        else:
            self.redirect("/signin")

class NewHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            self.render("new.html", **template_variables)
        else:
            self.redirect("/signin")

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        type = self.get_argument('t', "q")

        # validate the fields
        form = NewForm(self)

        if not form.validate():
            self.get({"errors": form.errors})
            return

        post_info = {
            "author_id": self.current_user["uid"],           
            "title": form.title.data,
            "content": form.content.data,
            "reply_num": 0,
            "type": type,
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        post_id = self.post_model.add_new_post(post_info)
        self.redirect("/p/"+str(post_id))

        # process tags
        tagStr = form.tag.data
        if tagStr:
            print tagStr
            tagNames = tagStr.split(',')  
            for tagName in tagNames:  
                tag = self.tag_model.get_tag_by_tag_name(tagName)
                if tag:
                    self.post_tag_model.add_new_post_tag({"post_id": post_id, "tag_id": tag.id})
                    self.tag_model.update_tag_by_tag_id(tag.id, {"post_num": tag.post_num+1})
                else:
                    tag_id = self.tag_model.add_new_tag({
                        "name": tagName, 
                        "post_num": 1, 
                        "is_new": 1, 
                        "post_add": post_id, 
                        "user_add":  self.current_user["uid"], 
                        "created": time.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    self.post_tag_model.add_new_post_tag({"post_id": post_id, "tag_id": tag_id})
  

class TagHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            self.render("tag.html", **template_variables)
        else:
            self.redirect("/signin")

class TagsHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            self.render("tags.html", **template_variables)
        else:
            self.redirect("/signin")