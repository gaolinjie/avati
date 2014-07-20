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
            (r"/post", handler.index.PostHandler),
            (r"/new", handler.index.NewHandler),
            (r"/tag", handler.index.TagHandler),   
            (r"/tags", handler.index.TagsHandler),

            (r"/user", handler.user.UserHandler),
            (r"/signin", handler.user.SigninHandler),
            (r"/signout", handler.user.SignoutHandler),
            (r"/signup", handler.user.SignupHandler),
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
        self.channel_model = self.loader.use("reply.model")
        self.plus_model = self.loader.use("feed_type.model")
        self.comment_model = self.loader.use("like.model")
        self.nav_model = self.loader.use("agree.model")
        self.subnav_model = self.loader.use("post_tag.model")
        self.video_model = self.loader.use("tag.model")
        self.favorite_model = self.loader.use("category.model")

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

