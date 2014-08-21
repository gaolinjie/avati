#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2014 avati

# cat /etc/mime.types
# application/octet-stream    crx

import sys
reload(sys)
sys.setdefaultencoding("utf8")

import os.path
import re
import memcache
import torndb
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

import handler.index
import handler.user

from tornado.options import define, options
from lib.loader import Loader
from lib.session import Session, SessionManager
from jinja2 import Environment, FileSystemLoader

define("port", default = 80, help = "run on the given port", type = int)
define("mysql_host", default = "localhost", help = "community database host")
define("mysql_database", default = "avati", help = "community database name")
define("mysql_user", default = "avati", help = "community database user")
define("mysql_password", default = "avati", help = "community database password")

class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            blog_title = u"avati",
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            root_path = os.path.join(os.path.dirname(__file__), "/"),
            xsrf_cookies = False,
            cookie_secret = "cookie_secret_code",
            login_url = "/login",
            autoescape = None,
            jinja2 = Environment(loader = FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")), trim_blocks = True),
            reserved = ["user", "topic", "home", "setting", "forgot", "login", "logout", "register", "admin"],
            debug=True,
        )

        handlers = [
            (r"/(favicon\.ico)", tornado.web.StaticFileHandler, dict(path = settings["static_path"])),
            (r"/(sitemap.*$)", tornado.web.StaticFileHandler, dict(path = settings["static_path"])),
            (r"/(bdsitemap\.txt)", tornado.web.StaticFileHandler, dict(path = settings["static_path"])),
            (r"/(orca\.txt)", tornado.web.StaticFileHandler, dict(path = settings["static_path"])),

            (r"/", handler.index.IndexHandler),
            (r"/p/(\d+)", handler.index.PostHandler),
            (r"/new", handler.index.NewHandler),
            (r"/t/(.*)", handler.index.TagHandler),   
            (r"/tags", handler.index.TagsHandler),
            (r"/reply/(\d+)", handler.index.ReplyHandler),
            (r"/follow", handler.index.FollowHandler),
            (r"/vote/reply/(\d+)", handler.index.VoteReplyHandler),
            (r"/thank/(\d+)", handler.index.ThankHandler),
            (r"/report/(\d+)", handler.index.ReportHandler),
            (r"/delete/reply/(\d+)", handler.index.DeleteReplyHandler),
            (r"/edit/reply/(\d+)", handler.index.EditReplyHandler),
            (r"/delete/post/(\d+)", handler.index.DeletePostHandler),
            (r"/edit/(\d+)", handler.index.EditHandler),

            (r"/u/(.*)", handler.user.UserHandler),
            (r"/signin", handler.user.SigninHandler),
            (r"/signout", handler.user.SignoutHandler),
            (r"/signup", handler.user.SignupHandler),
            (r"/setting", handler.user.SettingHandler),
            (r"/setting/avatar", handler.user.SettingAvatarHandler),
            (r"/setting/cover", handler.user.SettingCoverHandler),
            (r"/setting/password", handler.user.SettingPasswordHandler),
            (r"/forgot", handler.user.ForgotPasswordHandler),
            (r"/social", handler.user.SocialHandler),
            (r"/notifications", handler.index.NoticeHandler),
            (r"/follows/(.*)", handler.index.FollowsHandler),
            (r"/get/users/(\d+)", handler.index.GetInviteUsersHandler),
            (r"/invite/answer/(\d+)", handler.index.InviteAnswerHandler),
            (r"/invitations", handler.index.InvitationsHandler),
            (r"/invite/email/(\d+)", handler.index.InviteEmailHandler),
            (r"/invite/join", handler.index.InviteJoinHandler),

            (r"/edit/tag/(\d+)", handler.index.EditTagHandler),
            (r"/upload", handler.index.UploadHandler),
            (r"/list", handler.index.ListHandler),
            #(r".*", handler.index.PageNotFoundHandler)
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = torndb.Connection(
            host = options.mysql_host, database = options.mysql_database,
            user = options.mysql_user, password = options.mysql_password
        )

        # Have one global loader for loading models and handles
        self.loader = Loader(self.db)

        # Have one global model for db query
        self.user_model = self.loader.use("user.model")
        self.feed_model = self.loader.use("feed.model")
        self.post_model = self.loader.use("post.model")
        self.reply_model = self.loader.use("reply.model")
        self.feed_type_model = self.loader.use("feed_type.model")
        self.llike_model = self.loader.use("like.model")
        self.vote_model = self.loader.use("vote.model")
        self.post_tag_model = self.loader.use("post_tag.model")
        self.tag_model = self.loader.use("tag.model")
        self.category_model = self.loader.use("category.model")
        self.follow_model = self.loader.use("follow.model")
        self.thank_model = self.loader.use("thank.model")
        self.report_model = self.loader.use("report.model")
        self.notice_model = self.loader.use("notice.model")
        self.invite_model = self.loader.use("invite.model")
        self.tag_type_model = self.loader.use("tag_type.model")
        self.icode_model = self.loader.use("icode.model")

        # Have one global session controller
        self.session_manager = SessionManager(settings["cookie_secret"], ["127.0.0.1:11211"], 0)

        # Have one global memcache controller
        self.mc = memcache.Client(["127.0.0.1:11211"])

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

