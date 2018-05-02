#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: spoob
    @author: sebnapi
    @author: RaNaN
    @author: mkaay
    @version: v0.4.9
"""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging
import logging.handlers
import os
import signal
import subprocess
import sys
from codecs import getwriter
from imp import find_module
from os import (
    _exit,
    chdir,
    close,
    execl,
    getcwd,
    remove,
    sep,
    walk,
)
from os.path import (
    exists,
    join,
)
from sys import (
    executable,
    exit,
)
from time import (
    sleep,
    time,
)
from traceback import print_exc

import click
import six

import module.common.pylgettext as gettext
from module import (
    InitHomeDir,
    remote,
)
from module.CaptchaManager import CaptchaManager
from module.common.JsEngine import JsEngine
from module.ConfigParser import ConfigParser
from module.database import (
    DatabaseBackend,
    FileHandler,
)
from module.network.RequestFactory import RequestFactory
from module.plugins.AccountManager import AccountManager
from module.plugins.PluginManager import PluginManager
from module.PullEvents import PullManager
from module.remote.RemoteManager import RemoteManager
from module.Scheduler import Scheduler
from module.singletons import (
    get_account_manager,
    get_hook_manager,
    get_remote_manager,
    get_thread_manager,
    set_account_manager,
    set_captcha_manager,
    set_plugin_manager,
    set_pull_manager,
    set_remote_manager,
    set_request_factory,
    set_thread_manager,
)
from module.util.compatibility import (
    IS_WINDOWS,
    install_translation,
)
from module.util.encoding import (
    smart_bytes,
    smart_text,
)
from module.utils import (
    formatSize,
    freeSpace,
    get_console_encoding,
)
from module.web.ServerThread import WebServer


CURRENT_VERSION = '0.4.9'

# TODO: Why is this required? Is it also required on Python 3?
if six.PY2:
    enc = get_console_encoding(sys.stdout.encoding)
    sys.stdout = getwriter(enc)(sys.stdout, errors='replace')

# TODO List
# - configurable auth system ldap/mysql
# - cron job like sheduler


def exceptHook(exc_type, exc_value, exc_traceback):
    logger = logging.getLogger("log")
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("<<< UNCAUGHT EXCEPTION >>>", exc_info=(exc_type, exc_value, exc_traceback))


class Core(object):
    """pyLoad Core, one tool to rule them all... (the filehosters) :D"""

    def __init__(self, **kwargs):
        if kwargs.get('display_version'):
            print("pyLoad", CURRENT_VERSION)
            exit()
        elif kwargs.get('do_clean'):
            self.cleanTree()
            exit()
        elif kwargs.get('user'):
            from module.setup import Setup

            self.config = ConfigParser()
            s = Setup(pypath, self.config)
            s.set_user()
            exit()
        elif kwargs.get('setup'):
            from module.setup import Setup

            self.config = ConfigParser()
            s = Setup(pypath, self.config)
            s.start()
            exit()
        elif kwargs.get('change_dir'):
            from module.setup import Setup

            self.config = ConfigParser()
            s = Setup(pypath, self.config)
            s.conf_path(True)
            exit()
        elif kwargs.get('do_quit'):
            self.quitInstance()
            exit()
        elif kwargs.get('display_status'):
            pid = self.isAlreadyRunning()
            if self.isAlreadyRunning():
                print(pid)
                exit(0)
            else:
                print("false")
                exit(1)

        self.running = False
        self.pidfile = kwargs.get('pidfile') or 'pyload.pid'
        self.doDebug = bool(kwargs.get('do_debug'))
        self.remote = not bool(kwargs.get('no_remote'))
        self.daemon = bool(kwargs.get('is_daemon'))
        self.deleteLinks = bool(kwargs.get('do_clear'))  # will delete links on startup

    def toggle_pause(self):
        thread_manager = get_thread_manager()

        thread_manager.pause = not thread_manager.pause
        return thread_manager.pause

    def quit(self, a, b):
        self.shutdown()
        self.log.info(_("Received Quit signal"))
        _exit(1)

    def writePidFile(self):
        self.deletePidFile()
        pid = os.getpid()
        f = open(self.pidfile, "wb")
        f.write(smart_bytes(pid))
        f.close()

    def deletePidFile(self):
        if self.checkPidFile():
            self.log.debug("Deleting old pidfile %s" % self.pidfile)
            os.remove(self.pidfile)

    def checkPidFile(self):
        """ return pid as int or 0"""
        if os.path.isfile(self.pidfile):
            f = open(self.pidfile, "rb")
            pid = f.read().strip()
            f.close()
            if pid:
                pid = int(pid)
                return pid

        return 0

    def isAlreadyRunning(self):
        pid = self.checkPidFile()
        if not pid or IS_WINDOWS:
            return False
        try:
            os.kill(pid, 0)  # 0 - default signal (does nothing)
        except Exception:
            return 0

        return pid

    def quitInstance(self):
        if IS_WINDOWS:
            print("Not supported on windows.")
            return

        pid = self.isAlreadyRunning()
        if not pid:
            print("No pyLoad running.")
            return

        try:
            os.kill(pid, 3) #SIGUIT

            t = time()
            print("waiting for pyLoad to quit")

            while exists(self.pidfile) and t + 10 > time():
                sleep(0.25)

            if not exists(self.pidfile):
                print("pyLoad successfully stopped")
            else:
                os.kill(pid, 9) #SIGKILL
                print("pyLoad did not respond")
                print("Kill signal was send to process with id %s" % pid)

        except:
            print("Error quitting pyLoad")


    def cleanTree(self):
        for path, dirs, files in walk(self.path("")):
            for f in files:
                if not f.endswith(".pyo") and not f.endswith(".pyc"):
                    continue

                if "_25" in f or "_26" in f or "_27" in f:
                    continue

                print(join(path, f))
                remove(join(path, f))

    def start(self, rpc=True, web=True):
        """ starts the fun :D """

        self.version = CURRENT_VERSION

        if not exists("pyload.conf"):
            from module.setup import Setup

            print("This is your first start, running configuration assistent now.")
            self.config = ConfigParser()
            s = Setup(pypath, self.config)
            res = False
            try:
                res = s.start()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print("\nSetup interrupted")
            except:
                res = False
                print_exc()
                print("Setup failed")
            if not res:
                remove("pyload.conf")

            exit()

        try: signal.signal(signal.SIGQUIT, self.quit)
        except: pass

        self.config = ConfigParser()

        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("pyLoad", self.path("locale"),
                                          languages=[self.config['general']['language'],"en"],fallback=True)
        install_translation(translation)

        self.debug = self.doDebug or self.config['general']['debug_mode']
        self.remote &= self.config['remote']['activated']

        pid = self.isAlreadyRunning()
        if pid:
            print(_("pyLoad already running with pid %s") % pid)
            exit()

        if not IS_WINDOWS and self.config["general"]["renice"]:
            os.system("renice %d %d" % (self.config["general"]["renice"], os.getpid()))

        if self.config["permission"]["change_group"]:
            if not IS_WINDOWS:
                try:
                    from grp import getgrnam

                    group = getgrnam(self.config["permission"]["group"])
                    os.setgid(group[2])
                except Exception as e:
                    print(_("Failed changing group: %s") % e)

        if self.config["permission"]["change_user"]:
            if not IS_WINDOWS:
                try:
                    from pwd import getpwnam

                    user = getpwnam(self.config["permission"]["user"])
                    os.setuid(user[2])
                except Exception as e:
                    print(_("Failed changing user: %s") % e)

        self.check_file(
            self.config['log']['log_folder'],
            _("folder for logs"),
            is_folder=True,
        )

        if self.debug:
            self.init_logger(logging.DEBUG) # logging level
        else:
            self.init_logger(logging.INFO) # logging level

        sys.excepthook = exceptHook

        self.do_kill = False
        self.do_restart = False
        self.shuttedDown = False

        self.log.info(_("Starting") + " pyLoad %s" % CURRENT_VERSION)
        self.log.info(_("Using home directory: %s") % getcwd())

        self.writePidFile()

        #@TODO refractor

        remote.activated = self.remote
        self.log.debug("Remote activated: %s" % self.remote)

        self.check_install("Crypto", _("pycrypto to decode container files"))
        #img = self.check_install("Image", _("Python Image Libary (PIL) for captcha reading"))
        #self.check_install("pycurl", _("pycurl to download any files"), True, True)
        self.check_file("tmp", _("folder for temporary files"), is_folder=True)
        #tesser = self.check_install("tesseract", _("tesseract for captcha reading"), False) if not IS_WINDOWS else True

        self.captcha = True # checks seems to fail, althoug tesseract is available

        self.check_file(
            self.config['general']['download_folder'],
            _("folder for downloads"),
            is_folder=True,
        )

        if self.config['ssl']['activated']:
            self.check_install("OpenSSL", _("OpenSSL for secure connection"))

        self.setupDB()

        if self.deleteLinks:
            self.log.info(_("All links removed"))
            self.db.purgeLinks()

        set_request_factory(RequestFactory(self))

        self.lastClientConnected = 0

        # later imported because they would trigger api import, and remote value not set correctly
        from module import Api
        from module.HookManager import HookManager
        from module.ThreadManager import ThreadManager

        if Api.activated != self.remote:
            self.log.warning("Import error: API remote status not correct.")

        self.api = Api.Api(self)

        self.scheduler = Scheduler(self)

        #hell yeah, so many important managers :D
        set_plugin_manager(PluginManager(self))
        set_pull_manager(PullManager(self))
        set_thread_manager(ThreadManager(self))
        set_account_manager(AccountManager(self))
        set_captcha_manager(CaptchaManager(self))
        # HookManager sets itself as a singleton
        HookManager(self)
        set_remote_manager(RemoteManager(self))

        thread_manager = get_thread_manager()

        self.js = JsEngine()

        self.log.info(_("Downloadtime: %s") % self.api.isTimeDownload())

        if rpc:
            get_remote_manager().startBackends()

        if web:
            self.init_webserver()

        spaceLeft = freeSpace(self.config["general"]["download_folder"])

        self.log.info(_("Free space: %s") % formatSize(spaceLeft))

        self.config.save() #save so config files gets filled

        link_file = join(pypath, "links.txt")

        if exists(link_file):
            f = open(link_file, "rb")
            if f.read().strip():
                self.api.addPackage("links.txt", [link_file], 1)
            f.close()

        link_file = "links.txt"
        if exists(link_file):
            f = open(link_file, "rb")
            if f.read().strip():
                self.api.addPackage("links.txt", [link_file], 1)
            f.close()

        #self.scheduler.addJob(0, get_account_manager().getAccountInfos)
        self.log.info(_("Activating Accounts..."))
        get_account_manager().getAccountInfos()

        thread_manager.pause = False
        self.running = True

        self.log.info(_("Activating Plugins..."))
        get_hook_manager().coreReady()

        self.log.info(_("pyLoad is up and running"))

        #test api
#        from module.common.APIExerciser import startApiExerciser
#        startApiExerciser(self, 3)

        #some memory stats
#        from guppy import hpy
#        hp=hpy()
#        import objgraph
#        objgraph.show_most_common_types(limit=20)
#        import memdebug
#        memdebug.start(8002)

        locals().clear()

        while True:
            try:
                sleep(2)
            except IOError as e:
                if e.errno != 4:  # errno.EINTR
                    raise

            if self.do_restart:
                self.log.info(_("restarting pyLoad"))
                self.restart()

            if self.do_kill:
                self.shutdown()
                self.log.info(_("pyLoad quits"))
                self.removeLogger()
                _exit(0) #@TODO thrift blocks shutdown

            thread_manager.work()
            self.scheduler.work()

    def setupDB(self):
        self.db = DatabaseBackend(self) # the backend
        self.db.setup()

        self.files = FileHandler(self)
        self.db.manager = self.files #ugly?

    def init_webserver(self):
        if self.config['webinterface']['activated']:
            self.webserver = WebServer(self)
            self.webserver.start()

    def init_logger(self, level):
        console = logging.StreamHandler(sys.stdout)
        frm = logging.Formatter("%(asctime)s %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")
        console.setFormatter(frm)
        self.log = logging.getLogger("log") # settable in config

        if self.config['log']['file_log']:
            if self.config['log']['log_rotate']:
                file_handler = logging.handlers.RotatingFileHandler(
                    join(smart_text(self.config['log']['log_folder']), u'log.txt'),
                    maxBytes=self.config['log']['log_size'] * 1024,
                    backupCount=int(self.config['log']['log_count']),
                    encoding="utf8",
                )
            else:
                file_handler = logging.FileHandler(
                    join(smart_text(self.config['log']['log_folder']), u'log.txt'),
                    encoding="utf8",
                )

            file_handler.setFormatter(frm)
            self.log.addHandler(file_handler)

        self.log.addHandler(console) #if console logging
        self.log.setLevel(level)

    def removeLogger(self):
        for h in list(self.log.handlers):
            self.log.removeHandler(h)
            h.close()

    def check_install(self, check_name, legend, python=True, essential=False):
        """check wether needed tools are installed"""
        try:
            if python:
                find_module(check_name)
            else:
                pipe = subprocess.PIPE
                subprocess.Popen(check_name, stdout=pipe, stderr=pipe)

            return True
        except:
            if essential:
                self.log.info(_("Install %s") % legend)
                exit()

            return False

    def check_file(self, check_name, description, is_folder=False):
        """Check whether needed files exist."""
        file_created = True
        file_exists = True

        check_name = smart_text(check_name)

        if not exists(check_name):
            file_exists = False

            try:
                if is_folder:
                    check_name = check_name.replace(u'/', smart_text(sep))
                    os.makedirs(check_name)
                else:
                    open(check_name, "w")
            except Exception:
                file_created = False

        if not file_exists and not file_created:
            print(_("could not create %(desc)s: %(name)s") % {"desc": description, "name": check_name})

    def isClientConnected(self):
        return (self.lastClientConnected + 30) > time()

    def restart(self):
        self.shutdown()
        chdir(owd)
        # close some open fds
        for i in range(3,50):
            try:
                close(i)
            except:
                pass

        execl(executable, executable, *sys.argv)
        _exit(0)

    def shutdown(self):
        self.log.info(_("shutting down..."))
        try:
            if self.config['webinterface']['activated'] and hasattr(self, "webserver"):
                self.webserver.quit()

            for thread in get_thread_manager().threads:
                thread.put("quit")
            pyfiles = self.files.cache.values()

            for pyfile in pyfiles:
                pyfile.abortDownload()

            get_hook_manager().coreExiting()

        except:
            if self.debug:
                print_exc()
            self.log.info(_("error while shutting down"))

        finally:
            self.files.syncSave()
            self.shuttedDown = True

        self.deletePidFile()


    def path(self, *args):
        return join(pypath, *args)


def daemon():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.print_("fork #1 failed: %d (%s)" % (e.errno, e.strerror), file=sys.stderr)
        sys.exit(1)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
        # exit from second parent, print eventual PID before
            print("Daemon PID %d" % pid)
            sys.exit(0)
    except OSError as e:
        six.print_("fork #2 failed: %d (%s)" % (e.errno, e.strerror), file=sys.stderr)
        sys.exit(1)

    # Iterate through and close some file descriptors.
    for fd in range(0, 3):
        try:
            os.close(fd)
        except OSError:    # ERROR, fd wasn't open to begin with (ignored)
            pass

    os.open(os.devnull, os.O_RDWR)    # standard input (0)
    os.dup2(0, 1)            # standard output (1)
    os.dup2(0, 2)

    pyload_core = Core()
    pyload_core.start()


@click.command()
@click.option(
    '--daemon',
    'is_daemon',
    is_flag=True,
    help='Daemonize after start',
)
@click.option(
    '--version', '-v',
    'display_version',
    is_flag=True,
    help='Print program version',
)
@click.option(
    '--clear', '-c',
    'do_clear',
    is_flag=True,
    help='Delete all saved packages/links',
)
@click.option(
    '--debug', '-d',
    'do_debug',
    is_flag=True,
    help='Enable debug mode',
)
@click.option(
    '--clean',
    'do_clean',
    is_flag=True,
    help='Remove .pyc/.pyo files',
)
@click.option(
    '--user', '-u',
    is_flag=True,
    help='Manage users',
)
@click.option(
    '--setup', '-s',
    is_flag=True,
    help='Run setup assistant',
)
@click.option(
    '--changedir',
    'change_dir',
    is_flag=True,
    help='Change config dir permanently',
)
@click.option(
    '--quit', '-q',
    'do_quit',
    is_flag=True,
    help='Quit running pyLoad instance',
)
@click.option(
    '--no-remote',
    is_flag=True,
    help='Disable remote access (saves RAM)',
)
@click.option(
    '--status',
    'display_status',
    is_flag=True,
    help='Display PID if running or False',
)
@click.option(
    '--pidfile', '-p',
    help='Set PID file',
)
def main(
    is_daemon,
    display_version,
    do_clear,
    do_debug,
    do_clean,
    user,
    setup,
    change_dir,
    do_quit,
    no_remote,
    display_status,
    pidfile,
):
    # change name to 'pyLoadCore'
    # from setproctitle import setproctitle
    # setproctitle('pyLoadCore')
    if is_daemon:
        daemon()
    else:
        pyload_core = Core(
            change_dir=change_dir,
            display_status=display_status,
            display_version=display_version,
            do_clear=do_clear,
            do_debug=do_debug,
            is_daemon=is_daemon,
            no_remote=no_remote,
            pidfile=pidfile,
            setup=setup,
            user=user,
        )
        try:
            pyload_core.start()
        except KeyboardInterrupt:
            pyload_core.shutdown()
            pyload_core.log.info(_("killed pyLoad from Terminal"))
            pyload_core.removeLogger()
            _exit(1)


# And so it begins...
if __name__ == "__main__":
    main()
