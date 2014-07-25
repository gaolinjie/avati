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
import os

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
            template_variables["feeds"] = self.follow_model.get_user_all_follow_feeds(user_info.uid)
            self.render("index.html", **template_variables)
        else:
            self.redirect("/signin")

class PostHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info

        if(user_info):
            post = self.post_model.get_post_by_post_id(post_id)
            template_variables["post"] = post
            template_variables["tags"] = self.post_tag_model.get_post_all_tags(post_id)
            template_variables["replys"] = self.reply_model.get_post_all_replys(post_id)
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, post_id, post.post_type)
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

        post_type = self.get_argument('t', "q")

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
            "post_type": post_type,
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        post_id = self.post_model.add_new_post(post_info)
        self.redirect("/p/"+str(post_id))

        # add feed
        feed_info = {
            "user_id": self.current_user["uid"],           
            "post_id": post_id,
            "feed_type": 1,
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        self.feed_model.add_new_feed(feed_info)

        # add follow
        follow_info = {
            "author_id": self.current_user["uid"],
            "obj_id": post_id,
            "obj_type": post_type,
            "created": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.follow_model.add_new_follow(follow_info)

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
    def get(self, tag_name, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            tag = self.tag_model.get_tag_by_tag_name(tag_name)
            template_variables["tag"] = tag
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, tag.id, 't')
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


class ReplyHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user

    @tornado.web.authenticated
    def post(self, post_id, template_variables = {}):
        user_info = self.current_user

        data = json.loads(self.request.body)
        reply_content = data["reply_content"]

        if(user_info):
            reply_info = {
                "author_id": user_info["uid"],
                "post_id": post_id,
                "content": reply_content,
                "created": time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            reply_id = self.reply_model.add_new_reply(reply_info)

            post = self.post_model.get_post_by_post_id(post_id)
            self.post_model.update_post_by_post_id(post_id, {"reply_num": post.reply_num+1,})
            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                    "message": "successed",
            }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                    "message": "failed",
            }))


class FollowHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, template_variables = {}):
        user_info = self.current_user

        data = json.loads(self.request.body)
        obj_id = data["obj_id"]
        obj_type = data["obj_type"]

        if(user_info):
            follow = self.follow_model.get_follow(user_info.uid, obj_id, obj_type)
            if(follow):
                self.follow_model.delete_follow_by_id(follow.id)
            else:
                follow_info = {
                    "author_id": user_info["uid"],
                    "obj_id": obj_id,
                    "obj_type": obj_type,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.follow_model.add_new_follow(follow_info)

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                    "message": "successed",
            }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                    "message": "failed",
            }))