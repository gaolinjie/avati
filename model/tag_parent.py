#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class Tag_parentModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "tag_parent"
        super(Tag_parentModel, self).__init__()

    def add_new_tag_parent(self, tag_parent_info):
        return self.data(tag_parent_info).add()


