from lib.query import Query

class FollowModel(Query):
    def __init__(self, db):
        self.db = db
        self.table_name = "follow"
        super(FollowModel, self).__init__()

    def add_new_follow(self, follow_info):
        return self.data(follow_info).add()

    def get_follow(self, author_id, obj_id, obj_type):
        where = "author_id = %s AND obj_id = %s AND obj_type = %s" % (author_id, obj_id, obj_type)
        return self.where(where).find()


    def delete_follow_by_id(self, follow_id):
        where = "id = %s " % follow_id
        return self.where(where).delete()