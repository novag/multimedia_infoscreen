#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

"""
multimedia: ARD/ZDF live streams

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

import feedparser
import json
import os
import re
import requests
import sys
from datetime import datetime


CHANNELS = [
    {
        'name': 'Das Erste HD',
        'short': 'daserste',
        'stream': 'https://mcdn.daserste.de/daserste/de/master.m3u8',
        'hls': True,
        'picon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Das_Erste_2014.svg/320px-Das_Erste_2014.svg.png'
    },
    {
        'name': 'ZDF HD',
        'short': 'zdf',
        'stream': 'https://zdf-hls-15.akamaized.net/hls/live/2016498/de/high/master.m3u8',
        'hls': True,
        'picon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/ZDF_logo.svg/320px-ZDF_logo.svg.png'
    }
]


class TVStreams():
    def __init__(self):
        self.epg_data = []
        self.entries = []
        self.selection_id = None

        for channel in CHANNELS:
            self.entries.append({
                'title': channel['name'],
                'picon': utils.prefix_tmp(channel['short']),
                'subtitle': ''
            })

    def update(self):
        if self.entries:
            self.selection_id = 0
            utils.ib_update_selection(self.selection_id)

        utils.ib_update_selector(self.entries)

    def init(self):
        print('tvstreams: init.')

        self.update()
        utils.ib_notify('infoscreen/selector/visible', 'true')

    def get_entries(self):
        entries = []

        for channel in CHANNELS:
            entries.append({
                'id': channel['short'],
                'title': channel['name']
            })

        return entries

    def up(self):
        print('tvstreams: up.')

        self.selection_id = (self.selection_id - 1) % len(self.entries)
        utils.ib_update_selection(self.selection_id)

    def down(self):
        print('tvstreams: down.')

        self.selection_id = (self.selection_id + 1) % len(self.entries)
        utils.ib_update_selection(self.selection_id)

    def select(self, selection_id=None):
        print('tvstreams: select.')

        if not selection_id:
            selection_id = self.selection_id

        channel = CHANNELS[selection_id]

        streamer.play(channel['stream'], self.stream_finished, channel['hls'])

    def exit(self):
        print('tvnews: exit.')

        if streamer.is_playing():
            streamer.stop()
        self.stream_finished()

    def refresh(self):
        for channel in CHANNELS:
            utils.download_file(utils.prefix_tmp(channel['short']), channel['picon'])

        registry.set_ready()

    def stream_finished(self):
        self.selection_id = None
        registry.module_finished()

    def terminate(self):
        print('bye.')

        streamer.stop()
        self.selection_id = None

if __name__ != '__main__':
    from . import registry, streamer, utils

    registry.register(TVStreams(), {
        'id': 'tvstreams',
        'title': 'Live TV',
        'subtitle': '',
        'picon': 'tvstreams',
        'picon_url': 'https://cdn1.vectorstock.com/i/1000x1000/02/90/tv-icon-vector-13820290.jpg'
    })
