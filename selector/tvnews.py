#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

"""
multimedia: play/change/stop sport stream on button event

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

import datetime
import feedparser
import json
import os
import re
import requests
import signal
import socket
import sys
import time
from RPi import GPIO

programmes = [
    {
        'name': 'Tagesschau in 100 Sekunden',
        'short': 'tagesschau100',
        'rss': 'https://www.ardmediathek.de/tv/Tagesschau-in-100-Sekunden/Sendung?documentId=52149182&bcastId=52149182&rss=true',
        'picon': 'https://img.ardmediathek.de/standard/00/52/14/95/00/-1774185891/16x9/704?mandant=ard',
        'provider': 'ard'
    },
    {
        'name': 'Tagesthemen',
        'short': 'tagesthemen',
        'rss': 'https://www.ardmediathek.de/tv/Tagesthemen/Sendung?documentId=3914&bcastId=3914&rss=true',
        'picon': 'https://img.ardmediathek.de/standard/00/00/00/39/22/67648717/16x9/704?mandant=ard',
        'provider': 'ard'
    },
    {
        'name': 'Tagesschau',
        'short': 'tagesschau',
        'rss': 'https://www.ardmediathek.de/tv/Tagesschau/Sendung?documentId=4326&bcastId=4326&rss=true',
        'picon': 'https://img.ardmediathek.de/standard/00/07/64/05/74/2121327408/16x9/384?mandant=ard',
        'provider': 'ard'
    }
]

PIN = 16

epg_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'epg.tvnews.json')
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
epg_data = []
entries = []
selected_entry_id = None
playing = False

def download_file(name, url, parent=False):
    res = requests.head(url)
    if not res:
        return None

    filetype = res.headers['content-type'].split('/')[-1]
    filename = '{}.{}'.format(name, filetype)
    if parent:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), filename)
    else:
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)

    if os.path.isfile(path):
        return filename

    res = requests.get(url, stream=True)
    if not res.ok:
        return None

    with open(path, 'wb') as f:
        for chunk in res:
            f.write(chunk)

    return filename

def refresh_entries():
    global entries

    entries = []

    for epg_program in epg_data:
        program = programmes[epg_program['program_id']]
        date = datetime.datetime.strptime(epg_program['published'], "%a, %d %b %Y %H:%M:%S %Z")

        entries.append({
            'name': program['name'],
            'picon': program['short'],
            'subtitle': '{} - {} min'.format(date.strftime("%d.%m.%Y, %H:%M"), epg_program['duration'])
        })

def update():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 4444))
    s.recv(1000)
    s.send('selector\n'.encode())
    s.recv(1000)
    try:
        messages = []

        s.send(json.dumps({'entries': entries, 'messages': messages}, ensure_ascii=False).encode('utf8'))
        s.send('\n'.encode())
    except:
        pass
    finally:
        s.close()

def play_video(name):
    global playing
    print('playing ' + name)

    os.system('killall -SIGUSR1 wgis_radio.py')

    playing = True

    udp.sendto('infoscreen/selector/visible:false'.encode(), ('127.0.0.1', 4444))
    udp.sendto('infoscreen/video/file:{}'.format(name).encode(), ('127.0.0.1', 4444))
    udp.sendto('infoscreen/video/visible:true'.encode(), ('127.0.0.1', 4444))

def stop_video():
    global playing, selected_entry_id

    if not playing:
        return

    playing = False
    selected_entry_id = None

    udp.sendto('infoscreen/video/visible:false'.encode(), ('127.0.0.1', 4444))
    print('stopped ' + entries[selected_entry_id]['program']['name'])

def send_selected():
    udp.sendto('selector/selection:{}'.format(selected_entry_id + 1).encode(), ('127.0.0.1', 4444))
    udp.sendto('selector/update:'.encode(), ('127.0.0.1', 4444))

def short_press():
    global selected_entry_id

    print('short press.')
    if playing:
        stop_video()
    elif selected_entry_id == None:
        refresh_entries()
        update()

        if entries:
            selected_entry_id = 0
            send_selected()

        udp.sendto('infoscreen/selector/visible:true'.encode(), ('127.0.0.1', 4444))
    else:
        selected_entry_id = (selected_entry_id + 1) % len(entries)
        send_selected()

def long_press():
    print('long press.')

    if not playing and selected_entry_id != None:
        play_video(epg_data[selected_entry_id]['video'])

def button_callback(channel):
    time.sleep(0.005)
    if GPIO.input(channel) == GPIO.LOW:
        print('level less than 5 ms')
        return

    print('button pressed.')
    time.sleep(0.2)
    if GPIO.input(channel) == GPIO.LOW:
        short_press()
    else:
        time.sleep(0.2)
        if GPIO.input(channel) == GPIO.LOW:
            short_press()
        else:
            GPIO.remove_event_detect(channel)
            time.sleep(0.35)
            if GPIO.input(channel) == GPIO.HIGH:
                long_press()
                time.sleep(2)
            GPIO.add_event_detect(PIN, GPIO.RISING, callback=button_callback, bouncetime=200)

def reload_epg():
    global epg_data

    for program in programmes:
        download_file(program['short'], program['picon'])

    if not os.path.isfile(epg_path):
        fetch(False)

    with open(epg_path) as file:
        epg_data = json.load(file)

def sigterm_handler(signal, frame):
    stop_video()
    GPIO.cleanup()
    print('bye.')
    sys.exit(0)

def sigusr1_handler(signal, frame):
    global selected_entry_id
    print("usr1")
    #stop_video()
    refresh_entries()
    update()

    if entries:
        selected_entry_id = 0
        send_selected()

    udp.sendto('infoscreen/selector/visible:true'.encode(), ('127.0.0.1', 4444))

def sigusr2_handler(signal, frame):
    print("usr2")
    reload_epg()

def main():
    reload_epg()

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGUSR1, sigusr1_handler)
    signal.signal(signal.SIGUSR2, sigusr2_handler)

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(PIN, GPIO.RISING, callback=button_callback, bouncetime=200)

    while True:
        signal.pause()

def fetch_ard(program):
    feed = feedparser.parse(program['rss'])

    res = re.search(r'\| ([0-9]+) Min. \|', feed['entries'][0]['summary'])
    if res:
        duration = res.group(1)
    else:
        duration = -1

    res = re.search(r'([0-9]+)$', feed['entries'][0]['link'])
    if not res:
        return None

    document_id = res.group(1)

    url = 'http://www.ardmediathek.de/play/media/{}?devicetype=pc&features'.format(document_id)
    res = requests.get(url)
    if not res.ok:
        return None

    video_url = res.json()['_mediaArray'][-1]['_mediaStreamArray'][-1]['_stream'][-1]
    video_name = '{}_{}'.format(program['short'], document_id)

    filename = download_file(video_name, video_url, True)
    if not filename:
        return None

    return {
        'video': filename,
        'published': feed['entries'][0]['published'],
        'duration': duration
    }

def fetch_zdf(program):
    return None

def fetch(notify=True):
    available_programmes = []

    for program_id, program in enumerate(programmes):
        if program['provider'] == 'ard':
            entry = fetch_ard(program)
        else:
            entry = fetch_zdf(program)

        print(entry)

        if entry:
            entry['program_id'] = program_id
            available_programmes.append(entry)

    with open(epg_path, 'w') as file:
        json.dump(available_programmes, file)

    if notify:
        os.system('killall -SIGUSR2 int_1.py')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'fetch':
        fetch()
    else:
        main()
