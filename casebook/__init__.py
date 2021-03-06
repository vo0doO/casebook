#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

# Copyright (c) Valentin Fedulov <vasnake@gmail.com>
# See COPYING for details.

from casebook.const import CP

class LogOnError(Exception):
    '''raise this exception when LogOn request to casebook.ru failed
    '''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return u"%s" % (self.value, )


class RequestError(Exception):
    '''raise this exception when request to casebook.ru failed
    '''
    def __init__(self, value):
        self.value = value

    def __str__(self):
        if not isinstance(self.value, dict):
            return (u"%s" % (self.value, )).encode(CP)

        s = []
        for k,v in self.value.items():
            s.append(u"%s: %s" % (k, v))
        return (u'; '.join(s)).encode(CP)
