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


"""All GUI events call this module, independent from the used toolkit."""


import os
import signal
import subprocess
import sys
import time
from argparse import ArgumentParser

import alsaaudio

from alsacontrol.alsa import get_num_output_channels
from alsacontrol.logger import logger, update_verbosity, log_info


def get_volume_icon(volume, muted):
    """Return an icon name for use in GUIs.

    Parameters
    ----------
    volume : float
        between 0 and 1.
    muted : bool
        True, if no sound plays currently.
    """
    if muted or volume <= 0:
        icon = 'audio-volume-muted'
    elif volume < 0.5:
        icon = 'audio-volume-low'
    elif volume < 1.0:
        icon = 'audio-volume-medium'
    else:
        icon = 'audio-volume-high'
    return icon


def get_volume_string(volume, muted):
    """Return a string representing the current output state."""
    if not muted:
        return '{}%'.format(round(volume * 100))
    else:
        return 'muted'


class Bindings:
    """Do everything the ui code wants to do without using ui libs."""
    def __init__(self):
        """Parse argv, print version, execute command if possible."""
        parser = ArgumentParser()
        parser.add_argument(
            '-d', '--debug', action='store_true', dest='debug',
            help='Displays additional debug information',
            default=False
        )

        options = parser.parse_args(sys.argv[1:])
        update_verbosity(options.debug)
        log_info()

        self.output_volume = 0
        self.speaker_test_pid = None

    def toggle_speaker_test(self):
        """Run the speaker-test script or stop it, if it is running.

        Returns True if it is run, False if it has been stopped.
        """
        if self.speaker_test_pid is None:
            num_channels = get_num_output_channels()
            cmd = 'speaker-test -D default -c {} -twav'.format(num_channels)
            logger.info('Testing speakers, %d channels', num_channels)
            process = subprocess.Popen(
                cmd,
                shell=True,
                preexec_fn=os.setsid
            )
            self.speaker_test_pid = process.pid
            return True

        self.stop_speaker_test()
        return False

    def stop_speaker_test(self):
        """Stop the speaker test if it is running."""
        if self.speaker_test_pid is not None:
            logger.info('Stopping speaker test')
            os.killpg(os.getpgid(self.speaker_test_pid), signal.SIGTERM)
            self.speaker_test_pid = None
