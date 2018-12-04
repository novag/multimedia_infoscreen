#!/usr/bin/python3 -u

"""
multimedia: play/change/stop radio station on button event

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
import queue
import re
import requests
import signal
import socket
import subprocess
import sys
import threading
import time
from RPi import GPIO

STATIONS = [
    {
        'name': '95.5 Charivari',
        'short': 'charivari',
        'stream': 'http://rs5.stream24.net/stream',
        'image': 'https://www.charivari.de/assets/Uploads/_resampled/ScaleHeightWyI5NSJd/logo-955-charivari-webseite.png',
        'format': r"StreamTitle='(.*) - (.*?)';"
    },
    {
        'name': 'Radio Gong 96.3',
        'short': 'gong',
        'stream': 'http://mp3.radiogong963.c.nmdn.net/ps-radiogong963/livestream.mp3',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/b/b7/Gong_96.3_Logo.jpg',
        'format': r"StreamTitle='(?:Gong 96.3 - )?(.*) - (.*?)';"
    },
    {
        'name': 'top100station',
        'short': 'top100station',
        'stream': 'http://87.230.103.76/',
        'image': 'https://top100station.de/wp-content/uploads/2018/06/cropped-logo_hd.png',
        'format': r"StreamTitle='(.*) - (.*?)';"
    },
    {
        'name': '95.5 Charivari - PARTY-HIT-MIX',
        'short': 'charivari_party',
        'stream': 'http://rs5.stream24.net:8000/stream',
        'image': 'http://static.radio.de/images/broadcasts/d5/ce/5369/2/c175.png',
        'format': r"StreamTitle='(.*) - (.*?)';"
    },
    {
        'name': 'BAYERN 3',
        'short': 'bayern3',
        'stream': 'http://br-br3-live.cast.addradio.de/br/br3/live/mp3/128/stream.mp3',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Bayern3_logo_2015.svg/220px-Bayern3_logo_2015.svg.png',
        'format': r"StreamTitle='(?!Studio-Hotline)(.*): (.*?)';"
    },
    {
        'name': '95.5 Charivari - LOUNGE',
        'short': 'charivari_lounge',
        'stream': 'http://rs24.stream24.net:80/lounge',
        'image': 'http://static.radio.de/images/broadcasts/d0/53/20961/3/c175.png',
        'format': r"StreamTitle='(.*) - (.*?)';"
    }
]

PIN = 15

class Radio():
    SOCKET_ADDR = '/tmp/radio.ctrl'

    def __init__(self):
        self.station = 0
        self.process = None

    def init(self):
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)
        signal.signal(signal.SIGUSR1, self.sigusr1_handler)
        signal.signal(signal.SIGUSR2, self.sigusr2_handler)

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(PIN, GPIO.RISING, callback=self.button_callback, bouncetime=200)

    def run(self):
        try:
            os.unlink(self.SOCKET_ADDR)
        except OSError:
            if os.path.exists(self.SOCKET_ADDR):
                raise

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.SOCKET_ADDR)
        sock.listen(1)

        while True:
            connection, client_address = sock.accept()
            try:
                cmd = connection.recv(1)
                if cmd == b'n': # next
                    self.next()
                elif cmd == b'p': # previous
                    self.previous()
                elif cmd == b's': # stop
                    self.stop()
            finally:
                connection.close()

    def ib_notify(self, path, data=''):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.sendto('{}:{}'.format(path, data).encode(), ('127.0.0.1', 4444))

    def process_output(self, process, station):
        while True:
            line = self.process.stderr.readline().decode('utf8')
            if line == '' and self.process.poll() != None:
                break
            if line != '':
                res = re.search(station['format'], line, re.M|re.I)
                if res:
                    artist = res.group(1)
                    title = res.group(2)
                    print('title:' + title)
                    self.ib_notify('infoscreen/music/title', title)
                    self.ib_notify('infoscreen/music/artists', artist)
                    self.ib_notify('infoscreen/music/image', station['short'])
                    self.ib_notify('infoscreen/music/playing', 'true')

    def play(self, station):
        print('wgis_radio: play ' + station['name'])

        if self.process:
            self.process.terminate()
            self.process.wait()

        path = '{}/{}.jpeg'.format(os.path.dirname(os.path.realpath(__file__)), station['short'])
        if not os.path.isfile(path):
            res = requests.get(station['image'], stream=True)
            if res.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in res:
                        f.write(chunk)

        self.ib_notify('infoscreen/music/title', station['name'])
        self.ib_notify('infoscreen/music/artists')
        self.ib_notify('infoscreen/music/image', station['short'])
        self.ib_notify('infoscreen/music/playing', 'true')

        self.process = subprocess.Popen(['mpg123', station['stream']], stderr=subprocess.PIPE)
        threading.Thread(target=self.process_output, args=(self.process, station,)).start()

    def stop(self):
        print('wgis_radio: stop ' + STATIONS[self.station]['name'])

        if self.process:
            self.process.terminate()
            self.process.wait()

        self.ib_notify('infoscreen/music/playing', 'false')

    def previous(self):
        print('wgis_radio: previous station.')

        self.station = (self.station - 1) % len(STATIONS)
        self.play(STATIONS[self.station])

    def next(self):
        print('wgis_radio: next station.')

        self.station = (self.station + 1) % len(STATIONS)
        self.play(STATIONS[self.station])

    def button_callback(self, channel):
        time.sleep(0.005)
        if GPIO.input(channel) == GPIO.LOW:
            print('level less than 5 ms')
            return

        print('button pressed.')
        if not self.process or self.process.poll() != None:
            print('play station.')
            self.station = 0
            self.play(STATIONS[self.station])
        else:
            time.sleep(0.2)
            if GPIO.input(channel) == GPIO.LOW:
                self.next()
            else:
                time.sleep(0.2)
                if GPIO.input(channel) == GPIO.LOW:
                    self.next()
                else:
                    GPIO.remove_event_detect(channel)
                    time.sleep(0.35)
                    if GPIO.input(channel) == GPIO.HIGH:
                        self.stop()
                        time.sleep(2)
                    GPIO.add_event_detect(PIN, GPIO.RISING, callback=self.button_callback, bouncetime=200)

    def sigterm_handler(self, signal, frame):
        print('bye.')

        self.stop()
        GPIO.cleanup()
        sys.exit(0)

    def sigusr1_handler(signal, frame):
        print("usr1")

        self.stop()

    def sigusr2_handler(signal, frame):
        print("usr2")

        self.play(STATIONS[0])

if __name__ == '__main__':
    radio = Radio()
    radio.init()
    radio.run()