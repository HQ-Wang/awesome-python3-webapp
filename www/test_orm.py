#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file: test_orm.py
@time: 2016/4/15 14:37
"""
__author__ = 'Hongqing Wang'

from models import User
import asyncio
import orm
import pdb
import time

# 测试插入

@asyncio.coroutine
def test_save(loop):
    yield from orm.create_pool(loop, user='kami', password='kami', db='pure_blog')
    u = User(name='hi', email='hi@example.com',
             passwd='hi', image='about:blank')
    #pdb.set_trace()
    yield from u.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test_save(loop))
__pool = orm.__pool
__pool.close()      # 需要先关闭连接池
loop.run_until_complete(__pool.wait_closed())
loop.close()