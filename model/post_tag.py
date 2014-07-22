#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2013 meiritugua.com

import time
from lib.query import Query

class Post_tagModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "post_tag"
        super(Post_tagModel, self).__init__()

    def add_new_post_tag(self, post_tag_info):
        return self.data(post_tag_info).add()

    def delete_post_tag_by_post_id_and_tag_id(self, post_id, tag_id):
        where = "post_id = %s AND tag_id = %s" % (post_id, tag_id)
        return self.where(where).delete()

    def delete_post_tag_by_post_id(self, post_id):
        where = "post_id = %s" % post_id
        return self.where(where).delete()

    def get_post_all_tags(self, post_id, num = 100, current_page = 1):
        where = "post_tag.post_id = %s" % post_id
        join = "LEFT JOIN tag ON post_tag.tag_id = tag.id"
        order = "post_tag.id ASC"
        field = "post_tag.*, \
                tag.name as tag_name"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)

    def get_tag_all_posts(self, tag_id, num = 10, current_page = 1):
        where = "post_tag.tag_id = %s" % tag_id
        join = "LEFT JOIN post ON post_tag.post_id = post.id\
                LEFT JOIN user AS author_user ON post.author_id = author_user.uid"
        order = "post.created DESC, post.id DESC"
        field = "post.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)