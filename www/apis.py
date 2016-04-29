#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file: apis.py
@time: 2016/4/25 14:24
"""
__author__ = 'Hongqing Wang'
'''
JSON API definition.
'''

import json
import logging
import inspect
import functools

# 简单的几个api错误异常类，用于抛出异常

class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional).
    '''
    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. the data specifies the error field of input form.
    '''
    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('value:invalid', field, message)

class APIResourseNotFoundError(APIError):
    '''
    Indicate the resource was not found. teh data specifies the resource name.
    '''
    def __init__(self, field, message=''):
        super(APIResourseNotFoundError, self).__init__('value:notfound', field, message)

class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''
    def __init__(self, message=''):
        super(APIPermissionError, self).__init__('permission:forbidden', 'permission', message)