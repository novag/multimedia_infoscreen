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
import socket
import subprocess
import threading
from RPi import GPIO
from . import utils

PIN_AIRCOOLING = 17
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_AIRCOOLING, GPIO.OUT)

class OutputProcessorThread(threading.Thread):
    def __init__(self, player, callback):
        super(OutputProcessorThread, self).__init__()
        self.player = player
        self.callback = callback

    def run(self):
        while self.player:
            if not self.player or self.player.poll() != None:
                break

        utils.ib_notify('infoscreen/overlay/visible', 'false')
        if self.callback:
            self.callback()


restreamer = None
player = None
output_thread = None

def stop_radio():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect('/tmp/radio.ctrl')
    except socket.error as msg:
        print(msg)

    sock.sendall(b'stop')
    sock.close()

def is_playing():
    return player and player.poll() == None

def stop():
    global output_thread, player, restreamer

    GPIO.output(PIN_AIRCOOLING, GPIO.LOW)

    if restreamer and restreamer.poll() == None:
        os.killpg(os.getpgid(restreamer.pid), signal.SIGTERM)
        restreamer.wait()

    if player and player.poll() == None:
        os.killpg(os.getpgid(player.pid), signal.SIGTERM)
        player.wait()

    restreamer = None
    player = None

    output_thread = None

def play(url, callback=None, hls=False, fit=False):
    global output_thread, player, restreamer

    print('streamer: play: ' + url)
    stop()

    stop_radio()

    GPIO.output(PIN_AIRCOOLING, GPIO.HIGH)

    if hls:
        restreamer = subprocess.Popen([
            'ffmpeg',
            '-i', url,
            '-c', 'copy',
            '-f', 'mpegts',
            'udp://localhost:1234'
        ], preexec_fn=os.setsid)

        url = 'udp://localhost:1234'

    if fit:
        player = subprocess.Popen([
            'omxplayer',
            '--timeout', '20',
            '-b',
            '-o', 'alsa:hw:1,0',
            '--win', '165,540,1155,1080',
            url
        ], stderr=subprocess.PIPE, preexec_fn=os.setsid)
    else:
        player = subprocess.Popen([
            'omxplayer',
            '--timeout', '20',
            '-b',
            '-o', 'alsa:hw:1,0',
            url
        ], stderr=subprocess.PIPE, preexec_fn=os.setsid)
        utils.ib_notify('infoscreen/overlay/visible', 'true')

    output_thread = OutputProcessorThread(player, callback)
    output_thread.start()

    utils.ib_notify('infoscreen/selector/visible', 'false')
