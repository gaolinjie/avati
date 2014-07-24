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


    def delete_follow_by_id(self, follow_id):
        where = "id = %s " % follow_id
        return self.where(where).delete()

    def get_user_all_follow_feeds(self, author_id, num = 10, current_page = 1):
        where = "follow.author_id = %s" % author_id
        join = "RIGHT JOIN feed ON (follow.obj_type = 'u' AND follow.obj_id = feed.user_id) OR (follow.obj_type = 'q' AND follow.obj_id = feed.post_id)\
                LEFT JOIN user AS author_user ON post.author_id = author_user.uid \
                LEFT JOIN channel ON post.channel_id = channel.id \
                LEFT JOIN video ON post.video_id = video.id \
                LEFT JOIN nav ON channel.nav_id = nav.id \
                LEFT JOIN comment ON post.last_comment = comment.id \
                LEFT JOIN user AS comment_user ON comment.author_id = comment_user.uid \
                LEFT JOIN favorite ON '%s' = favorite.user_id AND post.id = favorite.post_id \
                LEFT JOIN later ON '%s' = later.user_id AND post.id = later.post_id" % (user_id, user_id)
        order = "post.created DESC, post.id DESC"
        field = "post.*, \
                author_user.username as author_username, \
                author_user.avatar as author_avatar, \
                channel.id as channel_id, \
                channel.name as channel_name, \
                nav.name as nav_name, \
                nav.title as nav_title, \
                video.source as video_source, \
                video.flash as video_flash, \
                video.title as video_title, \
                video.thumb as video_thumb, \
                video.link as video_link, \
                comment.content as comment_content, \
                comment.created as comment_created, \
                comment_user.username as comment_user_name, \
                comment_user.avatar as comment_user_avatar, \
                favorite.id as favorite_id, \
                later.id as later_id"
        return self.where(where).order(order).join(join).field(field).pages(current_page = current_page, list_rows = num)