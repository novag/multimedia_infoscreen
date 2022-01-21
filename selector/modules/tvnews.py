#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

"""
multimedia: ARD/ZDF tv news streams

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

from . import module, registry, streamer, utils


PROGRAMS = [
    {
        'name': 'Tagesschau in 100 Sekunden',
        'short': 'tagesschau100',
        'rss': 'https://www.tagesschau.de/export/video-podcast/webxl/tagesschau-in-100-sekunden_https/',
        'picon': 'https://img.ardmediathek.de/standard/00/52/14/95/00/-1774185891/16x9/704?mandant=ard',
        'provider': 'ard'
    },
    {
        'name': 'Tagesthemen',
        'short': 'tagesthemen',
        'rss': 'https://www.tagesschau.de/export/video-podcast/webxl/tagesthemen_https/',
        'picon': 'https://img.ardmediathek.de/standard/00/00/00/39/22/67648717/16x9/704?mandant=ard',
        'provider': 'ard'
    },
    {
        'name': 'Tagesschau',
        'short': 'tagesschau',
        'url': 'https://www.tagesschau.de/sendung/letzte-sendung/index.html',
        'picon': 'https://img.ardmediathek.de/standard/00/07/64/05/74/2121327408/16x9/384?mandant=ard',
        'provider': 'tagesschau'
    },
    {
        'name': 'heute Xpress',
        'short': 'heutexpress',
        'url': 'https://www.zdf.de/nachrichten/heute-sendungen/videos/heute-xpress-aktuelle-sendung-100.html',
        'picon': 'https://www.zdf.de/assets/der-schnelle-nachrichtenueberblick-heute-xpress-100~768x432?cb=1507802000508',
        'provider': 'zdf'
    },
    {
        'name': 'heute journal',
        'short': 'heutejournal',
        'url': 'https://www.zdf.de/nachrichten/heute-journal',
        'picon': 'https://img.selocon.com/media/resources/slotPreview/previewBig498_14d7af2a83b.jpg',
        'provider': 'zdf'
    }
]
EPG_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tmp_epg.tvnews.json')


class TVNews(module.Module):
    ID = 'tvnews'
    TITLE = 'title'
    PICON_URL = 'https://img.ardmediathek.de/standard/00/31/33/22/50/-2114473875/16x9/320?mandant=ard'

    def __init__(self):
        self.epg_data = []
        self.entries_length = 0
        self.selection_id = None

    def update(self):
        entries = []

        for epg_program in self.epg_data:
            program = PROGRAMS[epg_program['program_id']]
            date = datetime.fromtimestamp(epg_program['published'])

            entries.append({
                'title': program['name'],
                'picon': utils.prefix_tmp(program['short']),
                'subtitle': '{} - {} min'.format(date.strftime("%d.%m.%Y, %H:%M"), epg_program['duration'])
            })

        self.entries_length = len(entries)

        if entries:
            self.selection_id = 0
            utils.ib_update_selection(self.selection_id)

        utils.ib_update_selector(entries)

    def on_visible(self):
        self.log('on_visible')

        self.update()
        utils.ib_notify('infoscreen/selector/visible', 'true')

    def get_entries(self):
        self.log('get_entries')

        entries = []
        for epg_program in self.epg_data:
            program = PROGRAMS[epg_program['program_id']]

            entries.append({
                'id': program['short'],
                'title': program['name']
            })

        return entries

    def on_up(self):
        self.log('on_up')

        self.selection_id = (self.selection_id - 1) % self.entries_length
        utils.ib_update_selection(self.selection_id)

    def on_down(self):
        self.log('on_down')

        self.selection_id = (self.selection_id + 1) % self.entries_length
        utils.ib_update_selection(self.selection_id)

    def on_select(self, selection_id=None):
        self.log('on_select')

        if not selection_id:
            selection_id = self.selection_id

        streamer.play(self.epg_data[selection_id]['video'], self.stream_finished, False, True)

    def on_exit(self):
        self.log('on_exit')

        if streamer.is_playing():
            streamer.stop()
        self.stream_finished()

    def refresh(self):
        for program in PROGRAMS:
            utils.download_file(utils.prefix_tmp(program['short']), program['picon'])

        if not os.path.isfile(EPG_PATH):
            DataLoader().fetch(False)

        with open(EPG_PATH) as file:
            self.epg_data = json.load(file)

        registry.set_ready()

    def stream_finished(self):
        self.selection_id = None
        registry.module_finished()

    def on_terminate(self):
        self.log('on_terminate')

        streamer.stop()
        self.selection_id = None


class DataLoader:
    def fetch_tagesschau(self, program):
        res = requests.get(program['url'])
        if not res.ok:
            return None
        data = res.text

        res = re.search('multimediahead__date">([0-9]{2}\.[0-9]{2}\.[0-9]{4}\s[0-9]{1,2}:[0-9]{2})', data)
        if not res:
            return None
        published = datetime.strptime(res.group(1), '%d.%m.%Y %H:%M')

        res = re.search('(https://adaptive\.tagesschau\.de/i/video/.+?)&quot;', data)
        if not res:
            return None
        video_url = res.group(1).replace()

        return {
            'video': video_url,
            'published': published.timestamp(),
            'duration': ''
        }

    def fetch_ard(self, program):
        feed = feedparser.parse(program['rss'])
        first_entry = feed['entries'][0]

        video_url = first_entry['links'][0]['href']
        duration = first_entry['itunes_duration'].split(':', 1)[1]
        published = first_entry['published']
        published = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")

        return {
            'video': video_url,
            'published': published.timestamp(),
            'duration': duration
        }

    def fetch_zdf(self, program):
        res = requests.get(program['url'])
        if not res.ok:
            return None
        data = res.text

        res = re.search(r'content": "(.*)"', data)
        if not res:
            return None
        content_url = res.group(1)

        res = re.search(r'apiToken": "(.*)"', data)
        if not res:
            return None
        headers = {
            'Api-Auth': 'Bearer {}'.format(res.group(1))
        }

        res = requests.get(content_url, headers=headers)
        if not res.ok:
            return None
        data = res.json()

        hjo_url = data['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd-template']
        hjo_url = hjo_url.replace('{playerId}', 'ngplayer_2_3')
        published = data['editorialDate']

        res = requests.get('https://api.zdf.de{}'.format(hjo_url), headers=headers)
        if not res.ok:
            return None
        data = res.json()

        video_url = data['priorityList'][1]['formitaeten'][0]['qualities'][0]['audio']['tracks'][0]['uri']
        duration = data['attributes']['duration']['value']

        return {
            'video': video_url,
            'published': datetime.strptime(published[:-3] + published[-2:], "%Y-%m-%dT%H:%M:%S.%f%z").timestamp(),
            'duration': round(duration / 61000)
        }

    def fetch(self, notify=True):
        available_programmes = []

        for program_id, program in enumerate(PROGRAMS):
            provider = program['provider']

            if provider == 'tagesschau':
                entry = self.fetch_tagesschau(program)
            elif provider == 'ard':
                entry = self.fetch_ard(program)
            elif provider == 'zdf':
                entry = self.fetch_zdf(program)
            else:
                print('Unknown provider: ' + provider)
                continue

            print(entry)

            if entry:
                entry['program_id'] = program_id
                available_programmes.append(entry)

        with open(EPG_PATH, 'w') as file:
            json.dump(available_programmes, file)

        if notify:
            os.system('pkill -SIGUSR2 -f selector/service')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'fetch':
        DataLoader().fetch()
else:
    TVNews.register()
