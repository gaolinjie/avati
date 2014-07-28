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

THRESHOLD = 2
class IndexHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
            template_variables["related_posts"] = self.follow_model.get_user_follow_hot_posts(user_info.uid)
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
            template_variables["related_posts"] = self.post_tag_model.get_post_related_posts(post_id)
            template_variables["tags"] = self.post_tag_model.get_post_all_tags(post_id)
            replys = self.reply_model.get_post_all_replys(post_id, user_info.uid)
            template_variables["replys"] = replys
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, post_id, post.post_type)
            for reply in replys["list"]:
                template_variables["votes"+str(reply.id)] = self.vote_model.get_reply_all_up_votes(reply.id)

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

        if post_type == 'q':
            feed_type = 1
        else:
            feed_type = 7

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

            if post.post_type == 'q':
                feed_type = 2
            else:
                feed_type = 8
            # add feed: user 回答了问题
            feed_info = {
                "user_id": self.current_user["uid"],           
                "post_id": post.id,
                "reply_id": reply_id,
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

                    follows = self.follow_model.get_post_all_follows(obj_id)
                    if len(follows) <= THRESHOLD:
                        if obj_type == 'q':
                            feed_type = 4
                        else:
                            feed_type = 10
                        self.feed_model.delete_feed_by_post_and_type(obj_id, feed_type)
            else:
                follow_info = {
                    "author_id": user_info["uid"],
                    "obj_id": obj_id,
                    "obj_type": obj_type,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.follow_model.add_new_follow(follow_info)

                if obj_type=='q' or obj_type=='p':
                    if obj_type == 'q':
                        feed_type = 3
                    else:
                        feed_type = 9
                    # add feed: user 关注了问题
                    feed_info = {
                        "user_id": user_info["uid"],           
                        "post_id": obj_id,
                        "feed_type": feed_type,
                        "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    self.feed_model.add_new_feed(feed_info)

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

class VoteHandler(BaseHandler):
    def get(self, reply_id, template_variables = {}):
        user_info = self.current_user
        vote_type = self.get_argument('vote', "null")

        if(user_info):
            reply = self.reply_model.get_reply_by_id(reply_id)
            vote = self.vote_model.get_vote_by_user_and_reply(user_info.uid, reply_id)
            post = self.post_model.get_post_by_post_id(reply.post_id)
            if post.post_type == 'q':
                feed_type = 5;
            else:
                feed_type = 11;

            if vote:
                if vote_type==vote.up_down:
                    self.vote_model.delete_vote_by_id(vote.id)
                    if vote.up_down=='up':
                        self.reply_model.update_reply_by_id(reply.id, {"up_num": reply.up_num-1})
                        feed = self.feed_model.get_feed_user_vote_feed(user_info.uid, reply.id)
                        if feed:
                            self.feed_model.delete_feed_by_id(feed.id)

                        if reply.up_num-1 <= THRESHOLD:
                            if post.post_type == 'q':
                                feed_type2 = 6;
                            else:
                                feed_type2 = 12;
                            self.feed_model.delete_feed_by_reply_and_type(reply_id, feed_type2)

                    else:
                        self.reply_model.update_reply_by_id(reply.id, {"down_num": reply.down_num-1})
                else:
                    if vote.up_down=='up':
                        self.reply_model.update_reply_by_id(reply.id, {"up_num": reply.up_num-1, "down_num": reply.down_num+1})
                        feed = self.feed_model.get_feed_user_vote_feed(user_info.uid, reply.id)
                        if feed:
                            self.feed_model.delete_feed_by_id(feed.id)

                        if reply.up_num-1 <= THRESHOLD:
                            if post.post_type == 'q':
                                feed_type2 = 6;
                            else:
                                feed_type2 = 12;
                            self.feed_model.delete_feed_by_reply_and_type(reply_id, feed_type2)
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
                else:
                    self.reply_model.update_reply_by_id(reply.id, {"down_num": reply.down_num+1})
            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))