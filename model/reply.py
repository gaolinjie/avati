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

    def get_post_all_replys(self, post_id, user_id, num = 16, current_page = 1):
        where = "post_id = %s" % post_id
        join = "LEFT JOIN user ON reply.author_id = user.uid \
                LEFT JOIN vote ON vote.author_id = %s AND reply.id = vote.reply_id" % user_id
        order = "id ASC"
        field = "reply.*, \
                user.username as author_username, \
                user.sign as author_sign, \
                user.avatar as author_avatar, \
                vote.up_down as vote_up_down"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)

    def get_reply_by_id(self, reply_id):
        where = "reply.id = %s" % reply_id
        return self.where(where).find()

    def update_reply_by_id(self, reply_id, reply_info):
        where = "reply.id = %s" % reply_id
        return self.where(where).data(reply_info).save()