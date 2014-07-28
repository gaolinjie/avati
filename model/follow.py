from lib.query import Query

class FollowModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "follow"
        super(FollowModel, self).__init__()

    def add_new_follow(self, follow_info):
        return self.data(follow_info).add()

    def get_follow(self, author_id, obj_id, obj_type):
        where = "author_id = %s AND obj_id = %s AND obj_type = '%s'" % (author_id, obj_id, obj_type)
        return self.where(where).find()

    def get_post_all_follows(self, obj_id):
        where = "obj_id = %s AND (obj_type = 'p' OR obj_type = 'q')" % obj_id
        return self.where(where).select()


    def delete_follow_by_id(self, follow_id):
        where = "follow.id = %s " % follow_id
        return self.where(where).delete()

    def get_user_all_follow_feeds(self, author_id, num = 10, current_page = 1):
        where = "follow.author_id = %s" % author_id
        join = "RIGHT JOIN feed ON (follow.obj_type = 'u' AND follow.obj_id = feed.user_id) OR ((follow.obj_type = 'q' OR follow.obj_type = 'p') AND follow.obj_id = feed.post_id AND (feed.feed_type = 2 OR  feed.feed_type = 8)) OR (follow.obj_type = 't' AND follow.obj_id = feed.tag_id)\
                LEFT JOIN user AS author_user ON feed.user_id = author_user.uid \
                LEFT JOIN tag ON feed.tag_id = tag.id \
                LEFT JOIN post ON feed.post_id = post.id \
                LEFT JOIN user AS post_user ON post.author_id = post_user.uid \
                LEFT JOIN reply ON feed.reply_id = reply.id \
                LEFT JOIN user AS reply_user ON reply.author_id = reply_user.uid\
                LEFT JOIN feed_type ON feed.feed_type = feed_type.id\
                LEFT JOIN follow AS post_follow ON post_follow.author_id = %s AND post.id = post_follow.obj_id AND (post_follow.obj_type='q' OR post_follow.obj_type='p')" % author_id
        order = "feed.created DESC, feed.id DESC"
        field = "feed.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                tag.name as tag_name, \
                tag.thumb as tag_thumb, \
                post.id as post_id, \
                post.title as post_title, \
                post.content as post_content, \
                post.post_type as post_type, \
                post.thumb as post_thumb, \
                post.reply_num as post_reply_num, \
                post.created as post_created, \
                reply.id as reply_id, \
                reply.content as reply_content,\
                feed_type.feed_text as feed_text, \
                reply_user.username as reply_user_username, \
                reply_user.sign as reply_user_sign, \
                post_follow.id as post_follow_id"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)