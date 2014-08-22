#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 mifan.tv

from lib.query import Query

class PostModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "post"
        super(PostModel, self).__init__()

    def add_new_post(self, post_info):
        return self.data(post_info).add()

    def get_post_by_post_id2(self, post_id, user_id):
        where = "post.id = %s" % post_id
        join = "LEFT JOIN user AS author_user ON post.author_id = author_user.uid\
                LEFT JOIN vote ON vote.author_id = %s AND post.id = vote.post_id" % user_id
        field = "post.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                author_user.sign as author_sign, \
                vote.up_down as vote_up_down"
        return self.where(where).join(join).field(field).find()

    def get_post_by_post_id(self, post_id):
        where = "post.id = %s" % post_id
        join = "LEFT JOIN user AS author_user ON post.author_id = author_user.uid"
        field = "post.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                author_user.sign as author_sign"
        return self.where(where).join(join).field(field).find()

    def update_post_by_post_id(self, post_id, post_info):
        where = "post.id = %s" % post_id
        return self.where(where).data(post_info).save()

    def delete_post_by_post_id(self, post_id):
        where = "post.id = %s" % post_id
        return self.where(where).delete()