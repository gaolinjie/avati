#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class InviteModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "invite"
        super(InviteModel, self).__init__()

    def delete_invite_by_id(self, invite_id):
        where = "invite.id = %s " % invite_id
        return self.where(where).delete()

    def delete_invite_by_post_id(self, post_id):
        where = "invite.post_id = %s" % post_id
        return self.where(where).delete()


    def add_new_invite(self, invite_info):
        return self.data(invite_info).add()

    def get_invite(self, from_user, to_user, post_id):
        where = "from_user = %s AND to_user = %s AND post_id = %s" % (from_user, to_user, post_id)
        return self.where(where).find()



