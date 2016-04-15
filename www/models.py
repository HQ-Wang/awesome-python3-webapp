#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file: models.py
@time: 2016/4/15 11:31
"""
__author__ = 'Hongqing Wang'

import time
import uuid

from orm import Model, StringField, BooleanField, FloatField, TextField

def next_id():
    # 当前时间再集合uuid4就不会产生重复ID的问题了
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id(), ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='carchar(500)')
    name = StringField(ddl='varchar(50)')
    summmary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)


    class Comment(Model):
        __table__ = 'comments'

        id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
        blog_id = StringField(ddl='varchar(50)')
        user_id = StringField(ddl='varchar(50)')
        user_name = StringField(ddl='varchar(50)')
        user_image = StringField(ddl='varchar(500)')
        content = TextField()
        created_at = FloatField(default=time.time)
