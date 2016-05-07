#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file: handlers.py
@time: 2016/4/30 18:56
"""
__author__ = 'Hongqing Wang'

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio

import markdown2

from aiohttp import web

from web_frame import get, post
from apis import APIValueError, APIResourceNotFoundError, APIPermissionError

from models import User, Comment, Blog, next_id
from config import configs

# email的匹配正则表达式
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
# 密码的匹配正则表达式
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

# 检测当前用户是不是admin用户
def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

# 获取页数，主要是做一些容错处理
def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

# 把存文本文件转为html格式的文本
def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

# 根据用户信息拼接一个cookie字符串
def user2cookie(user, max_age):
    # build cookie string by : id-expires-sha1
    # 到期时间是当前时间+设置的有效时间
    expires = str(int(time.time() + max_age))
    # 构建cookie存储的信息字符串
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    # 用-隔开，返回
    return '-'.join(L)

# 根据cookie字符串，解析出用户信息相关的

@asyncio.coroutine
def cookie2user(cookie_str):
    # cookie_str是空则返回
    if not cookie_str:
        return None
    try:
        # 通过'-'分割字符串
        L = cookie_str.split('-')
        # 如果不是3个元素的话，与我们当初构造sha1字符串时不符，返回None
        if len(L) != 3:
            return None
        # 分别获取到用户id，到期时间和sha1字符串
        uid, expires, sha1 = L
        # 如果超时，返回None
        if int(expires) < time.time():
            return None
        # 根据用户id查找库，对比有没有该用户
        user = yield from User.find(uid)
        # 没有该用户返回None
        if user is None:
            return  None
        # 根据查到的user的数据构造一个校验sha1字符串
        s = '%s-%s-%s-%s' % (uid, user.passwd,expires, _COOKIE_KEY)
        # 比较cookie里的sha1和校验sha1，一样的话，说明当前请求用户是合法的
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        # 返回合法的user
        return user
    except Exception as e:
        logging.exception(e)
        return None

@get('/')
def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

# 注册页面

@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

# 登录页面

@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }


# 登出操作

@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    # 清理掉cookie的用户信息数据
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out')
    return r


'''
@get('/api/users')
def api_get_users():
    users = yield from User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd = '******'
    return dict(users=users)
'''

# 注册请求

@post('/api/users')
def api_register_user(*, email, name, passwd):
    # 判断name是否存在，且是否只是'\n','\r','\t',' ',这种特殊字符
    if not name or not name.strip():
        raise APIValueError('name')
    # 判断email是否存在，且是否符合规定的正则表达式
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    # 判断passwd是否存在，且是否符合规定的正则表达式
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')

    # 查一下库里是否有相同的email地址，如果有的话提示用户email已经被注册过
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIValueError('register:failed', 'email', 'Email is already in use.')

    # 生成一个当前要注册用户的唯一uid
    uid = next_id()
    # 构建sha1_passwd
    sha1_passwd = '%s:%s' % (uid, passwd)

    admin = False
    if email == 'admin@163.com':
        admin = True

    # 创建一个用户（密码是通过sha1加密保存）
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest(), admin=admin)

    # 保存这个用户到数据库用户表
    yield from user.save()
    logging.info('save user OK')
    # 构建返回信息
    r = web.Response()
    # 添加cookie
    r.set_cookie(COOKIE_NAME, user2cookie(
        user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

# 登录请求

@post('/api/authenticate')
def authenticate(*, email, passwd):
    # 如果email或passwd为空，都说明有错误
    if not email:
        raise APIValueError('email', 'Invalid email')
    if not passwd:
        raise APIValueError('passwd', 'Invalid passwd')
    # 根据email在库里查询匹配的用户
    users = yield from User.findAll('email=?', [email])
    # 没找到用户，返回用户不存在
    if len(users) == 0:
        raise APIValueError('email', 'email not exist')
    # 取第一个查到用户，理论上就一个
    user = users[0]
    # 按存储密码的方式获取出请求传入的密码字段的sha1值
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    # 和库里的密码字段的值作比较，一样的话认证成功，不一样的话，认证失败
    if user.passwd != sha1.hexidgest():
        raise APIValueError('passwd', 'Invalid passwd')
    # 构建返回信息
    r = web.Response()
    # 添加cookie
    r.set_cookie(COOKIE_NAME, user2cookie(
        user, 86400), max_age=86400, httponly=True)
    # 只要把返回的实例的密码改成‘******’，库里的密码依然是正确的，以保证真实的密码不会因返回而暴露
    user.passwd = '******'
    # 返回的是json数据，所以设置content-type为json的
    r.content_type = 'application/json'
    # 把对象转换成json格式返回
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

#----------------------------评论管理---------------------------------------------

#-----------------------------用户管理--------------------------------------------

#-----------------------------博客管理的处理函数----------------------------------

@get('/manage/blogs/create')
def manage_create_blog():
    # 写博客页面
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs' # 对应HTML页面中VUE的action名字
    }

@post('/api/blogs')
def api_create_blog(request, *, name, summary, content):
    # 只有管理员可以写博客
    check_admin(request)
    # name, summary, content 不能为空
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')
    # 根据传入的信息，构建一条博客数据
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name,
                user_image=request.__user__.image, name=name.strip(), summary=summary.strip, content=content.strip())
    # 保存
    yield from blog.save()
    return blog

@get('/blog/{id}')
def get_blog(id):
    # 根据博客id查询该博客信息
    blog = yield from Blog.find(id)
    # 根据博客id查询该条博客的评论
    comments = yield from Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    # markdown2是个扩展模块，这里把博客正文和评论套入到markdown2中
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    # 返回页面
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

@get('/api/blogs/{id}')
def api_get_blog(*, id):
    # 获取某条博客信息
    blog = yield from Blog.find(id)
    return blog





