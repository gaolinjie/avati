#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 meiritugua.com

import time
from lib.query import Query

class TagModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "tag"
        super(TagModel, self).__init__()

    def get_all_tags(self):
        return self.select()

    def get_tag_by_tag_name(self, tag_name):
    	where = "name = '%s'" % tag_name
        return self.where(where).find()
    
    def add_new_tag(self, tag_info):
        return self.data(tag_info).add()

    def update_tag_by_tag_id(self, tag_id, tag_info):
        where = "tag.id = %s" % tag_id
        return self.where(where).data(tag_info).save()

    def get_tag_all_feeds(self, tag_id, author_id, num = 10, current_page = 1):
        where = "tag.id = %s" % tag_id
        join = "LEFT JOIN post_tag ON tag.id = post_tag.tag_id \
                RIGHT JOIN feed ON post_tag.post_id = feed.post_id AND feed.feed_type!=3 AND feed.feed_type!=5 AND feed.feed_type!=9 AND feed.feed_type!=11 \
                LEFT JOIN user AS author_user ON feed.user_id = author_user.uid \
                LEFT JOIN tag AS feed_tag ON feed.tag_id = tag.id \
                LEFT JOIN post ON feed.post_id = post.id \
                LEFT JOIN user AS post_user ON post.author_id = post_user.uid \
                LEFT JOIN reply ON feed.reply_id = reply.id \
                LEFT JOIN user AS reply_user ON reply.author_id = reply_user.uid\
                LEFT JOIN feed_type ON feed.feed_type = feed_type.id\
                LEFT JOIN follow AS post_follow ON post_follow.author_id = %s AND post.id = post_follow.obj_id AND (post_follow.obj_type='q' OR post_follow.obj_type='p')" % author_id
        order = "feed.created DESC, feed.id DESC"
        field = "feed.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                feed_tag.name as tag_name, \
                feed_tag.thumb as tag_thumb, \
                post.id as post_id, \
                post.title as post_title, \
                post.content as post_content, \
                post.post_type as post_type, \
                post.thumb as post_thumb, \
                post.reply_num as post_reply_num, \
                post.created as post_created, \
                reply.id as reply_id, \
                reply.content as reply_content,\
                feed_type.feed_text as feed_text, \
                reply_user.username as reply_user_username, \
                reply_user.sign as reply_user_sign, \
                post_follow.id as post_follow_id"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)

    def get_tag_all_feeds_by_type(self, tag_id, author_id, feed_type, num = 10, current_page = 1):
        where = "tag.id = %s" % tag_id
        join = "LEFT JOIN post_tag ON tag.id = post_tag.tag_id \
                RIGHT JOIN feed ON post_tag.post_id = feed.post_id AND feed.feed_type= %s \
                LEFT JOIN user AS author_user ON feed.user_id = author_user.uid \
                LEFT JOIN tag AS feed_tag ON feed.tag_id = tag.id \
                LEFT JOIN post ON feed.post_id = post.id \
                LEFT JOIN user AS post_user ON post.author_id = post_user.uid \
                LEFT JOIN reply ON feed.reply_id = reply.id \
                LEFT JOIN user AS reply_user ON reply.author_id = reply_user.uid\
                LEFT JOIN feed_type ON feed.feed_type = feed_type.id\
                LEFT JOIN follow AS post_follow ON post_follow.author_id = %s AND post.id = post_follow.obj_id AND (post_follow.obj_type='q' OR post_follow.obj_type='p')" % (feed_type, author_id)
        order = "feed.created DESC, feed.id DESC"
        field = "feed.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                feed_tag.name as tag_name, \
                feed_tag.thumb as tag_thumb, \
                post.id as post_id, \
                post.title as post_title, \
                post.content as post_content, \
                post.post_type as post_type, \
                post.thumb as post_thumb, \
                post.reply_num as post_reply_num, \
                post.created as post_created, \
                reply.id as reply_id, \
                reply.content as reply_content,\
                feed_type.feed_text as feed_text, \
                reply_user.username as reply_user_username, \
                reply_user.sign as reply_user_sign, \
                post_follow.id as post_follow_id"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)