#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class IcodeModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "icode"
        super(IcodeModel, self).__init__()


    def get_invite_code(self, code):
        where = "code = '%s'" % code
        return self.where(where).find()

    def delete_code_by_id(self, icode_id):
        where = "id = %s " % icode_id
        return self.where(where).delete()


