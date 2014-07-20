#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class Post_tagModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "post_tag"
        super(Post_tagModel, self).__init__()