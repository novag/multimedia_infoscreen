#!/usr/bin/python3 -u

"""
multimedia/infoscreen: fetch spotify track information and display it

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

import base64
import json
import os
import re
import requests
import socket
import time
from systemd import journal

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
with open(config_path) as f:
    config = json.load(f)
    spotify_client_id = config['spotify']['client_id']
    spotify_client_secret = config['spotify']['client_secret']
    spotify_b64_auth = base64.b64encode('{}:{}'.format(spotify_client_id, spotify_client_secret).encode()).decode("utf-8")

event = os.environ['PLAYER_EVENT']
track_id = os.environ['TRACK_ID']
if event == 'change':
    old_track_id = os.environ['OLD_TRACK_ID']

def clear_cache():
    if event == 'change':
        path = '{}/tmp_{}.jpeg'.format(os.path.dirname(os.path.realpath(__file__)), old_track_id)
    else:
        path = '{}/tmp_{}.jpeg'.format(os.path.dirname(os.path.realpath(__file__)), track_id)

    try:
        os.remove(path)
    except OSError:
        pass

def fetch_track():
    j = journal.Reader()
    j.log_level(journal.LOG_INFO)
    j.add_match(_SYSTEMD_UNIT="raspotify.service")
    j.seek_tail()

    uri = ''
    while uri == '':
        msg = j.get_previous()['MESSAGE']
        res = re.search(r'spotify:track:([a-zA-Z0-9]+)', msg, re.M | re.I)
        if res:
            uri = res.group(1)

    headers = {
        'Authorization': 'Basic ' + spotify_b64_auth
    }
    payload = {
        'grant_type': 'client_credentials'
    }
    token = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=payload).json()['access_token']

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    track = requests.get('https://api.spotify.com/v1/tracks/' + uri, headers=headers).json()

    title = track['name']
    artists = ', '.join([artist['name'] for artist in track['artists']])
    image_url = track['album']['images'][0]['url'] if len(track['album']['images']) > 0 else None

    image = 'null'
    if image_url:
        image = 'tmp_{}'.format(track_id)
        res = requests.get(image_url, stream=True)
        if res.status_code == 200:
            with open('{}/{}.jpeg'.format(os.path.dirname(os.path.realpath(__file__)), image), 'wb') as f:
                for chunk in res:
                    f.write(chunk)

    udp.sendto('infoscreen/music/title:{}'.format(title).encode(), ('127.0.0.1', 4444))
    udp.sendto('infoscreen/music/artists:{}'.format(artists).encode(), ('127.0.0.1', 4444))
    udp.sendto('infoscreen/music/image:{}'.format(image).encode(), ('127.0.0.1', 4444))

if event == 'start':
    os.system('killall -SIGUSR1 radio.py')
    fetch_track()
    udp.sendto('infoscreen/music/playing:true'.encode(), ('127.0.0.1', 4444))
elif event == 'stop':
    udp.sendto('infoscreen/music/playing:false'.encode(), ('127.0.0.1', 4444))
    time.sleep(0.25)
    clear_cache()
elif event == 'change':
    fetch_track()
    udp.sendto('infoscreen/music/playing:true'.encode(), ('127.0.0.1', 4444))
    time.sleep(0.25)
    clear_cache()
