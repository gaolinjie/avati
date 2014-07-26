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

    def get_feed_user_vote_feed(self, user_id, reply_id):
        where = "user_id = %s AND reply_id = %s AND (feed_type = 5 OR feed_type = 11)" % (user_id, reply_id)
        return self.where(where).find()

    def delete_feed_by_id(self, feed_id):
        where = "feed.id = %s " % feed_id
        return self.where(where).delete()

    def delete_feed_by_reply_and_type(self, reply_id, feed_type):
    	where = "feed.reply_id = %s AND feed.feed_type = %s" % (reply_id, feed_type)
        return self.where(where).delete()



