# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import re
from os.path import (
    exists,
    join,
)
from shutil import copy
from time import sleep
from traceback import print_exc

import six
from six.moves import range

from module.util.encoding import (
    smart_bytes,
    smart_text,
)

from .utils import chmod

# ignore these plugin configs, mainly because plugins were wiped out
IGNORE = (
    'FreakshareNet',
    'SpeedManager',
    'ArchiveTo',
    'ShareCx',
    ('hooks', 'UnRar'),
    'EasyShareCom',
    'FlyshareCz',
    # TODO: UpdateManager can't be used by pyreload, until a valid
    # update server is configured
    'UpdateManager',
)

CONF_VERSION = 1


class ConfigParser:
    """
    holds and manage the configuration

    current dict layout:

    {

     section : {
      option : {
            value:
            type:
            desc:
      }
      desc:

    }


    """

    CONFLINE = re.compile(r'^\s*(?P<T>.+?)\s+(?P<N>[^ ]+?)\s*:\s*"(?P<D>.+?)"\s*=\s?(?P<V>.*)')

    def __init__(self):
        """Constructor."""
        self.config = {}  # the config values
        self.plugin = {}  # the config for plugins
        self.pluginCB = None  # callback when plugin config value is changed

        self.checkVersion()
        self.read_config()
        self.deleteOldPlugins()

    def checkVersion(self):
        """determines if config need to be copied"""
        MAX_ITERATIONS = 4

        for iteration in range(1, MAX_ITERATIONS + 1):
            try:
                if not exists("pyload.conf"):
                    copy(join(pypath, "module", "config", "default.conf"), "pyload.conf")
                    chmod("pyload.conf", 0o600)

                if not exists("plugin.conf"):
                    with open("plugin.conf", "wb") as f:
                        f.write(smart_bytes("version: {0}".format(CONF_VERSION)))
                    chmod("plugin.conf", 0o600)

                with open("pyload.conf", "rb") as f:
                    v = f.readline()

                v = v[v.find(b":") + 1:].strip()

                if not v or int(v) < CONF_VERSION:
                    copy(join(pypath, "module", "config", "default.conf"), "pyload.conf")
                    print("Old version of config was replaced")

                with open("plugin.conf", "rb") as f:
                    v = f.readline()

                v = v[v.find(b":") + 1:].strip()

                if not v or int(v) < CONF_VERSION:
                    with open("plugin.conf", "wb") as f:
                        f.write(smart_bytes("version: {0}".format(CONF_VERSION)))
                    print("Old version of plugin-config replaced")

                return

            except Exception:
                if iteration < MAX_ITERATIONS:
                    sleep(0.3)
                else:
                    raise

    def read_config(self):
        """Read the configuration files and save their contents to inner objects."""
        self.config = self.parse_config(join(pypath, 'module', 'config', 'default.conf'))
        self.plugin = self.parse_config('plugin.conf')

        try:
            homeconf = self.parse_config('pyload.conf')
            self.updateValues(homeconf, self.config)
        except Exception as e:
            print('Config Warning')
            print_exc()

    def parse_config(self, config):
        """Parse a given configuration file."""
        with open(config) as f:
            config = f.read()

        config = config.splitlines()[1:]

        conf = {}

        section, option, value, typ, desc = "", "", "", "", ""

        listmode = False

        for line in config:
            comment = line.rfind("#")
            if line.find(":", comment) < 0 > line.find("=", comment) and comment > 0 and line[comment - 1].isspace():
                line = line.rpartition("#") # removes comments
                if line[1]:
                    line = line[0]
                else:
                    line = line[2]

            line = line.strip()

            try:
                if line == "":
                    continue
                elif line.endswith(":"):
                    section, none, desc = line[:-1].partition('-')
                    section = section.strip()
                    desc = desc.replace('"', "").strip()
                    conf[section] = {"desc": desc}
                else:
                    if listmode:
                        if line.endswith("]"):
                            listmode = False
                            line = line.replace("]", "")

                        value += [self.cast(typ, x.strip()) for x in line.split(",") if x]

                        if not listmode:
                            conf[section][option] = {"desc": desc,
                                                     "type": typ,
                                                     "value": value}


                    else:
                        m = self.CONFLINE.search(line)

                        typ = m.group('T')
                        option = m.group('N')
                        desc = m.group('D').strip()
                        value = m.group('V').strip()

                        if value.startswith("["):
                            if value.endswith("]"):
                                listmode = False
                                value = value[:-1]
                            else:
                                listmode = True

                            value = [self.cast(typ, x.strip()) for x in value[1:].split(",") if x]
                        else:
                            value = self.cast(typ, value)

                        if not listmode:
                            conf[section][option] = {"desc": desc,
                                                     "type": typ,
                                                     "value": value}

            except Exception as e:
                print("Config Warning:")
                print(line)
                print_exc()

        return conf


    def updateValues(self, config, dest):
        """sets the config values from a parsed config file to values in destination"""

        for section, section_data in six.iteritems(config):
            if section in dest:
                for option, option_data in six.iteritems(section_data):
                    if option in ("desc", "outline"):
                        continue

                    if option in dest[section]:
                        dest[section][option]["value"] = option_data["value"]

                        #else:
                        #    dest[section][option] = config[section][option]


                        #else:
                        #    dest[section] = config[section]

    def save_config(self, config, filename):
        """Save configuration `config` to a file with `filename` name."""
        with open(filename, 'wb') as f:
            chmod(filename, 0o600)
            f.write(smart_bytes('version: {0} \n'.format(CONF_VERSION)))

            for section in sorted(six.iterkeys(config)):
                f.write(smart_bytes('\n{0} - "{1}":\n'.format(section, config[section]["desc"])))

                for option, data in sorted(config[section].items(), key=lambda _x: _x[0]):
                    if option in ("desc", "outline"):
                        continue

                    if isinstance(data["value"], list):
                        value = "[ \n"
                        for x in data["value"]:
                            value += "\t\t" + str(x) + ",\n"
                        value += "\t\t]\n"
                    else:
                        value = '{val}\n'.format(val=smart_text(data["value"]))

                    f.write(smart_bytes(
                        u'\t{0} {1} : "{2}" = {3}'.format(
                            data["type"],
                            option,
                            data["desc"],
                            value,
                        )
                    ))

    def cast(self, typ, value):
        """cast value to given format"""
        if not isinstance(value, six.string_types):
            return value

        elif typ == "int":
            return int(value)
        elif typ == "bool":
            return value.lower() in {"1", "true", "on", "an", "yes"}
        elif typ == "time":
            if not value:
                value = "0:00"
            if ":" not in value:
                value += ":00"
            return value
        elif typ in {"str", "file", "folder"}:
            return smart_text(value)

        return value

    def save(self):
        """saves the configs to disk"""

        self.save_config(self.config, "pyload.conf")
        self.save_config(self.plugin, "plugin.conf")

    def __getitem__(self, section):
        """provides dictonary like access: c['section']['option']"""
        return Section(self, section)

    def get(self, section, option):
        """get value"""
        val = self.config[section][option]["value"]
        try:
            if isinstance(val, six.binary_type):
                return smart_text(val)
        except Exception:
            return val
        return val

    def set(self, section, option, value):
        """set value"""

        value = self.cast(self.config[section][option]["type"], value)

        self.config[section][option]["value"] = value
        self.save()

    def getPlugin(self, plugin, option):
        """gets a value for a plugin"""
        val = self.plugin[plugin][option]["value"]
        try:
            if isinstance(val, six.string_types):
                return val.decode("utf8")
            else:
                return val
        except:
            return val

    def setPlugin(self, plugin, option, value):
        """sets a value for a plugin"""

        value = self.cast(self.plugin[plugin][option]["type"], value)

        if self.pluginCB:
            self.pluginCB(plugin, option, value)

        self.plugin[plugin][option]["value"] = value
        self.save()

    def getMetaData(self, section, option):
        """ get all config data for an option """
        return self.config[section][option]

    def addPluginConfig(self, name, config, outline=""):
        """adds config options with tuples (name, type, desc, default)"""
        if name not in self.plugin:
            conf = {"desc": name,
                    "outline": outline}
            self.plugin[name] = conf
        else:
            conf = self.plugin[name]
            conf["outline"] = outline

        for item in config:
            if item[0] in conf and item[1] == conf[item[0]]["type"]:
                conf[item[0]]["desc"] = item[2]
            else:
                conf[item[0]] = {
                    "desc": item[2],
                    "type": item[1],
                    "value": self.cast(item[1], item[3])
                }

        values = [x[0] for x in config] + ["desc", "outline"]
        #delete old values
        for item in conf.keys():
            if item not in values:
                del conf[item]

    def deleteConfig(self, name):
        """Removes a plugin config"""
        if name in self.plugin:
            del self.plugin[name]


    def deleteOldPlugins(self):
        """ remove old plugins from config """
        for name in IGNORE:
            if name in self.plugin:
                del self.plugin[name]



class Section:
    """provides dictionary like access for configparser"""

    def __init__(self, parser, section):
        """Constructor"""
        self.parser = parser
        self.section = section

    def __getitem__(self, item):
        """getitem"""
        return self.parser.get(self.section, item)

    def __setitem__(self, item, value):
        """setitem"""
        self.parser.set(self.section, item, value)
