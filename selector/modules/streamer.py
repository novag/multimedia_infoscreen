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

        GPIO.output(PIN_AIRCOOLING, GPIO.LOW)
        utils.ib_notify('infoscreen/overlay/visible', 'false')
        if self.callback:
            self.callback()


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
    global output_thread, player

    GPIO.output(PIN_AIRCOOLING, GPIO.LOW)

    if player and player.poll() == None:
        os.killpg(os.getpgid(player.pid), signal.SIGTERM)
        player.wait()

    player = None

    output_thread = None

def play(url, callback=None, fit=False):
    global output_thread, player

    print('streamer: play: ' + url)
    stop()

    stop_radio()

    GPIO.output(PIN_AIRCOOLING, GPIO.HIGH)

    player = subprocess.Popen([
        'cvlc',
        '--play-and-exit',
        '--no-video-title',
        '--aout=alsa',
        '--alsa-audio-device', 'hw:CARD=Headphones',
        url
    ], stderr=subprocess.PIPE, preexec_fn=os.setsid)
    utils.ib_notify('infoscreen/overlay/visible', 'true')

    output_thread = OutputProcessorThread(player, callback)
    output_thread.start()

    utils.ib_notify('infoscreen/selector/visible', 'false')
