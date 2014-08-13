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
from lib.sendmail import send
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
        template_variables["gen_random"] = gen_random
        p = int(self.get_argument("p", "1"))
        print p
        if(user_info):
            template_variables["related_posts"] = self.follow_model.get_user_follow_hot_posts(user_info.uid)
            template_variables["feeds"] = self.follow_model.get_user_all_follow_feeds(user_info.uid, current_page = p)
            self.render("index.html", **template_variables)
        else:
            self.redirect("/signin")

class PostHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        template_variables["gen_random"] = gen_random
        sort = self.get_argument('sort', "voted")
        p = int(self.get_argument("p", "1"))

        if(user_info):
            post = self.post_model.get_post_by_post_id(post_id)
            template_variables["post"] = post
            self.post_model.update_post_by_post_id(post.id, {"view_num": post.view_num+1})
            template_variables["related_posts"] = self.post_tag_model.get_post_related_posts(post_id)
            template_variables["tags"] = self.post_tag_model.get_post_all_tags(post_id)
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

            self.render("post.html", **template_variables)
        else:
            self.redirect("/signin")

class NewHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        if(user_info):
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
            self.render("new.html", **template_variables)
        else:
            self.redirect("/signin")

    @tornado.web.authenticated
    def post(self, template_variables = {}):
        user_info = self.current_user
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

            # update user_info
            self.user_model.update_user_info_by_user_id(user_info.uid, {"questions": user_info.questions+1})
        else:
            feed_type = 7
            notice_type = 13

            # update user_info
            self.user_model.update_user_info_by_user_id(user_info.uid, {"posts": user_info.posts+1})

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
            self.render("edit.html", **template_variables)
        else:
            self.redirect("/signin")

    @tornado.web.authenticated
    def post(self, post_id, template_variables = {}):
        template_variables = {}

        post_type = self.get_argument('t', "q")

        # validate the fields
        form = NewForm(self)

        if not form.validate():
            self.get({"errors": form.errors})
            return

        post_info = {          
            "title": form.title.data,
            "content": form.content.data,
            "updated": time.strftime('%Y-%m-%d %H:%M:%S'),

        }

        self.post_model.update_post_by_post_id(post_id, post_info)
        self.redirect("/p/"+str(post_id))

        tags = self.post_tag_model.get_post_all_tags(post_id)
        for tag in tags["list"]:
                self.tag_model.update_tag_by_tag_id(tag.tag_id, {"post_num": tag.tag_post_num-1})
        self.post_tag_model.delete_post_tag_by_post_id(post_id)
        # process tags
        tagStr = form.tag.data
        if tagStr:
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
        p = int(self.get_argument("p", "1"))
        if(user_info):
            tag = self.tag_model.get_tag_by_tag_name(tag_name)
            template_variables["tag"] = tag
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, tag.id, 't')
            template_variables["feeds"] = self.tag_model.get_tag_all_feeds(tag.id, user_info.uid, current_page = p)
            template_variables["feeds1"] = self.tag_model.get_tag_all_feeds_by_type(tag.id, user_info.uid, 1, current_page = p)
            template_variables["feeds7"] = self.tag_model.get_tag_all_feeds_by_type(tag.id, user_info.uid, 7, current_page = p)
            template_variables["feeds1_len"] = self.tag_model.get_tag_all_feeds_count_by_type(tag.id, user_info.uid, 1)
            template_variables["feeds7_len"] = self.tag_model.get_tag_all_feeds_count_by_type(tag.id, user_info.uid, 7)
            template_variables["follow_num"] = self.follow_model.get_tag_followers_count(tag.id)
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
            self.post_model.update_post_by_post_id(post_id, {"reply_num": post.reply_num+1,})

            if post.post_type == 'q':
                feed_type = 2
                notice_type = 1
                notice_type2 = 7
                # update user_info
                self.user_model.update_user_info_by_user_id(user_info.uid, {"answers": user_info.answers+1})
            else:
                feed_type = 8
                notice_type = 8
                notice_type2 = 14
                # update user_info
                self.user_model.update_user_info_by_user_id(user_info.uid, {"comments": user_info.comments+1})
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
            else:
                follow_info = {
                    "author_id": user_info["uid"],
                    "obj_id": obj_id,
                    "obj_type": obj_type,
                    "created": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.follow_model.add_new_follow(follow_info)

                if obj_type=='u':
                    # add notice: user 关注了你
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
                else:
                    self.reply_model.update_reply_by_id(reply.id, {"down_num": reply.down_num+1})
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
                        "reputation": to_user.reputation+2,
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
                        "reputation": to_user.reputation+1,
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
                        "reputation": to_user.reputation-1,
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
                        "reputation": to_user.reputation-1,
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

class DeletePostHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user

        if(user_info):
            self.post_model.delete_post_by_post_id(post_id)
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
            template_variables["notices"] = self.notice_model.get_user_all_notices(user_info.uid, current_page = p)
            self.render("notice.html", **template_variables)
        else:
            self.redirect("/signin")

class FollowsHandler(BaseHandler):
    def get(self, username, template_variables = {}):
        user_info = self.current_user
        template_variables["user_info"] = user_info
        p = int(self.get_argument("p", "1"))
        active_tab = self.get_argument('tab', "question")

        if(user_info):
            template_variables["active_tab"] = active_tab
            view_user = self.user_model.get_user_by_username(username)
            template_variables["view_user"] = view_user
            template_variables["follow"] = self.follow_model.get_follow(user_info.uid, view_user.uid, 'u')

            template_variables["feeds1"] = self.follow_model.get_user_follow_questions(view_user.uid, current_page = p)
            template_variables["feeds2"] = self.follow_model.get_user_follow_posts(view_user.uid, current_page = p)
            template_variables["feeds3"] = self.follow_model.get_user_followees(view_user.uid, user_info.uid, current_page = p)
            template_variables["feeds4"] = self.follow_model.get_user_followers(view_user.uid, user_info.uid, current_page = p)


            self.render("follows.html", **template_variables)
        else:
            self.redirect("/login")

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
                    user.avatar = "http://avati-avatar.qiniudn.com/b_default.png-avatar"
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

class InviteAnswerHandler(BaseHandler):
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
            self.render("invitations.html", **template_variables)
        else:
            self.redirect("/login")

class InviteEmailHandler(BaseHandler):
    def get(self, post_id, template_variables = {}):
        user_info = self.current_user
        email = self.get_argument('email', "null")
        print email

        if(user_info):
            # send invite to answer mail to user
            mail_title = u"邀请回答"
            mail_content = self.render_string("invite-answer.html")
            send(mail_title, mail_content, email)

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))

class InviteJoinHandler(BaseHandler):
    def get(self, template_variables = {}):
        user_info = self.current_user
        email = self.get_argument('email', "null")

        if(user_info):
            # send invite to answer mail to user
            mail_title = u"邀请回答"
            mail_content = self.render_string("invite-answer.html")
            send(mail_title, mail_content, email)

            self.write(lib.jsonp.print_JSON({
                    "success": 1,
                }))
        else:
            self.write(lib.jsonp.print_JSON({
                    "success": 0,
                }))