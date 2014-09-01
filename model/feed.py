#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class FeedModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "feed"
        super(FeedModel, self).__init__()

    def add_new_feed(self, feed_info):
        return self.data(feed_info).add()

    def get_feed_user_vote_reply_feed(self, user_id, reply_id):
        where = "user_id = %s AND reply_id = %s AND (feed_type = 5 OR feed_type = 11)" % (user_id, reply_id)
        return self.where(where).find()

    def get_feed_user_vote_post_feed(self, user_id, post_id):
        where = "user_id = %s AND post_id = %s AND (feed_type = 13 OR feed_type = 15)" % (user_id, post_id)
        return self.where(where).find()

    def delete_feed_by_id(self, feed_id):
        where = "feed.id = %s " % feed_id
        return self.where(where).delete()

    def delete_feed_by_post_id(self, post_id):
        where = "feed.post_id = %s " % post_id
        return self.where(where).delete()

    def delete_feed_by_reply_id(self, reply_id):
        where = "feed.reply_id = %s " % reply_id
        return self.where(where).delete()

    def delete_feed_by_reply_and_type(self, reply_id, feed_type):
    	where = "feed.reply_id = %s AND feed.feed_type = %s" % (reply_id, feed_type)
        return self.where(where).delete()

    def delete_feed_by_post_and_type(self, post_id, feed_type):
        where = "feed.post_id = %s AND feed.feed_type = %s" % (post_id, feed_type)
        return self.where(where).delete()

    def delete_feed_by_user_post__and_type(self, user_id, post_id,  feed_type):
        where = "feed.user_id = %s AND feed.post_id = %s AND feed.feed_type = %s" % (user_id, post_id, feed_type)
        return self.where(where).delete()

    def delete_feed_by_post_and_type(self, post_id, feed_type):
        where = "feed.post_id = %s AND feed.feed_type = %s" % (post_id, feed_type)
        return self.where(where).delete()

    def get_user_all_feeds(self, author_id,  user_id, num = 10, current_page = 1):
        where = "feed.user_id = %s" % author_id
        join = "LEFT JOIN user AS author_user ON feed.user_id = author_user.uid \
                LEFT JOIN tag ON feed.tag_id = tag.id \
                LEFT JOIN post ON feed.post_id = post.id \
                LEFT JOIN user AS post_user ON post.author_id = post_user.uid \
                LEFT JOIN reply ON feed.reply_id = reply.id \
                LEFT JOIN user AS reply_user ON reply.author_id = reply_user.uid\
                LEFT JOIN feed_type ON feed.feed_type = feed_type.id\
                LEFT JOIN follow AS post_follow ON post_follow.author_id = %s AND post.id = post_follow.obj_id AND (post_follow.obj_type='q' OR post_follow.obj_type='p')\
                LEFT JOIN thank AS post_thank ON post_thank.from_user = %s AND post_thank.to_user = post.author_id AND post_thank.obj_id = post.id AND post_thank.obj_type = 'post'\
                LEFT JOIN report AS post_report ON post_report.from_user = %s AND post_report.to_user = post.author_id AND post_report.obj_id = post.id AND post_report.obj_type = 'post'\
                LEFT JOIN thank AS reply_thank ON reply_thank.from_user = %s AND reply_thank.to_user = reply.author_id AND reply_thank.obj_id = reply.id AND reply_thank.obj_type = 'reply'\
                LEFT JOIN report AS reply_report ON reply_report.from_user = %s AND reply_report.to_user = reply.author_id AND reply_report.obj_id = reply.id AND reply_report.obj_type = 'reply'" % (user_id, user_id, user_id, user_id, user_id)
        order = "feed.created DESC, feed.id DESC"
        field = "feed.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                tag.name as tag_name, \
                tag.thumb as tag_thumb, \
                post.id as post_id, \
                post.title as post_title, \
                post.content as post_content, \
                post.post_type as post_type, \
                post.thumb as post_thumb, \
                post.reply_num as post_reply_num, \
                post.created as post_created, \
                post_user.username as post_user_username, \
                reply.id as reply_id, \
                reply.content as reply_content,\
                feed_type.feed_text as feed_text, \
                reply_user.username as reply_user_username, \
                reply_user.sign as reply_user_sign, \
                post_follow.id as post_follow_id, \
                post_thank.id as post_thank_id, \
                post_report.id as post_report_id, \
                reply_thank.id as reply_thank_id, \
                reply_report.id as reply_report_id"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)

    def get_user_all_feeds2(self, author_id, num = 10, current_page = 1):
        where = "feed.user_id = %s" % author_id
        join = "LEFT JOIN user AS author_user ON feed.user_id = author_user.uid \
                LEFT JOIN tag ON feed.tag_id = tag.id \
                LEFT JOIN post ON feed.post_id = post.id \
                LEFT JOIN user AS post_user ON post.author_id = post_user.uid \
                LEFT JOIN reply ON feed.reply_id = reply.id \
                LEFT JOIN user AS reply_user ON reply.author_id = reply_user.uid\
                LEFT JOIN feed_type ON feed.feed_type = feed_type.id"
        order = "feed.created DESC, feed.id DESC"
        field = "feed.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                tag.name as tag_name, \
                tag.thumb as tag_thumb, \
                post.id as post_id, \
                post.title as post_title, \
                post.content as post_content, \
                post.post_type as post_type, \
                post.thumb as post_thumb, \
                post.reply_num as post_reply_num, \
                post.created as post_created, \
                post_user.username as post_user_username, \
                reply.id as reply_id, \
                reply.content as reply_content,\
                feed_type.feed_text as feed_text, \
                reply_user.username as reply_user_username, \
                reply_user.sign as reply_user_sign"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)

    def get_user_all_feeds_by_type(self, author_id, user_id, feed_type, num = 10, current_page = 1):
        where = "feed.user_id = %s AND feed.feed_type = %s" % (author_id, feed_type)
        join = "LEFT JOIN user AS author_user ON feed.user_id = author_user.uid \
                LEFT JOIN tag ON feed.tag_id = tag.id \
                LEFT JOIN post ON feed.post_id = post.id \
                LEFT JOIN user AS post_user ON post.author_id = post_user.uid \
                LEFT JOIN reply ON feed.reply_id = reply.id \
                LEFT JOIN user AS reply_user ON reply.author_id = reply_user.uid\
                LEFT JOIN feed_type ON feed.feed_type = feed_type.id\
                LEFT JOIN follow AS post_follow ON post_follow.author_id = %s AND post.id = post_follow.obj_id AND (post_follow.obj_type='q' OR post_follow.obj_type='p')\
                LEFT JOIN thank AS post_thank ON post_thank.from_user = %s AND post_thank.to_user = post.author_id AND post_thank.obj_id = post.id AND post_thank.obj_type = 'post'\
                LEFT JOIN report AS post_report ON post_report.from_user = %s AND post_report.to_user = post.author_id AND post_report.obj_id = post.id AND post_report.obj_type = 'post'\
                LEFT JOIN thank AS reply_thank ON reply_thank.from_user = %s AND reply_thank.to_user = reply.author_id AND reply_thank.obj_id = reply.id AND reply_thank.obj_type = 'reply'\
                LEFT JOIN report AS reply_report ON reply_report.from_user = %s AND reply_report.to_user = reply.author_id AND reply_report.obj_id = reply.id AND reply_report.obj_type = 'reply'" % (user_id, user_id, user_id, user_id, user_id)
        order = "feed.created DESC, feed.id DESC"
        field = "feed.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                tag.name as tag_name, \
                tag.thumb as tag_thumb, \
                post.id as post_id, \
                post.title as post_title, \
                post.content as post_content, \
                post.post_type as post_type, \
                post.thumb as post_thumb, \
                post.reply_num as post_reply_num, \
                post.created as post_created, \
                post_user.username as post_user_username, \
                reply.id as reply_id, \
                reply.content as reply_content,\
                feed_type.feed_text as feed_text, \
                reply_user.username as reply_user_username, \
                reply_user.sign as reply_user_sign, \
                post_follow.id as post_follow_id, \
                post_thank.id as post_thank_id, \
                post_report.id as post_report_id, \
                reply_thank.id as reply_thank_id, \
                reply_report.id as reply_report_id"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)

    def get_user_all_feeds_by_type2(self, author_id, feed_type, num = 10, current_page = 1):
        where = "feed.user_id = %s AND feed.feed_type = %s" % (author_id, feed_type)
        join = "LEFT JOIN user AS author_user ON feed.user_id = author_user.uid \
                LEFT JOIN tag ON feed.tag_id = tag.id \
                LEFT JOIN post ON feed.post_id = post.id \
                LEFT JOIN user AS post_user ON post.author_id = post_user.uid \
                LEFT JOIN reply ON feed.reply_id = reply.id \
                LEFT JOIN user AS reply_user ON reply.author_id = reply_user.uid\
                LEFT JOIN feed_type ON feed.feed_type = feed_type.id"
        order = "feed.created DESC, feed.id DESC"
        field = "feed.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                tag.name as tag_name, \
                tag.thumb as tag_thumb, \
                post.id as post_id, \
                post.title as post_title, \
                post.content as post_content, \
                post.post_type as post_type, \
                post.thumb as post_thumb, \
                post.reply_num as post_reply_num, \
                post.created as post_created, \
                post_user.username as post_user_username, \
                reply.id as reply_id, \
                reply.content as reply_content,\
                feed_type.feed_text as feed_text, \
                reply_user.username as reply_user_username, \
                reply_user.sign as reply_user_sign"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)

    def get_user_all_feeds_count_by_type(self, author_id, feed_type):
        where = "feed.user_id = %s AND feed.feed_type = %s" % (author_id, feed_type)
        return self.where(where).count()


    def get_default_feeds(self, num = 10, current_page = 1):
        where = "feed.feed_type = 1 OR feed.feed_type = 4 OR  feed.feed_type = 6 OR feed.feed_type = 7 OR feed.feed_type = 10 OR feed.feed_type = 12 OR feed.feed_type = 14 OR feed.feed_type = 16" 
        join = "LEFT JOIN user AS author_user ON feed.user_id = author_user.uid \
                LEFT JOIN tag ON feed.tag_id = tag.id \
                LEFT JOIN post ON feed.post_id = post.id \
                LEFT JOIN user AS post_user ON post.author_id = post_user.uid \
                LEFT JOIN reply ON feed.reply_id = reply.id \
                LEFT JOIN user AS reply_user ON reply.author_id = reply_user.uid\
                LEFT JOIN feed_type ON feed.feed_type = feed_type.id"
        order = "feed.created DESC, feed.id DESC"
        field = "feed.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                tag.name as tag_name, \
                tag.thumb as tag_thumb, \
                post.id as post_id, \
                post.title as post_title, \
                post.content as post_content, \
                post.post_type as post_type, \
                post.thumb as post_thumb, \
                post.reply_num as post_reply_num, \
                post.created as post_created, \
                post_user.username as post_user_username, \
                reply.id as reply_id, \
                reply.content as reply_content,\
                feed_type.feed_text as feed_text, \
                reply_user.username as reply_user_username, \
                reply_user.sign as reply_user_sign"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)



