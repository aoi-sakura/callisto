# -*- coding: utf-8 -*-
import urllib.request


def get_stb_info(location, ua):
    req = urllib.request.Request(location)
    with urllib.request.urlopen(req) as res:
        body = res.read()
        return body
