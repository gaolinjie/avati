#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class VoteModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "vote"
        super(VoteModel, self).__init__()

    def get_vote_by_user_and_reply(self, author_id, reply_id):
        where = "author_id = %s AND reply_id = %s" % (author_id, reply_id)
        return self.where(where).find()

    def delete_vote_by_id(self, vote_id):
        where = "vote.id = %s " % vote_id
        return self.where(where).delete()

    def update_vote_by_id(self, vote_id, vote_info):
        where = "vote.id = %s" % vote_id
        return self.where(where).data(vote_info).save()

    def add_new_vote(self, vote_info):
        return self.data(vote_info).add()

