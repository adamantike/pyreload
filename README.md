# pyreload

|                       |     Status     |
| --------------------- | -------------- |
| Build                 | [![Build Status](https://travis-ci.org/pyreload/pyreload.svg?branch=master)](https://travis-ci.org/pyreload/pyreload) |
| Code quality          | [![Maintainability](https://api.codeclimate.com/v1/badges/dfcf925fdb8be0544c5e/maintainability)](https://codeclimate.com/github/pyreload/pyreload/maintainability) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/f146f220efef4a0f84ee1aff0e1a224f)](https://www.codacy.com/app/adamantike/pyreload) |
| Test coverage         | [![Coverage Status](https://coveralls.io/repos/github/pyreload/pyreload/badge.svg?branch=master)](https://coveralls.io/github/pyreload/pyreload?branch=master) [![Test Coverage](https://api.codeclimate.com/v1/badges/dfcf925fdb8be0544c5e/test_coverage)](https://codeclimate.com/github/pyreload/pyreload/test_coverage) [![Codacy Badge](https://api.codacy.com/project/badge/Coverage/f146f220efef4a0f84ee1aff0e1a224f)](https://www.codacy.com/app/adamantike/pyreload) |
| Dependency management | [![Requirements Status](https://requires.io/github/pyreload/pyreload/requirements.svg?branch=master)](https://requires.io/github/pyreload/pyreload/requirements/?branch=master) |
| Communication | [![Join the chat](https://badges.gitter.im/pyreload/Lobby.svg)](https://gitter.im/pyreload/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) |

Description
===========

pyreload forked pyLoad to focus on a deliverable software with code tests and build process.

Its a free and open source downloader for 1-click-hosting sites like rapidshare.com or uploaded.to.
It supports link decryption as well as all important container formats.

pyreload is written in Python and is currently under heavy development.

To report bugs, suggest features, ask a question, get the developer version
or help us out, visit http://github.com/pyreload/pyreload

Documentation about extending pyLoad can be found at https://github.com/pyload/pyload/wiki

Dependencies
============

You need at least Python 2.7 to run pyLoad and all of these required libraries.
They should be automatically installed when using pip install.
The prebuilt pyload packages also install these dependencies or have them included, so manuall install
is only needed when installing pyLoad from source.

Required
--------

- pycurl a.k.a python-curl
- jinja2
- beaker
- thrift

Some plugins require additional packages, only install these when needed.

Optional
--------

- pycrypto: RSDF/CCF/DLC support
- tesseract, python-pil a.k.a python-imaging: Automatic captcha recognition for a small amount of plugins
- jsengine (spidermonkey, ossp-js, pyv8, rhino): Used for several hoster, ClickNLoad
- feedparser
- BeautifulSoup
- pyOpenSSL: For SSL connection

First start
===========

Note: If you installed pyload via package-manager `python pyLoadCore.py` is probably equivalent to `pyLoadCore`

Run::

    python pyLoadCore.py

and follow the instructions of the setup assistent.

For a list of options use::

    python pyLoadCore.py -h

Configuration
=============

After finishing the setup assistent pyLoad is ready to use and more configuration can be done via webinterface.
Additionally you could simply edit the config files located in your pyLoad home dir (defaults to: ~/.pyload)
with your favorite editor and edit the appropriate options. For a short description of
the options take a look at https://github.com/pyload/pyload/wiki/Configuration.

To restart the configure assistent run::

    python pyLoadCore.py -s

Adding downloads
----------------

To start the CLI and connect to a local server, run::

    python pyLoadCli.py -l

for more options refer to::

    python pyLoadCli.py -h

The webinterface can be accessed when pointing your webbrowser to the ip and configured port, defaults to http://localhost:8000
