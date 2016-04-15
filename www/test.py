from models import User
import asyncio
import orm
import pdb
import time

# 测试插入

@asyncio.coroutine
def test_save(loop):
    yield from orm.create_pool(user='www-data', password='www-data', database='awesome')

    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    yield from u.save()

for x in test():
    pass
