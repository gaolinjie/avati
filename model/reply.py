#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class ReplyModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "reply"
        super(ReplyModel, self).__init__()


    def add_new_reply(self, reply_info):
        return self.data(reply_info).add()

    def get_post_all_replys(self, post_id, num = 16, current_page = 1):
        where = "post_id = %s" % post_id
        join = "LEFT JOIN user ON reply.author_id = user.uid"
        order = "id ASC"
        field = "reply.*, \
                user.username as author_username, \
                user.sign as author_sign, \
                user.avatar as author_avatar"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)