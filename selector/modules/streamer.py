#!/usr/bin/python3 -u

"""
multimedia: streamer

 Copyright (C) 2018 Hendrik Hagendorn

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import signal
import subprocess
import threading
from . import utils


class OutputProcessorThread(threading.Thread):
    def __init__(self, process, callback):
        super(OutputProcessorThread, self).__init__()
        self.process = process
        self.callback = callback

    def run(self):
        while self.process:
            if not self.process or self.process.poll() != None:
                break

        utils.ib_notify('infoscreen/overlay/visible', 'false')
        if self.callback:
            self.callback()


process = None
output_thread = None

def is_playing():
    return process and process.poll() == None

def stop():
    global output_thread, process

    if process and process.poll() == None:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()

    process = None

    output_thread = None

def play(url, callback=None, fit=False):
    global output_thread, process

    print('streamer: play: ' + url)
    stop()

    os.system('killall -SIGUSR1 wgis_radio.py')

    if fit:
        process = subprocess.Popen(['omxplayer', '-b', '-o', 'alsa:hw:1,0', '--win', '0,530,880,1025', url], stderr=subprocess.PIPE, preexec_fn=os.setsid)
    else:
        process = subprocess.Popen(['omxplayer', '-b', '-o', 'alsa:hw:1,0', url], stderr=subprocess.PIPE, preexec_fn=os.setsid)
        utils.ib_notify('infoscreen/overlay/visible', 'true')

    output_thread = OutputProcessorThread(process, callback)
    output_thread.start()

    utils.ib_notify('infoscreen/selector/visible', 'false')
