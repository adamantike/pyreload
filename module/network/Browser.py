#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from logging import getLogger

from module.network.HTTPDownload import HTTPDownload
from module.network.HTTPRequest import HTTPRequest


class Browser(object):
    __slots__ = ("log", "options", "bucket", "cj", "_size", "http", "dl")

    def __init__(self, bucket=None, options=None):
        self.log = getLogger("log")

        # Holds pycurl options
        self.options = options if options is not None else {}
        self.bucket = bucket

        # Needs to be set later
        self.cj = None
        self._size = 0

        self.renewHTTPRequest()
        self.dl = None

    def renewHTTPRequest(self):
        if hasattr(self, "http"):
            self.http.close()
        self.http = HTTPRequest(self.cj, self.options)

    def setLastURL(self, val):
        self.http.lastURL = val

    # tunnel some attributes from HTTP Request to Browser
    lastEffectiveURL = property(lambda self: self.http.lastEffectiveURL)
    lastURL = property(lambda self: self.http.lastURL, setLastURL)
    code = property(lambda self: self.http.code)
    cookieJar = property(lambda self: self.cj)

    def setCookieJar(self, cj):
        self.cj = cj
        self.http.cj = cj

    @property
    def speed(self):
        if self.dl:
            return self.dl.speed
        return 0

    @property
    def size(self):
        if self._size:
            return self._size
        if self.dl:
            return self.dl.size
        return 0

    @property
    def arrived(self):
        if self.dl:
            return self.dl.arrived
        return 0

    @property
    def percent(self):
        if not self.size:
            return 0
        return (self.arrived * 100) / self.size

    def clearCookies(self):
        if self.cj:
            self.cj.clear()
        self.http.clearCookies()

    def clearReferer(self):
        self.http.lastURL = None

    def abortDownloads(self):
        self.http.abort = True
        if self.dl:
            self._size = self.dl.size
            self.dl.abort = True

    def httpDownload(self, url, filename, get={}, post={}, ref=True, cookies=True, chunks=1, resume=False,
                     progressNotify=None, disposition=False):
        """ this can also download ftp """
        self._size = 0
        self.dl = HTTPDownload(
            url,
            filename,
            get,
            post,
            self.lastEffectiveURL if ref else None,
            self.cj if cookies else None,
            self.bucket,
            self.options,
            progressNotify,
            disposition
        )
        name = self.dl.download(chunks, resume)
        self._size = self.dl.size

        self.dl = None

        return name

    def load(self, *args, **kwargs):
        """ retrieves page """
        return self.http.load(*args, **kwargs)

    def putHeader(self, name, value):
        """ add a header to the request """
        self.http.putHeader(name, value)

    def addAuth(self, pwd):
        """Adds user and pw for http auth

        :param pwd: string, user:password
        """
        self.options["auth"] = pwd
        # We need a new request
        self.renewHTTPRequest()

    def removeAuth(self):
        if "auth" in self.options:
            del self.options["auth"]
        self.renewHTTPRequest()

    def setOption(self, name, value):
        """Adds an option to the request, see HTTPRequest for existing ones"""
        self.options[name] = value

    def deleteOption(self, name):
        if name in self.options:
            del self.options[name]

    def clearHeaders(self):
        self.http.clearHeaders()

    def close(self):
        """ cleanup """
        if hasattr(self, "http"):
            self.http.close()
            del self.http
        if hasattr(self, "dl"):
            del self.dl
        if hasattr(self, "cj"):
            del self.cj
