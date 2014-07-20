#!/usr/bin/env python
# coding=utf-8
#
# Copyright 2014 avati

import uuid
import hashlib
import Image
import StringIO
import time
import json
import re
import urllib2
import tornado.web
import lib.jsonp
import pprint
import math
import datetime 

from base import *
from lib.variables import *
from lib.variables import gen_random
from lib.xss import XssCleaner
from lib.utils import find_mentions
from lib.reddit import hot
from lib.utils import pretty_date

from lib.mobile import is_mobile_browser

class IndexHandler(BaseHandler):
    def get(self, template_variables = {}):
        self.render("index.html", **template_variables)

class PostHandler(BaseHandler):
    def get(self, template_variables = {}):
        self.render("post.html", **template_variables)

class NewHandler(BaseHandler):
    def get(self, template_variables = {}):
        self.render("new.html", **template_variables)

class TagHandler(BaseHandler):
    def get(self, template_variables = {}):
        self.render("tag.html", **template_variables)

class TagsHandler(BaseHandler):
    def get(self, template_variables = {}):
        self.render("tags.html", **template_variables)