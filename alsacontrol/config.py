#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ALSA-Control - ALSA configuration interface
# Copyright (C) 2020 sezanzeb <proxima@hip70890b.de>
#
# This file is part of ALSA-Control.
#
# ALSA-Control is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ALSA-Control is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ALSA-Control.  If not, see <https://www.gnu.org/licenses/>.


"""Query settings, parse and write config files."""


import os

from alsacontrol.logger import logger


_config = None


_defaults = {
    'pcm_input': 'null',
    'input_use_dsnoop': True,
    'input_use_softvol': True,
    'input_plugin': 'hw',
    'pcm_output': 'null',
    'output_use_dmix': True,
    'output_use_softvol': True,
    'output_channels': 2,
    'output_plugin': 'hw'
}


def _modify_config(config_contents, key, value):
    """Return a string representing the modified contents of the config file.

    Parameters
    ----------
    config_contents : string
        Contents of the config file in ~/.config/alsacontrol/config.
        It is not edited in place and the config file is not overwritten.
    key : string
        Settings key that should be modified
    value : string, int
        Value to write
    """
    logger.info('Setting "%s" to "%s"', key, value)

    split = config_contents.split('\n')
    if split[-1] == '':
        split = split[:-1]

    found = False
    setting = f'{key}={value}'
    for i, line in enumerate(split):
        strip = line.strip()
        if strip.startswith('#'):
            continue
        if strip.startswith(f'{key}='):
            # replace the setting
            logger.debug('Overwriting "%s=%s" in config', key, value)
            split[i] = setting
            found = True
            break
    if not found:
        logger.debug('Adding "%s=%s" to config', key, value)
        split.append(setting)
    return '\n'.join(split)


class Config:
    """Read and set config values."""
    def __init__(self, path=None):
        """Initialize the interface to the config file.

        Parameters
        ----------
        path : string or None
            If none, will default to '~/.config/alsacontrol/config'
        """
        if path is None:
            path = os.path.expanduser('~/.config/alsacontrol/config')
        logger.debug('Using config file at %s', path)

        self._path = path
        self._config = {}
        self.mtime = 0

        self.create_config_file()

        self.load_config()

    def create_config_file(self):
        """Create an empty config if it doesn't exist."""
        if not os.path.exists(os.path.dirname(self._path)):
            os.makedirs(os.path.dirname(self._path))
        if not os.path.exists(self._path):
            logger.info('Creating config file "%s"', self._path)
            os.mknod(self._path)

    def load_config(self):
        """Read the config file."""
        logger.debug('Loading configuration')
        self._config = {}
        # load config
        self.mtime = os.path.getmtime(self._path)
        with open(self._path, 'r') as config_file:
            for line in config_file:
                line = line.strip()
                if not line.startswith('#'):
                    split = line.split('=', 1)
                    if len(split) == 2:
                        key = split[0]
                        value = split[1]
                    else:
                        key = split[0]
                        value = None
                if value.isdigit():
                    value = int(value)
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                if value == 'True':
                    value = True
                if value == 'False':
                    value = False
                self._config[key] = value

    def check_mtime(self):
        """Check if the config file has been modified and reload if needed."""
        if os.path.getmtime(self._path) != self.mtime:
            logger.info('Config changed, reloading')
            self.load_config()

    def get(self, key):
        """Read a value from the configuration or get the default."""
        self.check_mtime()
        if key not in _defaults:
            logger.error('Unknown setting %s', key)
            return None
        return self._config.get(key, _defaults[key])

    def set(self, key, value):
        """Write a setting into memory and ~/.config/alsacontrol/config."""
        if key not in _defaults:
            logger.error('Unknown setting %s', key)
            return None

        self.check_mtime()

        if key in self._config and self._config[key] == value:
            logger.debug('Setting "%s" is already "%s"', key, value)
            return False

        self._config[key] = value

        with open(self._path, 'r+') as config_file:
            config_contents = config_file.read()
            config_contents = _modify_config(config_contents, key, value)

        # overwrite completely
        with open(self._path, 'w') as config_file:
            if not config_contents.endswith('\n'):
                config_contents += '\n'
            config_file.write(config_contents)

        self.mtime = os.path.getmtime(self._path)
        return True


def get_config(*args, **kwargs):
    """Ask for the config. Initialize it if not yet done so.

    Will pass any parameters to the config constructor. Only needed in tests
    to avoid writing the users config.
    """
    # don't initialize it right away in the global scope, to avoid having
    # the wrong logging verbosity.
    global _config
    if _config is None:
        _config = Config(*args, **kwargs)
    return _config
