#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class AgreeModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "agree"
        super(AgreeModel, self).__init__()


