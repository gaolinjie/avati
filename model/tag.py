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