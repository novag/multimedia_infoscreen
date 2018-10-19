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
        'stream': 'https://daserstehdde-lh.akamaihd.net/i/daserstehd_de@629196/index_3776_av-p.m3u8?sd=10&rebase=on',
        'picon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Das_Erste_2014.svg/320px-Das_Erste_2014.svg.png'
    },
    {
        'name': 'ZDF HD',
        'short': 'zdf',
        'stream': 'https://zdf1314-lh.akamaihd.net/i/de14_v1@392878/index_3096_av-b.m3u8?sd=10&rebase=on',
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
                'picon': channel['short'],
                'subtitle': ''
            })

    def update(self):
        if self.entries:
            self.selection_id = 0
            utils.ib_update_selection(self.selection_id)

        utils.ib_update_selector(self.entries)

    def handle_short_press(self):
        print('short press.')

        if streamer.is_playing():
            streamer.stop()
        elif self.selection_id == None:
            self.update()

            utils.ib_notify('infoscreen/selector/visible', 'true')
        else:
            self.selection_id = (self.selection_id + 1) % len(self.entries)
            utils.ib_update_selection(self.selection_id)

    def handle_long_press(self):
        print('long press.')

        if not streamer.is_playing() and self.selection_id != None:
            streamer.play(CHANNELS[self.selection_id]['stream'], self.stream_finished)

    def reload_epg(self):
        for channel in CHANNELS:
            utils.download_file(channel['short'], channel['picon'])

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
        'title': 'Live TV',
        'subtitle': '',
        'picon': 'tvstreams',
        'picon_url': 'https://cdn1.vectorstock.com/i/1000x1000/02/90/tv-icon-vector-13820290.jpg'
    })
