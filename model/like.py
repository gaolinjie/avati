#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class LikeModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "like"
        super(LikeModel, self).__init__()

