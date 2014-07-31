#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class ThankModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "thank"
        super(ThankModel, self).__init__()

    def delete_thank_by_id(self, thank_id):
        where = "thank.id = %s " % thank_id
        return self.where(where).delete()

    def add_new_thank(self, thank_info):
        return self.data(thank_info).add()

    def get_thank(self, from_user, to_user, obj_id, obj_type):
        where = "from_user = %s AND to_user = %s AND obj_id = %s AND obj_type = '%s'" % (from_user, to_user, obj_id, obj_type)
        return self.where(where).find()



