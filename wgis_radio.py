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

stations = [
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

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
station = 0
process = None

def sigterm_handler(signal, frame):
    stop_station()
    GPIO.cleanup()
    print('bye.')
    sys.exit(0)

def sigusr1_handler(signal, frame):
    print("usr1")
    stop_station()

def sigusr2_handler(signal, frame):
    print("usr2")
    play_station(stations[0])

signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGUSR1, sigusr1_handler)
signal.signal(signal.SIGUSR2, sigusr2_handler)

def process_output(process, station):
    while True:
        line = process.stderr.readline().decode('utf8')
        if line == '' and process.poll() != None:
            break
        if line != '':
            res = re.search(station['format'], line, re.M|re.I)
            if res:
                artist = res.group(1)
                title = res.group(2)
                udp.sendto('infoscreen/music/title:{}'.format(title).encode(), ('127.0.0.1', 4444))
                udp.sendto('infoscreen/music/artists:{}'.format(artist).encode(), ('127.0.0.1', 4444))
                udp.sendto('infoscreen/music/image:{}'.format(station['short']).encode(), ('127.0.0.1', 4444))
                udp.sendto('infoscreen/music/playing:true'.encode(), ('127.0.0.1', 4444))

def play_station(station):
    global process
    print('playing ' + station['name'])

    if process:
        process.terminate()
        process.wait()

    path = '{}/{}.jpeg'.format(os.path.dirname(os.path.realpath(__file__)), station['short'])
    if not os.path.isfile(path):
        res = requests.get(station['image'], stream=True)
        if res.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in res:
                    f.write(chunk)

    udp.sendto('infoscreen/music/title:{}'.format(station['name']).encode(), ('127.0.0.1', 4444))
    udp.sendto('infoscreen/music/artists:'.encode(), ('127.0.0.1', 4444))
    udp.sendto('infoscreen/music/image:{}'.format(station['short']).encode(), ('127.0.0.1', 4444))
    udp.sendto('infoscreen/music/playing:true'.encode(), ('127.0.0.1', 4444))

    process = subprocess.Popen(['mpg123', station['stream']], stderr=subprocess.PIPE)
    threading.Thread(target=process_output, args=(process, station,)).start()

def stop_station():
    if process:
        process.terminate()
        process.wait()

    udp.sendto('infoscreen/music/playing:false'.encode(), ('127.0.0.1', 4444))
    print('stopped ' + stations[station]['name'])

def change_station():
    global station

    print('change station.')
    station = (station + 1) % len(stations)
    play_station(stations[station])

def button_callback(channel):
    global station

    time.sleep(0.005)
    if GPIO.input(channel) == GPIO.LOW:
        print('level less than 5 ms')
        return

    print('button pressed.')
    if not process or process.poll() != None:
        print('play station.')
        station = 0
        play_station(stations[station])
    else:
        time.sleep(0.2)
        if GPIO.input(channel) == GPIO.LOW:
            change_station()
        else:
            time.sleep(0.2)
            if GPIO.input(channel) == GPIO.LOW:
                change_station()
            else:
                GPIO.remove_event_detect(channel)
                time.sleep(0.35)
                if GPIO.input(channel) == GPIO.HIGH:
                    print('stop station.')
                    stop_station()
                    time.sleep(2)
                GPIO.add_event_detect(PIN, GPIO.RISING, callback=button_callback, bouncetime=200)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(PIN, GPIO.RISING, callback=button_callback, bouncetime=200)

while True:
    signal.pause()
