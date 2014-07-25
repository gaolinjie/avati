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



