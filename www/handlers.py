#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file: handlers.py
@time: 2016/4/30 18:56
"""
__author__ = 'Hongqing Wang'

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio

from web_frame import get, post

from models import User, Comment, Blog, next_id

@get('/')
async def index(request):
    users = await User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }
