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
import requests
import urllib

from base import *
from lib.sendmail import send
from lib.variables import *
from lib.variables import gen_random
from lib.xss import XssCleaner
from lib.utils import find_mentions
from lib.reddit import hot
from lib.utils import pretty_date
from pyquery import PyQuery as pyq

from lib.mobile import is_mobile_browser
from form.post import *

from qiniu import Auth
from qiniu import BucketManager
from qiniu import put_data

import xml.etree.ElementTree as ET
import commands

access_key = "DaQzr1UhFQD6im_kJJjZ8tQUKQW7ykiHo4ZWfC25"
secret_key = "Ge61JJtUSC5myXVrntdVOqAZ5L7WpXR_Taa9C8vb"
q = Auth(access_key, secret_key)
bucket = BucketManager(q)

THRESHOLD = 2
class IndexHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        p = int(self.get_argument("p", "1"))
        #template_variables["ad"] = self.ads_model.get_rand_ad()[0]
        template_variables["hot_items"] = self.item_model.get_rand_items()
        if(user_info):
            template_variables["related_posts"] = self.follow_model.get_user_follow_hot_posts(user_info.uid)
            template_variables["feeds"] = self.follow_model.get_user_all_follow_and_all_post_feeds(user_info.uid, current_page = p)        
            template_variables["notice_count"] = self.notice_model.get_user_unread_notice_count(user_info.uid)  + self.follow_model.get_user_all_follow_post_feeds_count(user_info.uid, user_info.view_follow, time.strftime('%Y-%m-%d %H:%M:%S'))
            template_variables["invite_count"] = self.invite_model.get_user_unread_invite_count(user_info.uid)
        else:
            template_variables["sign_in_up"] = self.get_argument("s", "") 
            link = self.get_argument("link", "")
            if link!="":
                template_variables["link"] =  link
            link2 = self.get_argument("link2", "")
            if link2!="":
                template_variables["link2"] = link2 
            invite = self.get_argument("i", "")
            if invite!="":
                template_variables["invite"] = invite
            else:
                template_variables["invite"] = None
            error = self.get_argument("e", "")
            if error!="":
                template_variables["error"] = error
            else:
                template_variables["error"] = None
            template_variables["notice_count"] = None
            template_variables["invite_count"] = None
            template_variables["feeds"] = self.feed_model.get_default_feeds(current_page = p)
            feeds = self.feed_model.get_default_feeds(current_page = p)
            for fee in feeds["list"]:
                print fee.author_username

        if is_mobile_browser(self):
            self.render("mobile/index.html", **template_variables)
        else:
            self.render("index.html", **template_variables)

class PostHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        sort = self.get_argument('sort', "voted")
        p = int(self.get_argument("p", "1"))

        
        template_variables["related_posts"] = self.post_tag_model.get_post_related_posts(post_id)
        template_variables["tags"] = self.post_tag_model.get_post_all_tags(post_id)
        if(user_info):  
            post = self.post_model.get_post_by_post_id2(post_id, user_info.uid)
            template_variables["post"] = post
            self.post_model.update_post_by_post_id(post.id, {"view_num": post.view_num+1})          
            if sort== "voted":
                replys = self.reply_model.get_post_all_replys_sort_by_voted(post_id, user_info.uid, current_page = p)
                template_variables["sort"] = "voted"
            else:
                replys = self.reply_model.get_post_all_replys_sort_by_created(post_id, user_info.uid, current_page = p)
                template_variables["sort"] = "created"
            template_variables["replys"] = replys
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, post_id, post.post_type)
            template_variables["thank"] = self.thank_model.get_thank(user_info.uid, post.author_id, post_id, 'post')
            template_variables["report"] = self.report_model.get_report(user_info.uid, post.author_id, post_id, 'post')
            votesList = []
            for reply in replys["list"]:
                votesList.append(self.vote_model.get_reply_all_up_votes(reply.id)) 
            template_variables["votesList"] = votesList
        else:
            post = self.post_model.get_post_by_post_id(post_id)
            template_variables["post"] = post
            self.post_model.update_post_by_post_id(post.id, {"view_num": post.view_num+1}) 
            if sort== "voted":
                replys = self.reply_model.get_post_all_replys_sort_by_voted2(post_id, current_page = p)
                template_variables["sort"] = "voted"
            else:
                replys = self.reply_model.get_post_all_replys_sort_by_created2(post_id, current_page = p)
                template_variables["sort"] = "created"
            template_variables["replys"] = replys
            template_variables["follow"] = None
            template_variables["link"] = "p"
            template_variables["link2"] = post_id
            votesList = []
            for reply in replys["list"]:
                votesList.append(self.vote_model.get_reply_all_up_votes(reply.id)) 
            template_variables["votesList"] = votesList
            template_variables["sign_in_up"] = self.get_argument("s", "") 
            link = self.get_argument("link", "")
            if link!="":
                template_variables["link"] =  link
            link2 = self.get_argument("link2", "")
            if link2!="":
                template_variables["link2"] = link2 
            invite = self.get_argument("i", "")
            if invite!="":
                template_variables["invite"] = invite
            else:
                template_variables["invite"] = None
            error = self.get_argument("e", "")
            if error!="":
                template_variables["error"] = error
            else:
                template_variables["error"] = None

        if is_mobile_browser(self):
            self.render("mobile/post.html", **template_variables)
        else:
            self.render("post.html", **template_variables)

class GetTagsHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        allTags = self.tag_model.get_all_tags()
        print allTags
        allTagJson = []
        for tag in allTags:
            allTagJson.append(tag.name)

        self.write(json.dumps(allTagJson))
        
            


class NewHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            if is_mobile_browser(self):
                self.render("mobile/new.html", **template_variables)
            else:
                self.render("new.html", **template_variables)           
        else:
            self.redirect("/?s=signin&link=new")

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        user_info = self.current_user
        template_variables = {}

        post_type = self.get_argument('t', "q")

        # validate the fields
        form = NewForm(self)

        #if not form.validate():
           # self.get({"errors": form.errors})
            #return
            
        post_info = {
            "author_id": self.current_user["uid"],           
            "title": form.title.data,
            "content": form.content.data,
            "reply_num": 0,
            "view_num": 1,
            "follow_num": 1,
            "post_type": post_type,
            "updated": time.strftime('%Y-%m-%d %H:%M:%S'),
            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        post_id = self.post_model.add_new_post(post_info)
        self.redirect("/p/"+str(post_id))

        if post_type == 'q':
            feed_type = 1
            notice_type = 6
        else:
            feed_type = 7
            notice_type = 13

        # add feed: user 提出了问题
        feed_info = {
            "user_id": self.current_user["uid"],           
            "post_id": post_id,
            "feed_type": feed_type,
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
        print tagStr
        if tagStr:
            tagNames = tagStr.split(',') 
            for tagName in tagNames:  
                tag = self.tag_model.get_tag_by_tag_name(tagName)
                if tag:
                    self.post_tag_model.add_new_post_tag({"post_id": post_id, "tag_id": tag.id})
                    if(post_type == 'q'):
                        self.tag_model.update_tag_by_tag_id(tag.id, {"question_num": tag.question_num+1})
                    else:
                        self.tag_model.update_tag_by_tag_id(tag.id, {"post_num": tag.post_num+1})
                else:
                    if(post_type == 'q'):
                        tag_info = {
                            "name": tagName, 
                            "question_num": 1, 
                            "is_new": 1, 
                            "post_add": post_id, 
                            "user_add":  self.current_user["uid"], 
                            "created": time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    else:
                        tag_info = {
                            "name": tagName, 
                            "post_num": 1, 
                            "is_new": 1, 
                            "post_add": post_id, 
                            "user_add":  self.current_user["uid"], 
                            "created": time.strftime('%Y-%m-%d %H:%M:%S')
                        }                  
                    tag_id = self.tag_model.add_new_tag(tag_info)
                    self.post_tag_model.add_new_post_tag({"post_id": post_id, "tag_id": tag_id})
                    category = self.category_model.get_category_by_id(1)
                    self.category_model.update_category_by_id(1, {"tag_num":category.tag_num+1})


        # create @username notification
        for username in set(find_mentions(form.content.data)):
            mentioned_user = self.user_model.get_user_by_username(username)

            if not mentioned_user:
                continue

            if mentioned_user["uid"] == self.current_user["uid"]:
                continue

            if mentioned_user["uid"] == post.author_id:
                continue

            notice_info = {
                "author_id": mentioned_user["uid"],
                "user_id": self.current_user["uid"],          
                "post_id": post_id,
                "notice_type": notice_type,
                "created": time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            self.notice_model.add_new_notice(notice_info)

        # update user_info
        if post_type == 'q':
            self.user_model.update_user_info_by_user_id(user_info.uid, {"questions": user_info.questions+1, "expend": user_info.expend+20})
        else:
            self.user_model.update_user_info_by_user_id(user_info.uid, {"posts": user_info.posts+1, "expend": user_info.expend+20})
        self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 2, "amount": -20, "balance": user_info.income-user_info.expend-20, "post_id": post_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})


class EditHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            post = self.post_model.get_post_by_post_id(post_id)
            template_variables["post"] = post
            tags = self.post_tag_model.get_post_all_tags(post_id)
            tagStr = ''
            i=0
            for tag in tags["list"]:
                if i==0:
                    tagStr = tag.tag_name
                else:
                    tagStr = tagStr + ','+tag.tag_name
                i=i+1
            template_variables["tagStr"] = tagStr 
            if is_mobile_browser(self):
                self.render("mobile/edit.html", **template_variables)
            else:
                self.render("edit.html", **template_variables)
        else:
            self.redirect("/?s=signin")

    @tornado.web.authenticated
    def post(self, post_id, template_variables = {}):
        template_variables = {}

        post_type = self.get_argument('t', "q")

        # validate the fields
        form = NewForm(self)

        #if not form.validate():
            #self.get({"errors": form.errors})
            #return

        post_info = {          
            "title": form.title.data,
            "content": form.content.data,
            "updated": time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        self.post_model.update_post_by_post_id(post_id, post_info)
        self.redirect("/p/"+str(post_id))

        tags = self.post_tag_model.get_post_all_tags(post_id)
        for tag in tags["list"]:
            if(post_type == 'q'):
                self.tag_model.update_tag_by_tag_id(tag.tag_id, {"question_num": tag.tag_question_num-1})
            else:
                self.tag_model.update_tag_by_tag_id(tag.tag_id, {"post_num": tag.tag_post_num-1})
        self.post_tag_model.delete_post_tag_by_post_id(post_id)
        # process tags
        tagStr = form.tag.data
        print tagStr
        if tagStr:
            tagNames = tagStr.split(',')  
            for tagName in tagNames:  
                tag = self.tag_model.get_tag_by_tag_name(tagName)
                if tag:
                    self.post_tag_model.add_new_post_tag({"post_id": post_id, "tag_id": tag.id})
                    if(post_type == 'q'):
                        self.tag_model.update_tag_by_tag_id(tag.id, {"question_num": tag.question_num+1})
                    else:
                        self.tag_model.update_tag_by_tag_id(tag.id, {"post_num": tag.post_num+1})
                else:
                    if(post_type == 'q'):
                        tag_info = {
                            "name": tagName, 
                            "question_num": 1, 
                            "is_new": 1, 
                            "post_add": post_id, 
                            "user_add":  self.current_user["uid"], 
                            "created": time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    else:
                        tag_info = {
                            "name": tagName, 
                            "post_num": 1, 
                            "is_new": 1, 
                            "post_add": post_id, 
                            "user_add":  self.current_user["uid"], 
                            "created": time.strftime('%Y-%m-%d %H:%M:%S')
                        }                  
                    tag_id = self.tag_model.add_new_tag(tag_info)
                    self.post_tag_model.add_new_post_tag({"post_id": post_id, "tag_id": tag_id})
                    category = self.category_model.get_category_by_id(1)
                    self.category_model.update_category_by_id(1, {"tag_num":category.tag_num+1})
  

class TagHandler(BaseHandler):
    def get(self, tag_name, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        p = int(self.get_argument("p", "1"))
        tag = self.tag_model.get_tag_by_tag_name(tag_name)
        template_variables["tag"] = tag
        template_variables["follow_num"] = self.follow_model.get_tag_followers_count(tag.id)
        template_variables["feeds1_len"] = self.tag_model.get_tag_all_feeds_count_by_type(tag.id, 1)
        template_variables["feeds7_len"] = self.tag_model.get_tag_all_feeds_count_by_type(tag.id, 7)
        template_variables["parent_tags"] = self.tag_parent_model.get_parent_tags(tag.id)
        template_variables["child_tags"] = self.tag_parent_model.get_child_tags(tag.id)
        if(user_info):   
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, tag.id, 't')
            template_variables["feeds"] = self.tag_model.get_tag_all_feeds(tag.id, user_info.uid, current_page = p)
            template_variables["feeds1"] = self.tag_model.get_tag_all_feeds_by_type(tag.id, user_info.uid, 1, current_page = p)
            template_variables["feeds7"] = self.tag_model.get_tag_all_feeds_by_type(tag.id, user_info.uid, 7, current_page = p)
        else:
            template_variables["feeds"] = self.tag_model.get_tag_all_feeds2(tag.id, current_page = p)
            template_variables["feeds1"] = self.tag_model.get_tag_all_feeds_by_type2(tag.id, 1, current_page = p)
            template_variables["feeds7"] = self.tag_model.get_tag_all_feeds_by_type2(tag.id, 7, current_page = p)
            template_variables["link"] = "t"
            template_variables["link2"] = tag_name
            template_variables["follow"] = None
            
        if is_mobile_browser(self):
            self.render("mobile/tag.html", **template_variables)
        else:
            self.render("tag.html", **template_variables)

class TagsHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        
        #template_variables["categorys"] = self.category_model.get_tag_categorys()
        template_variables["tags"] = self.tag_model.get_all_tags2()
        template_variables["scrollspy"] = "scrollspy"

        if is_mobile_browser(self):
            self.render("mobile/tags.html", **template_variables)
        else:
            self.render("tags.html", **template_variables)


class ReplyHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user

    @tornado.web.authenticated
    def post(self, post_id, template_variables = {}):
        user_info = self.current_user

        data = json.loads(self.request.body)
        reply_content = data["reply_content"]
        anon = data["anon"]

        if(user_info):
            reply_info = {
                "author_id": user_info["uid"],
                "post_id": post_id,
                "content": reply_content,
                "anon": anon,
                "created": time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            reply_id = self.reply_model.add_new_reply(reply_info)

            post = self.post_model.get_post_by_post_id(post_id)
            self.post_model.update_post_by_post_id(post_id, {
                "reply_num": post.reply_num+1, 
                "updated": time.strftime('%Y-%m-%d %H:%M:%S'),
            })

            if post.post_type == 'q':
                feed_type = 2
                notice_type = 1
                notice_type2 = 7
            else:
                feed_type = 8
                notice_type = 8
                notice_type2 = 14
            # add feed: user 回答了问题
            feed_info = {
                "user_id": self.current_user["uid"],           
                "post_id": post.id,
                "reply_id": reply_id,
                "feed_type": feed_type,
                "created": time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            self.feed_model.add_new_feed(feed_info)

            # add notice: user 回答了问题
            if user_info.uid != post.author_id:
                notice_info = {
                    "author_id": post.author_id,
                    "user_id": self.current_user["uid"],          
                    "post_id": post.id,
                    "reply_id": reply_id,
                    "notice_type": notice_type,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                self.notice_model.add_new_notice(notice_info)
            
            # create @username notification
            for username in set(find_mentions(reply_content)):
                mentioned_user = self.user_model.get_user_by_username(username)

                if not mentioned_user:
                    continue

                if mentioned_user["uid"] == self.current_user["uid"]:
                    continue

                if mentioned_user["uid"] == post.author_id:
                    continue

                notice_info2 = {
                    "author_id": mentioned_user["uid"],
                    "user_id": self.current_user["uid"],          
                    "post_id": post_id,
                    "reply_id": reply_id,
                    "notice_type": notice_type2,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                self.notice_model.add_new_notice(notice_info2)

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                    "message": "successed",
                    "reply_id": reply_id
            }))

            # update user_info
            if post.post_type == 'q':
                self.user_model.update_user_info_by_user_id(user_info.uid, {"answers": user_info.answers+1})
            else:
                self.user_model.update_user_info_by_user_id(user_info.uid, {"comments": user_info.comments+1})

            if user_info.uid != post.author_id:
                self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend+5})
                self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 3, "amount": -5, "balance": user_info.income-user_info.expend-5, "post_id": post_id, "reply_id": reply_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})
                post_author = self.user_model.get_user_by_uid(post.author_id)
                self.user_model.update_user_info_by_user_id(post_author.uid, {"income": post_author.income+5})
                self.balance_model.add_new_balance({"author_id":  post_author.uid, "balance_type": 4, "amount": 5, "balance": post_author.income-post_author.expend+5, "post_id": post_id, "reply_id": reply_id, "user_id": user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')})
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
                if obj_type=='q' or obj_type=='p':
                    if obj_type == 'q':
                        feed_type = 3
                    else:
                        feed_type = 9
                    self.feed_model.delete_feed_by_user_post__and_type(user_info.uid,  obj_id, feed_type)

                    post = self.post_model.get_post_by_post_id(obj_id)
                    self.post_model.update_post_by_post_id(post.id, {"follow_num": post.follow_num-1})

                    follows = self.follow_model.get_post_all_follows(obj_id)
                    if len(follows) <= THRESHOLD:
                        if obj_type == 'q':
                            feed_type = 4                         
                        else:
                            feed_type = 10
                        self.feed_model.delete_feed_by_post_and_type(obj_id, feed_type)
                if obj_type=='u':
                    # update user_info
                    user = self.user_model.get_user_by_uid(obj_id)
                    self.user_model.update_user_info_by_user_id(obj_id, {"followers": user.followers-1})
                    self.user_model.update_user_info_by_user_id(user_info.uid, {"followees": user_info.followees-1})
                if obj_type=='t':
                    tag = self.tag_model.get_tag_by_tag_id(obj_id)
                    self.tag_model.update_tag_by_tag_id(tag.id, {"follow_num": tag.follow_num-1})
            else:
                follow_info = {
                    "author_id": user_info["uid"],
                    "obj_id": obj_id,
                    "obj_type": obj_type,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.follow_model.add_new_follow(follow_info)

                if obj_type=='t':
                    tag = self.tag_model.get_tag_by_tag_id(obj_id)
                    self.tag_model.update_tag_by_tag_id(tag.id, {"follow_num": tag.follow_num+1})

                if obj_type=='u':
                    # add notice: user 关注了你
                    if obj_id != user_info["uid"]:
                        notice_info = {
                            "author_id": obj_id,
                            "user_id": user_info["uid"],           
                            "notice_type": 15,
                            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        self.notice_model.add_new_notice(notice_info)

                    # update user_info
                    user = self.user_model.get_user_by_uid(obj_id)
                    self.user_model.update_user_info_by_user_id(obj_id, {"followers": user.followers+1})
                    self.user_model.update_user_info_by_user_id(user_info.uid, {"followees": user_info.followees+1})

                if obj_type=='q' or obj_type=='p':
                    if obj_type == 'q':
                        feed_type = 3
                        notice_type = 2
                    else:
                        feed_type = 9
                        notice_type = 9
                    # add feed: user 关注了问题
                    feed_info = {
                        "user_id": user_info["uid"],           
                        "post_id": obj_id,
                        "feed_type": feed_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    self.feed_model.add_new_feed(feed_info)

                    post = self.post_model.get_post_by_post_id(obj_id)
                    self.post_model.update_post_by_post_id(post.id, {"follow_num": post.follow_num+1})

                    # add notice: user 关注了问题
                    if post.author_id != user_info["uid"]:
                        notice_info = {
                            "author_id": post.author_id,
                            "user_id": user_info["uid"],           
                            "post_id": obj_id,
                            "notice_type": notice_type,
                            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        self.notice_model.add_new_notice(notice_info)

                    follows = self.follow_model.get_post_all_follows(obj_id)
                    if len(follows) > THRESHOLD:
                        tags = self.post_tag_model.get_post_all_tags(obj_id)
                        if obj_type == 'q':
                            feed_type = 4
                        else:
                            feed_type = 10
                        for tag in tags["list"]:
                            # add feed: tag 下很多人关注了问题
                            feed_info = {
                                "tag_id": tag.id,           
                                "post_id": obj_id,
                                "feed_type": feed_type,
                                "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                            }
                            self.feed_model.add_new_feed(feed_info)
            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                    "message": "successed",
            }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                    "message": "failed",
            }))

class VotePostHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        vote_type = self.get_argument('vote', "null")

        if(user_info):
            post = self.post_model.get_post_by_post_id(post_id)
            vote = self.vote_model.get_vote_by_user_and_post(user_info.uid, post_id)
            post_author = self.user_model.get_user_by_uid(post.author_id)
            if post.post_type == 'q':
                feed_type = 13;
            else:
                feed_type = 15;

            if vote:
                if vote_type==vote.up_down:
                    self.vote_model.delete_vote_by_id(vote.id)
                    if vote.up_down=='up':
                        # cancel up vote
                        self.post_model.update_post_by_post_id(post.id, {"up_num": post.up_num-1})
                        feed = self.feed_model.get_feed_user_vote_post_feed(user_info.uid, post.id)
                        if feed:
                            self.feed_model.delete_feed_by_id(feed.id)

                        if post.up_num-1 <= THRESHOLD:
                            if post.post_type == 'q':
                                feed_type2 = 14;
                            else:
                                feed_type2 = 16;
                            self.feed_model.delete_feed_by_post_and_type(post_id, feed_type2)
                        self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend-1})
                        self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 7, "amount": 1, "balance": user_info.income-user_info.expend, "post_id": post_id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                        self.user_model.update_user_info_by_user_id(post_author.uid, {"income": post_author.income-1, "up_num": post_author.up_num-1})
                        self.balance_model.add_new_balance({"author_id":  post_author.uid, "balance_type": 8, "amount": -1, "balance": post_author.income-post_author.expend, "post_id": post_id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
                    else:
                        self.post_model.update_post_by_post_id(post.id, {"down_num": post.down_num-1})
                        self.user_model.update_user_info_by_user_id(post_author.uid, {"down_num": post_author.down_num-1})
                else:
                    if vote.up_down=='up':
                        # cancel up vote
                        self.post_model.update_post_by_post_id(post.id, {"up_num": post.up_num-1, "down_num": post.down_num+1})
                        feed = self.feed_model.get_feed_user_vote_post_feed(user_info.uid, post.id)
                        if feed:
                            self.feed_model.delete_feed_by_id(feed.id)

                        if post.up_num-1 <= THRESHOLD:
                            if post.post_type == 'q':
                                feed_type2 = 14;
                            else:
                                feed_type2 = 16;
                            self.feed_model.delete_feed_by_post_and_type(post_id, feed_type2)
                        self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend-1})
                        self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 7, "amount": 1, "balance": user_info.income-user_info.expend, "post_id": post_id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                        self.user_model.update_user_info_by_user_id(post_author.uid, {"income": post_author.income-1, "up_num": post_author.up_num-1, "down_num": post_author.down_num+1})
                        self.balance_model.add_new_balance({"author_id":  post_author.uid, "balance_type": 8, "amount": -1, "balance": post_author.income-post_author.expend, "post_id": post_id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
                    else:
                        self.post_model.update_post_by_post_id(post.id, {"up_num": post.up_num+1, "down_num": post.down_num-1})
                        # add feed: user 赞同了回答
                        feed_info = {
                            "user_id": user_info.uid,           
                            "post_id": post_id,
                            "feed_type": feed_type,
                            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        self.feed_model.add_new_feed(feed_info)

                        if post.up_num+1 > THRESHOLD:
                            tags = self.post_tag_model.get_post_all_tags(post.id)
                            if post.post_type == 'q':
                                feed_type2 = 14;
                            else:
                                feed_type2 = 16;
                            for tag in tags["list"]:
                                # add feed: tag 下很多人关注了问题
                                feed_info2 = {
                                    "tag_id": tag.id,           
                                    "post_id": post.id,
                                    "feed_type": feed_type2,
                                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                                }
                                self.feed_model.add_new_feed(feed_info2)
                        self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend+1})
                        self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 5, "amount": -1, "balance": user_info.income-user_info.expend, "post_id": post_id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                        self.user_model.update_user_info_by_user_id(post_author.uid, {"income": post_author.income+1,  "up_num": post_author.up_num+1, "down_num": post_author.down_num-1})
                        self.balance_model.add_new_balance({"author_id":  post_author.uid, "balance_type": 6, "amount": 1, "balance": post_author.income-post_author.expend, "post_id": post_id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
                    self.vote_model.update_vote_by_id(vote.id, {"up_down": vote_type, "created": time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                self.vote_model.add_new_vote({"post_id": post_id, "up_down": vote_type, "author_id": user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')})
                if vote_type=='up':
                    self.post_model.update_post_by_post_id(post.id, {"up_num": post.up_num+1})

                    # add feed: user 赞同了回答
                    feed_info = {
                        "user_id": user_info.uid,           
                        "post_id": post_id,
                        "feed_type": feed_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    self.feed_model.add_new_feed(feed_info)

                    if post.up_num+1 > THRESHOLD:
                            tags = self.post_tag_model.get_post_all_tags(post.id)
                            if post.post_type == 'q':
                                feed_type2 = 14
                            else:
                                feed_type2 = 16
                            for tag in tags["list"]:
                                # add feed: tag 下很多人关注了问题
                                feed_info2 = {
                                    "tag_id": tag.id,           
                                    "post_id": post.id,
                                    "feed_type": feed_type2,
                                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                                }
                                self.feed_model.add_new_feed(feed_info2)

                    if post.post_type == 'q':
                        notice_type = 16
                    else:
                        notice_type = 17
                    # add notice: 赞了你的问题
                    notice_info = {
                        "author_id": post.author_id,
                        "user_id": user_info["uid"],           
                        "post_id": post_id,
                        "notice_type": notice_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    self.notice_model.add_new_notice(notice_info)

                    self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend+1})
                    self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 5, "amount": -1, "balance": user_info.income-user_info.expend, "post_id": post_id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                    self.user_model.update_user_info_by_user_id(post_author.uid, {"income": post_author.income+1, "up_num": post_author.up_num+1})
                    self.balance_model.add_new_balance({"author_id":  post_author.uid, "balance_type": 6, "amount": 1, "balance": post_author.income-post_author.expend, "post_id": post_id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
                else:
                    self.post_model.update_post_by_post_id(post.id, {"down_num": post.down_num+1})
                    self.user_model.update_user_info_by_user_id(post_author.uid, {"up_num": post_author.down_num+1})
            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class VoteReplyHandler(BaseHandler):
    def get(self, reply_id, template_variables = {}):
        user_info = self.current_user
        vote_type = self.get_argument('vote', "null")

        if(user_info):
            reply = self.reply_model.get_reply_by_id(reply_id)
            vote = self.vote_model.get_vote_by_user_and_reply(user_info.uid, reply_id)
            post = self.post_model.get_post_by_post_id(reply.post_id)
            reply_author = self.user_model.get_user_by_uid(reply.author_id)
            if post.post_type == 'q':
                feed_type = 5;
            else:
                feed_type = 11;

            if vote:
                if vote_type==vote.up_down:
                    self.vote_model.delete_vote_by_id(vote.id)
                    if vote.up_down=='up':
                        self.reply_model.update_reply_by_id(reply.id, {"up_num": reply.up_num-1})
                        feed = self.feed_model.get_feed_user_vote_reply_feed(user_info.uid, reply.id)
                        if feed:
                            self.feed_model.delete_feed_by_id(feed.id)

                        if reply.up_num-1 <= THRESHOLD:
                            if post.post_type == 'q':
                                feed_type2 = 6;
                            else:
                                feed_type2 = 12;
                            self.feed_model.delete_feed_by_reply_and_type(reply_id, feed_type2)

                        self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend-1})
                        self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 7, "amount": 1, "balance": user_info.income-user_info.expend, "post_id": post.id, "reply_id": reply.id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                        self.user_model.update_user_info_by_user_id(reply_author.uid, {"up_num": reply_author.up_num-1, "income": reply_author.income-1})
                        self.balance_model.add_new_balance({"author_id":  reply_author.uid, "balance_type": 8, "amount": -1, "balance": reply_author.income-reply_author.expend, "post_id": post.id, "reply_id": reply.id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
                    else:
                        self.reply_model.update_reply_by_id(reply.id, {"down_num": reply.down_num-1})
                        self.user_model.update_user_info_by_user_id(reply_author.uid, {"down_num": reply_author.down_num-1})
                else:
                    if vote.up_down=='up':
                        self.reply_model.update_reply_by_id(reply.id, {"up_num": reply.up_num-1, "down_num": reply.down_num+1})
                        self.user_model.update_user_info_by_user_id(reply_author.uid, {"up_num": reply_author.up_num-1, "down_num": reply_author.down_num+1})
                        feed = self.feed_model.get_feed_user_vote_reply_feed(user_info.uid, reply.id)
                        if feed:
                            self.feed_model.delete_feed_by_id(feed.id)

                        if reply.up_num-1 <= THRESHOLD:
                            if post.post_type == 'q':
                                feed_type2 = 6;
                            else:
                                feed_type2 = 12;
                            self.feed_model.delete_feed_by_reply_and_type(reply_id, feed_type2)

                        self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend-1})
                        self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 7, "amount": 1, "balance": user_info.income-user_info.expend, "post_id": post.id, "reply_id": reply.id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                        self.user_model.update_user_info_by_user_id(reply_author.uid, {"income": reply_author.income-1})
                        self.balance_model.add_new_balance({"author_id":  reply_author.uid, "balance_type": 8, "amount": -1, "balance": reply_author.income-reply_author.expend, "post_id": post.id, "reply_id": reply.id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
                    else:
                        self.reply_model.update_reply_by_id(reply.id, {"up_num": reply.up_num+1, "down_num": reply.down_num-1})
                        
                        # add feed: user 赞同了回答
                        feed_info = {
                            "user_id": user_info.uid,           
                            "post_id": reply.post_id,
                            "reply_id": reply.id,
                            "feed_type": feed_type,
                            "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        self.feed_model.add_new_feed(feed_info)

                        if reply.up_num+1 > THRESHOLD:
                            tags = self.post_tag_model.get_post_all_tags(post.id)
                            if post.post_type == 'q':
                                feed_type2 = 6;
                            else:
                                feed_type2 = 12;
                            for tag in tags["list"]:
                                # add feed: tag 下很多人关注了问题
                                feed_info2 = {
                                    "tag_id": tag.id,           
                                    "post_id": post.id,
                                    "reply_id": reply_id,
                                    "feed_type": feed_type2,
                                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                                }
                                self.feed_model.add_new_feed(feed_info2)

                        self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend+1})
                        self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 5, "amount": -1, "balance": user_info.income-user_info.expend, "post_id": post.id, "reply_id": reply.id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                        self.user_model.update_user_info_by_user_id(reply_author.uid, {"income": reply_author.income+1, "up_num": reply_author.up_num+1, "down_num": reply_author.down_num-1})
                        self.balance_model.add_new_balance({"author_id":  reply_author.uid, "balance_type": 6, "amount": 1, "balance": reply_author.income-reply_author.expend, "post_id": post.id, "reply_id": reply.id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
                    self.vote_model.update_vote_by_id(vote.id, {"up_down": vote_type, "created": time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                self.vote_model.add_new_vote({"reply_id": reply_id, "up_down": vote_type, "author_id": user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')})
                if vote_type=='up':
                    self.reply_model.update_reply_by_id(reply.id, {"up_num": reply.up_num+1})

                    # add feed: user 赞同了回答
                    feed_info = {
                        "user_id": user_info.uid,           
                        "post_id": reply.post_id,
                        "reply_id": reply.id,
                        "feed_type": feed_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    self.feed_model.add_new_feed(feed_info)

                    if reply.up_num+1 > THRESHOLD:
                            tags = self.post_tag_model.get_post_all_tags(post.id)
                            if post.post_type == 'q':
                                feed_type2 = 6
                            else:
                                feed_type2 = 12
                            for tag in tags["list"]:
                                # add feed: tag 下很多人关注了问题
                                feed_info2 = {
                                    "tag_id": tag.id,           
                                    "post_id": post.id,
                                    "reply_id": reply_id,
                                    "feed_type": feed_type2,
                                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                                }
                                self.feed_model.add_new_feed(feed_info2)

                    if post.post_type == 'q':
                        notice_type = 4
                    else:
                        notice_type = 11
                    # add notice: 赞同了你的回答
                    notice_info = {
                        "author_id": reply.author_id,
                        "user_id": user_info["uid"],           
                        "post_id": reply.post_id,
                        "reply_id": reply.id,
                        "notice_type": notice_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    self.notice_model.add_new_notice(notice_info)

                    self.user_model.update_user_info_by_user_id(user_info.uid, {"expend": user_info.expend+1})
                    self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 5, "amount": -1, "balance": user_info.income-user_info.expend, "post_id": post.id, "reply_id": reply.id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                    self.user_model.update_user_info_by_user_id(reply_author.uid, {"income": reply_author.income+1, "up_num": reply_author.up_num+1})
                    self.balance_model.add_new_balance({"author_id":  reply_author.uid, "balance_type": 6, "amount": 1, "balance": reply_author.income-reply_author.expend, "post_id": post.id, "reply_id": reply.id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
                else:
                    self.reply_model.update_reply_by_id(reply.id, {"down_num": reply.down_num+1})
                    self.user_model.update_user_info_by_user_id(reply_author.uid, {"down_num": reply_author.down_num+1})
            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))


class ThankHandler(BaseHandler):
    def get(self, obj_id, template_variables = {}):
        user_info = self.current_user
        obj_type = self.get_argument('type', "null")

        if(user_info):
            if obj_type=='post':
                post = self.post_model.get_post_by_post_id(obj_id)
                self.thank_model.add_new_thank({
                        "from_user": user_info.uid,
                        "to_user": post.author_id,
                        "obj_id": obj_id,
                        "obj_type": obj_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    })
                to_user = self.user_model.get_user_by_uid(post.author_id)
                self.user_model.update_user_info_by_user_id(to_user.uid, {
                        "thank_num": to_user.thank_num+1,
                    })

                if post.post_type=='q':
                    notice_type = 3
                else:
                    notice_type = 10
                # add notice: user 感谢了问题
                notice_info = {
                    "author_id": post.author_id,
                    "user_id": user_info["uid"],           
                    "post_id": post.id,
                    "notice_type": notice_type,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                self.notice_model.add_new_notice(notice_info)

                self.user_model.update_user_info_by_user_id(user_info.uid, {"income": user_info.expend+10})
                self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 9, "amount": -10, "balance": user_info.income-user_info.expend-10, "post_id": post.id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                post_author = self.user_model.get_user_by_uid(post.author_id)
                self.user_model.update_user_info_by_user_id(post_author.uid, {"income": post_author.income+10})
                self.balance_model.add_new_balance({"author_id":  post_author.uid, "balance_type": 10, "amount": 10, "balance": post_author.income-post_author.expend+10, "post_id": post.id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 
            else:
                reply = self.reply_model.get_reply_by_id(obj_id)
                self.thank_model.add_new_thank({
                        "from_user": user_info.uid,
                        "to_user": reply.author_id,
                        "obj_id": obj_id,
                        "obj_type": obj_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    })
                to_user = self.user_model.get_user_by_uid(reply.author_id)
                self.user_model.update_user_info_by_user_id(to_user.uid, {
                        "thank_num": to_user.thank_num+1,
                    })

                post = self.post_model.get_post_by_post_id(reply.post_id)
                if post.post_type=='q':
                    notice_type = 5
                else:
                    notice_type = 12
                # add notice: user 感谢了问题
                notice_info = {
                    "author_id": reply.author_id,
                    "user_id": user_info["uid"],   
                    "reply_id": reply.id,           
                    "post_id": post.id,
                    "notice_type": notice_type,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                self.notice_model.add_new_notice(notice_info)

                self.user_model.update_user_info_by_user_id(user_info.uid, {"income": user_info.expend+10})
                self.balance_model.add_new_balance({"author_id":  user_info.uid, "balance_type": 9, "amount": -10, "balance": user_info.income-user_info.expend-10, "post_id": post.id, "reply_id": reply.id, "user_id": post.author_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})  
                post_author = self.user_model.get_user_by_uid(post.author_id)
                self.user_model.update_user_info_by_user_id(post_author.uid, {"income": post_author.income+10})
                self.balance_model.add_new_balance({"author_id":  post_author.uid, "balance_type": 10, "amount": 10, "balance": post_author.income-post_author.expend+10, "post_id": post.id, "reply_id": reply.id, "user_id":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')}) 

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))


class ReportHandler(BaseHandler):
    def get(self, obj_id, template_variables = {}):
        user_info = self.current_user
        obj_type = self.get_argument('type', "null")

        if(user_info):
            if obj_type=='post':
                post = self.post_model.get_post_by_post_id(obj_id)
                self.report_model.add_new_report({
                        "from_user": user_info.uid,
                        "to_user": post.author_id,
                        "obj_id": obj_id,
                        "obj_type": obj_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    })
                to_user = self.user_model.get_user_by_uid(post.author_id)
                self.user_model.update_user_info_by_user_id(to_user.uid, {
                        "report_num": to_user.report_num+1,
                    })
            else:
                reply = self.reply_model.get_reply_by_id(obj_id)
                self.report_model.add_new_report({
                        "from_user": user_info.uid,
                        "to_user": reply.author_id,
                        "obj_id": obj_id,
                        "obj_type": obj_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    })
                to_user = self.user_model.get_user_by_uid(reply.author_id)
                self.user_model.update_user_info_by_user_id(to_user.uid, {
                        "report_num": to_user.report_num+1,
                    })

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class DeleteReplyHandler(BaseHandler):
    def get(self, reply_id, template_variables = {}):
        user_info = self.current_user

        if(user_info):
            reply = self.reply_model.get_reply_by_id(reply_id)
            post = self.post_model.get_post_by_post_id(reply.post_id)
            self.post_model.update_post_by_post_id(post.id, {"reply_num": post.reply_num-1, "updated": time.strftime('%Y-%m-%d %H:%M:%S')})
            self.vote_model.delete_vote_by_reply_id(reply_id)
            self.thank_model.delete_thank_by_reply_id(reply_id)
            self.report_model.delete_report_by_reply_id(reply_id)
            self.reply_model.delete_reply_by_id(reply_id)
            self.feed_model.delete_feed_by_reply_id(reply_id)
            self.notice_model.delete_notice_by_reply_id(reply_id)

            post = self.post_model.get_post_by_post_id(reply.post_id)
            if post.post_type=='q':
                # update user_info
                self.user_model.update_user_info_by_user_id(user_info.uid, {"answers": user_info.answers-1})
            else:
                # update user_info
                self.user_model.update_user_info_by_user_id(user_info.uid, {"comments": user_info.comments-1})

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class EditReplyHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, reply_id, template_variables = {}):
        user_info = self.current_user
        data = json.loads(self.request.body)
        reply_content = data["reply_content"]

        if(user_info):
            self.reply_model.update_reply_by_id(reply_id, {"content": reply_content})

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class AddItemHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, template_variables = {}):
        user_info = self.current_user

        if(user_info):
            data = json.loads(self.request.body)
            url = data["url"]
            sku = ""
            link = ""
            pyq_url = ""
            vendor = ""
            amazoncn_pattern = re.compile(r'http://www.amazon.cn/gp/product/([0-9A-Z]{10})')
            amazoncn_match = amazoncn_pattern.search(url)
            if amazoncn_match: 
                sku = amazoncn_match.group(1)
                link = 'http://www.amazon.cn/gp/product/' + sku
                pyq_url = link
                vendor = 'amazoncn'
                item = self.item_model.get_item_by_sku_and_vendor2(sku, vendor)
                if item:
                    self.item_model.update_item_by_id(item.id, {"add_num": item.add_num+1})
                    self.write(lib.jsonp.print_JSON({
                        "success": 1,
                        "id": item.id,
                        "sku": item.sku,
                        "name": item.name,
                        "img": item.img,
                        "like_num": item.like_num,
                        "price": item.price,
                        "vendor": item.vendor
                    }))
                else:
                    doc=pyq(pyq_url)
                    info = doc('.a-container')
                    name = info.find('#centerCol #productTitle').text()
                    img = info.find('#leftCol #imgTagWrapperId img').attr('src')
                    price_url = 'http://s.etao.com/detail/10.html?uc_url=http%3A%2F%2Fwww.amazon.cn%2Fgp%2Fproduct%2F'+sku
                    price_doc=pyq(price_url)
                    price = price_doc('.real-price-num').text()
                    item_id = self.item_model.add_new_item({
                        "sku": sku,
                        "name": name,
                        "img": img,
                        "link": link,
                        "vendor": vendor,
                        "price": price
                    })
                    self.write(lib.jsonp.print_JSON({
                        "success": 1,
                        "id": item_id,
                        "sku": sku,
                        "name": name,
                        "img": img,
                        "like_num": 0,
                        "price": price,
                        "vendor": vendor
                    }))             
                return
            jd_pattern = re.compile(r'http://item.jd.com/(\d+).html') 
            jd_match = jd_pattern.search(url) 
            if jd_match: 
                sku = jd_match.group(1)
                link = 'http://item.jd.com/' + sku + '.html'
                pyq_url = 'http://gouwu.sogou.com/compare?p=40251500&clf=2&query=129493916&adsUrl=http%3A%2F%2Fitem.jd.com%2F'+sku+'.html'
                vendor = 'jd'
            tmall_pattern = re.compile(r'http://detail.tmall.com/item.htm?\S*id=(\d+)')
            tmall_match = tmall_pattern.search(url) 
            if tmall_match: 
                sku = tmall_match.group(1)
                link = 'http://detail.tmall.com/item.htm?id=' + sku
                pyq_url = 'http://gouwu.sogou.com/compare?p=40251500&query=-100&adsUrl=http%3A%2F%2Fdetail.tmall.com%2Fitem.htm%3Fid%3D'+sku
                vendor = 'tmall'
            taobao_pattern = re.compile(r'http://item.taobao.com/item.htm?\S*id=(\d+)')
            taobao_match = taobao_pattern.search(url) 
            if taobao_match: 
                sku = taobao_match.group(1)
                link = 'http://item.taobao.com/item.htm?id=' + sku
                pyq_url = 'http://gouwu.sogou.com/compare?p=40251500&query=-100&adsUrl=http%3A%2F%2Fitem.taobao.com%2Fitem.htm%3Fid%3D'+sku
                vendor = 'taobao'
            if jd_match or tmall_match or taobao_match: 
                item = self.item_model.get_item_by_sku_and_vendor(sku, vendor)
                if item:
                    self.item_model.update_item_by_id(item.id, {"add_num": item.add_num+1})
                    self.write(lib.jsonp.print_JSON({
                        "success": 1,
                        "id": item.id,
                        "sku": item.sku,
                        "name": item.name,
                        "img": item.img,
                        "like_num": item.like_num,
                        "price": item.price,
                        "vendor": item.vendor
                    }))
                else:
                    doc=pyq(pyq_url)
                    info = doc('.nbox1')
                    name = info.find('.nst1 #sb_title').text()
                    img = info.find('.nbox1_imgmn #sb_pic img').attr('src')
                    price = info.find('.n_list .shopprice').text()
                    item_id = self.item_model.add_new_item({
                        "sku": sku,
                        "name": name,
                        "img": img,
                        "link": link,
                        "vendor": vendor,
                        "price": price
                    })
                    self.write(lib.jsonp.print_JSON({
                        "success": 1,
                        "id": item_id,
                        "sku": sku,
                        "name": name,
                        "img": img,
                        "like_num": 0,
                        "price": price,
                        "vendor": vendor
                    }))                
            else:
                self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class ItemHandler(BaseHandler):
    def get(self, item_id, template_variables = {}):
        item = self.item_model.get_item_by_id(item_id)
        if item:
            template_variables["redirect_time"] = 1
            template_variables["redirect_url"] = item.link
            self.render("item.html", **template_variables)
            self.item_model.update_item_by_id(item.id, {"view_num": item.view_num+1})
        else:
            self.render("404.html", **template_variables)

class LikeItemHandler(BaseHandler):
    def get(self, item_id, template_variables = {}):
        user_info = self.current_user

        if(user_info):
            like = self.like_item_model.get_like_by_author_and_item(user_info.uid, item_id)
            if not like:
                item = self.item_model.get_item_by_id(item_id)
                self.item_model.update_item_by_id(item_id, {"like_num": item.like_num+1})
                self.like_item_model.add_new_like({
                    "author_id": user_info.uid,
                    "item_id": item_id,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S')
                })
                
            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))

        

class DeletePostHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user

        if(user_info):
            self.feed_model.delete_feed_by_post_id(post_id)
            self.post_tag_model.delete_post_tag_by_post_id(post_id)
            self.follow_model.delete_follow_by_post_id(post_id)
            self.thank_model.delete_thank_by_post_id(post_id)
            self.report_model.delete_report_by_post_id(post_id)

            post = self.post_model.get_post_by_post_id(post_id)
            if post.post_type=='q':
                # update user_info
                self.user_model.update_user_info_by_user_id(user_info.uid, {"questions": user_info.questions-1})
            else:
                # update user_info
                self.user_model.update_user_info_by_user_id(user_info.uid, {"posts": user_info.posts-1})

            self.post_model.delete_post_by_post_id(post_id)

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))


class NoticeHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        p = int(self.get_argument("p", "1"))
        if(user_info):
            template_variables["active_tab"] = "me"
            template_variables["notices"] = self.notice_model.get_user_all_notices(user_info.uid, current_page = p)
            template_variables["feeds"] = self.follow_model.get_user_all_follow_post_feeds(user_info.uid, current_page = p)
            if user_info.view_follow:
                template_variables["post_count"] = self.follow_model.get_user_all_follow_post_feeds_count(user_info.uid, user_info.view_follow, time.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                template_variables["post_count"] = None
            self.notice_model.set_user_notice_as_read(user_info.uid)
            template_variables["invite_count"] = self.invite_model.get_user_unread_invite_count(user_info.uid)
            if is_mobile_browser(self):
                self.render("mobile/notice.html", **template_variables)
            else:
                self.render("notice.html", **template_variables)
        else:
            self.redirect("/?s=signin&link=notifications")

class FollowsHandler(BaseHandler):
    def get(self, username, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        p = int(self.get_argument("p", "1"))
        active_tab = self.get_argument('tab', "question")
        template_variables["active_tab"] = active_tab
        view_user = self.user_model.get_user_by_username(username)
        template_variables["view_user"] = view_user
        template_variables["feeds1"] = self.follow_model.get_user_follow_questions(view_user.uid, current_page = p)
        template_variables["feeds2"] = self.follow_model.get_user_follow_posts(view_user.uid, current_page = p)
        template_variables["tags"] = self.follow_model.get_user_follow_tags(view_user.uid)

        if(user_info):            
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, view_user.uid, 'u')
            template_variables["feeds3"] = self.follow_model.get_user_followees(view_user.uid, user_info.uid, current_page = p)
            template_variables["feeds4"] = self.follow_model.get_user_followers(view_user.uid, user_info.uid, current_page = p)
        else:
            template_variables["feeds3"] = self.follow_model.get_user_followees2(view_user.uid, current_page = p)
            template_variables["feeds4"] = self.follow_model.get_user_followers2(view_user.uid, current_page = p)
            template_variables["link"] = "follows"
            template_variables["link2"] = username
            template_variables["follow"] = None
        if user_info and user_info==view_user:
            if is_mobile_browser(self):
                self.render("mobile/follows.html", **template_variables)
            else:
                self.render("follows.html", **template_variables)
        else:
            self.render("404.html", **template_variables)

class GetInviteUsersHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user

        if(user_info):  
            users = self.post_tag_model.get_post_related_users(post_id, user_info.uid)          
            jarray = []
            uids = []
            i = 0
            for user in users["list"]:
                if len(uids) == 20:
                    continue
                if user.uid==None:
                    continue
                if user.uid in uids:
                    continue
                invite = self.invite_model.get_invite(user_info.uid, user.uid, post_id)
                if invite:
                    continue
                if user.avatar==None:
                    user.avatar = "http://mmm-static.qiniudn.com/avatar.png-avatar"
                if user.sign==None:
                    user.sign=""
                jobject = {
                    "uid": user.uid,
                    "username": user.username,
                    "avatar": user.avatar,
                    "sign": user.sign,
                    "answers": user.answers
                }
                jarray.append(jobject)
                uids.append(user.uid)
                i=i+1

            self.write(lib.jsonp.print_JSON({"users": jarray}))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class InviteToAnswerHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        invite_user = self.get_argument('u', "null")

        if(user_info):
            post = self.post_model.get_post_by_post_id(post_id)
            invite = self.invite_model.get_invite(user_info.uid, invite_user, post_id)
            if invite:
                self.invite_model.delete_invite_by_id(invite.id)
            else:
                self.invite_model.add_new_invite({"from_user": user_info.uid, "to_user": invite_user, "post_id": post_id, "created": time.strftime('%Y-%m-%d %H:%M:%S')})   

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class InvitationsHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        p = int(self.get_argument("p", "1"))

        if(user_info):
            template_variables["feeds"] = self.invite_model.get_user_invites(user_info.uid, current_page = p)
            template_variables["notice_count"] = self.notice_model.get_user_unread_notice_count(user_info.uid)
            self.invite_model.set_user_invite_as_read(user_info.uid)
            if is_mobile_browser(self):
                self.render("mobile/invitations.html", **template_variables)
            else:
                self.render("invitations.html", **template_variables)
        else:
            self.redirect("/?s=signin&link=invitations")

class InviteToEmailHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        post = self.post_model.get_post_by_post_id(post_id)
        template_variables["user_info"] = user_info
        email = self.get_argument('email', "null")
        print email
        invite_code = "%s" % uuid.uuid1()
        self.icode_model.add_new_icode({"code": invite_code, "user_created":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')})

        if(user_info):
            # send invite to answer mail to user
            mail_content = self.render_string("mail/invite-answer.html", user_info=user_info, invite_code=invite_code, post=post)
            print "send mail"

            params = { "api_user": "postmaster@mmmai-invite.sendcloud.org", \
                "api_key" : "bRjboOZIVFUU9s0q",\
                "from" : "noreply@mmmai.com", \
                "to" : email, \
                "fromname" : "买买买", \
                "subject" : user_info.username+"邀请您回答问题："+post.title+"--买买买", \
                "html": mail_content \
            }

            url="https://sendcloud.sohu.com/webapi/mail.send.xml"
            r = requests.post(url, data=params)
            print r.text

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class InviteToJoinHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        email = self.get_argument('email', "null")
        print email
        invite_code = "%s" % uuid.uuid1()
        self.icode_model.add_new_icode({"code": invite_code, "user_created":  user_info.uid, "created": time.strftime('%Y-%m-%d %H:%M:%S')})

        if(user_info):
            # send invite to answer mail to user
            mail_content = self.render_string("mail/invite-join.html", user_info=user_info, invite_code=invite_code)
            print "send mail"

            params = { "api_user": "postmaster@mmmai-invite.sendcloud.org", \
                "api_key" : "bRjboOZIVFUU9s0q",\
                "from" : "noreply@mmmai.com", \
                "to" : email, \
                "fromname" : "买买买", \
                "subject" : "邀请加入买买买", \
                "html": mail_content \
            }

            url="https://sendcloud.sohu.com/webapi/mail.send.xml"
            r = requests.post(url, data=params)
            print r.text

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class InviteHandler(BaseHandler):
    def get(self, invite_code, template_variables = {}):
        post_id = self.get_argument("p", "")
        # validate invite code
        icode = self.icode_model.get_invite_code(invite_code)
        if not icode:
            print "fasdfsad"
            template_variables["error_text"] = "对不起，邀请链接无效！"
            self.render("404.html", **template_variables)
        else:
            if icode.used==1:
                template_variables["error_text"] = "对不起，邀请链接已经被使用！"
                self.render("404.html", **template_variables)
            else:
                if post_id=="":
                    self.redirect("/?s=signup&i="+invite_code)
                else:
                    self.redirect("/p/"+post_id+"?s=signup&i="+invite_code)    

class EditTagHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,  tag_id, template_variables = {}):
        user_info = self.get_current_user()
        tag= self.tag_model.get_tag_by_tag_id(tag_id)
        template_variables["user_info"] = user_info
        template_variables["tag"] = tag
        template_variables["categorys"] = self.category_model.get_tag_categorys()
        template_variables["tag_types"] = self.tag_type_model.get_tag_types()
        allTags = self.tag_model.get_all_tags()
        allTagStr = ''
        i=0
        for tag in allTags:
            if i==0:
                allTagStr = tag.name
            else:
                allTagStr = allTagStr + ','+ tag.name
            i=i+1
        template_variables["allTagStr"] = allTagStr 

        self.render("edit_tag.html", **template_variables)

    @tornado.web.authenticated
    def post(self, tag_id, template_variables = {}):
        template_variables = {}

        # validate the fields
        form = EditTagForm(self)
        tag= self.tag_model.get_tag_by_tag_id(tag_id)
        category = self.category_model.get_category_by_name(form.category.data)
        tag_type = self.tag_type_model.get_tag_type_by_name(form.tag_type.data)
        if("thumb" in self.request.files):            
            origin_thumb = tag.thumb
            
            tag_name = "%s" % uuid.uuid1()
            thumb_raw = self.request.files["thumb"][0]["body"]
            thumb_buffer = StringIO.StringIO(thumb_raw)
            thumb = Image.open(thumb_buffer)

            usr_home = os.path.expanduser('~')
            thumb.save(usr_home+"/www/avati/static/tmp/m_%s.png" % tag_name, "PNG")

            uptoken = q.upload_token("mmm-avatar", "m_%s.png" % tag_name)
            data=open(usr_home+"/www/avati/static/tmp/m_%s.png" % tag_name)
            ret, info = put_data(uptoken, "m_%s.png" % tag_name, data)
 
            os.remove(usr_home+"/www/avati/static/tmp/m_%s.png" % tag_name)

            thumb_name = "http://mmm-avatar.qiniudn.com/m_"+tag_name
            self.tag_model.update_tag_by_tag_id(tag_id, {"name": form.name.data, "intro": form.intro.data, "thumb": "%s.png" %  thumb_name, "category": category.id, "tag_type": tag_type.id})

            if origin_thumb:
                pattern = re.compile(r'm_.*.png') 
                match = pattern.search(origin_thumb) 
                if match: 
                    ret, info = bucket.delete("mmm-avatar", match.group())
                    #ret, err = qiniu.rs.Client().delete("mmm-avatar", match.group())
        else:
            self.tag_model.update_tag_by_tag_id(tag_id, {"name": form.name.data, "intro": form.intro.data, "category": category.id, "tag_type": tag_type.id})

        if tag.category != category.id:
            old_category =  self.category_model.get_category_by_id(tag.category)
            self.category_model.update_category_by_id(tag.category, {"tag_num": old_category.tag_num-1})
            self.category_model.update_category_by_id(category.id, {"tag_num":category.tag_num+1})

        # process tags
        tagStr = form.tag.data
        if tagStr:
            print tagStr
            tagNames = tagStr.split(',')  
            for tagName in tagNames:  
                tag = self.tag_model.get_tag_by_tag_name(tagName)
                if tag:
                    self.tag_parent_model.add_new_tag_parent({"tag_id": tag_id, "parent_id": tag.id})
                 
        template_variables["success_message"] = [u"标签已更新"]
        self.redirect("/t/"+form.name.data)


class UploadHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, template_variables = {}):
        template_variables = {}

        # validate the fields
        if("file" in self.request.files):            
            file_name = "%s" % uuid.uuid1()
            file_raw = self.request.files["file"][0]["body"]
            file_buffer = StringIO.StringIO(file_raw)
            file = Image.open(file_buffer)

            usr_home = os.path.expanduser('~')
            file.save(usr_home+"/www/avati/static/tmp/m_%s.png" % file_name, "PNG")  

            uptoken = q.upload_token("mmm-cdn", "m_%s.png" % file_name)
            data=open(usr_home+"/www/avati/static/tmp/m_%s.png" % file_name)
            ret, info = put_data(uptoken, "m_%s.png" % file_name, data)
 
            os.remove(usr_home+"/www/avati/static/tmp/m_%s.png" % file_name)

            file_name = "http://mmm-cdn.qiniudn.com/m_"+file_name+".png"

            self.write(file_name)

class ListHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["scrollspy"] = "scrollspy"
        if(user_info):
            template_variables["tag_types"] = self.tag_type_model.get_tag_types()
            template_variables["tags"] = self.follow_model.get_user_follow_tags(user_info.uid)
            self.render("list.html", **template_variables)
        else:
            self.redirect("/?s=signin&link=list")

class BalanceHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        p = int(self.get_argument("p", "1"))
        if(user_info):
            gold_coins = (user_info.income - user_info.expend )/ 10000
            silver_coins = (user_info.income - user_info.expend )% 10000     
            bronze_coins = silver_coins  % 100
            silver_coins = silver_coins / 100
            template_variables["gold_coins"] = gold_coins
            template_variables["silver_coins"] = silver_coins
            template_variables["bronze_coins"] = bronze_coins
            template_variables["notice_count"] = self.notice_model.get_user_unread_notice_count(user_info.uid)  
            template_variables["invite_count"] = self.invite_model.get_user_unread_invite_count(user_info.uid)
            template_variables["balances"] = self.balance_model.get_user_balances(user_info.uid, current_page = p)
            if is_mobile_browser(self):
                self.render("mobile/balance.html", **template_variables)
            else:
                self.render("balance.html", **template_variables)
        else:
            self.redirect("/?s=signin&link=list")

class PageNotFoundHandler(BaseHandler):
    def get(self, template_variables = {}):
        self.render("404.html", **template_variables)

class UpdateUserViewFollowHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        
        if(user_info):
            self.user_model.update_user_info_by_user_id(user_info.uid, {"view_follow": time.strftime('%Y-%m-%d %H:%M:%S')})
            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class GetYoukuHandler(BaseHandler):
    def get(self, youku_id, template_variables = {}):

        json_link = "http://v.youku.com/player/getPlayList/VideoIDS/"+youku_id
        video_json = json.load(urllib2.urlopen(json_link))
        video_logo = video_json[u'data'][0][u'logo']
        video_title = video_json[u'data'][0][u'title']
        youku_tip = self.render_string("tooltip/youku-tip.html", video_id=youku_id, video_logo=video_logo, video_title=video_title)
        self.write(youku_tip)


class GetUserHandler(BaseHandler):
    def get(self, username, template_variables = {}):
        user_info = self.current_user
        view_user = self.user_model.get_user_by_username(username)
        if(view_user==None):
            user_tip = self.render_string("tooltip/user-tip.html", user_info=user_info,  view_user=view_user)
            self.write(user_tip)
            return
        follow_users = self.follow_model.get_user_followers2(view_user.uid)
        if(user_info):
            follow = self.follow_model.get_follow(user_info.uid, view_user.uid, 'u')
        else:
            follow = None
        user_tip = self.render_string("tooltip/user-tip.html", user_info=user_info, follow=follow, view_user=view_user, follow_users=follow_users)
        self.write(user_tip)

class GetTagHandler(BaseHandler):
    def get(self, tagname, template_variables = {}):
        user_info = self.current_user
        view_tag = self.tag_model.get_tag_by_tag_name(tagname)
        follow_users = self.follow_model.get_tag_followers(view_tag.id)
        if(user_info):
            follow = self.follow_model.get_follow(user_info.uid, view_tag.id, 't')
        else:
            follow = None
        tag_tip = self.render_string("tooltip/tag-tip.html", user_info=user_info, follow=follow, view_tag=view_tag, follow_users=follow_users)
        self.write(tag_tip)


class MenuManager:
    accessUrl = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=appid&secret=secret"
    delMenuUrl = "https://api.weixin.qq.com/cgi-bin/menu/delete?access_token="
    createUrl = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token="
    getMenuUri="https://api.weixin.qq.com/cgi-bin/menu/get?access_token="
    def getAccessToken(self):
        f = urllib.request.urlopen(self.accessUrl)
        accessT = f.read().decode("utf-8")
        jsonT = json.loads(accessT)
        return jsonT["access_token"]
    def delMenu(self, accessToken):
        html = urllib.request.urlopen(self.delMenuUrl + accessToken)
        result = json.loads(html.read().decode("utf-8"))
        return result["errcode"]
    def createMenu(self, accessToken):
        menu = '''{
                    "button":[
                        {
                            "type":"click",
                            "name":"今日歌曲",
                            "key":"V1001_TODAY_MUSIC"
                        },
                        {
                            "type":"view",
                            "name":"歌手简介",
                            "url":"http://www.qq.com/"
                        },
                        {
                            "name":"菜单",
                            "sub_button":[
                                {
                                    "type":"click",
                                    "name":"hello word",
                                    "key":"V1001_HELLO_WORLD"
                                },
                                {
                                    "type":"click",
                                    "name":"赞一下我们",
                                    "key":"V1001_GOOD"
                                }
                            ]
                        }
                    ]
                }'''
        html = urllib.request.urlopen(self.createUrl + accessToken, menu.encode("utf-8"))
        result = json.loads(html.read().decode("utf-8"))
        return result["errcode"]
    def getMenu(self):
        html = urllib.request.urlopen(self.getMenuUri + accessToken)
        print(html.read().decode("utf-8"))

# for weixin test
class SDJHandler(BaseHandler):
    def get(self, template_variables = {}):
        #获取微信公众平台发送的验证参数
        signature = self.get_argument('signature', '')
        timestamp = self.get_argument('timestamp', '')
        nonce = self.get_argument('nonce', '')
        echostr = self.get_argument('echostr', '')
        #定义token，需要和Web页面上填写的一致
        token = 'songdaojia'
        #将参数放入列表中，并排序
        list=[token,timestamp,nonce]
        list.sort()
        #加密列表中的参数
        sha1=hashlib.sha1()
        map(sha1.update,list)
        #比较加密结果
        hashcode=sha1.hexdigest()
        if hashcode == signature:
            self.write(echostr)
            wx = MenuManager()
            accessToken = wx.getAccessToken()
            wx.getMenu()
        else:
            self.write('error,code 403')

    def post(self):
        body = self.request.body
        data = ET.fromstring(body)
        tousername = data.find('ToUserName').text
        fromusername = data.find('FromUserName').text
        createtime = data.find('CreateTime').text
        msgtype = data.find('MsgType').text
        content = data.find('Content').text
        msgid = data.find('MsgId').text

        if content.strip() in ('ls','pwd','w','uptime'):
            result = commands.getoutput(content)
        else:
            result = '不可以哦!!!'
        textTpl = """<xml>
                        <ToUserName><![CDATA[%s]]></ToUserName>
                        <FromUserName><![CDATA[%s]]></FromUserName>
                        <CreateTime>%s</CreateTime>
                        <MsgType><![CDATA[%s]]></MsgType>
                        <Content><![CDATA[%s]]></Content>
                    </xml>"""
        out = textTpl % (fromusername, tousername, str(int(time.time())), msgtype, result)
        self.write(out)    