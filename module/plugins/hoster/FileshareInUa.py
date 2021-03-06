# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from ..internal.DeadHoster import DeadHoster


class FileshareInUa(DeadHoster):
    __name__ = "FileshareInUa"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?fileshare\.in\.ua/\w{7}'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Fileshare.in.ua hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("fwannmacher", "felipe@warhammerproject.com")]
