#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

"""
multimedia: List Modules

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
from . import registry, streamer, utils


class Selector():
    def __init__(self):
        self.modules = []
        self.selection_id = None

    def init(self):
        print('selector: init.')

        self.selection_id = 0
        self.modules = registry.get_all_metadata()

        utils.ib_update_selection(self.selection_id)
        utils.ib_update_selector(self.modules)
        utils.ib_notify('infoscreen/selector/visible', 'true')

    def get_entries(self):
        entries = []

        for module in registry.get_all_metadata():
            entries.append({
                'id': module['id'],
                'title': module['title']
            })

        return entries

    def up(self):
        print('selector: up.')

        self.selection_id = (self.selection_id - 1) % len(self.modules)
        utils.ib_update_selection(self.selection_id)

    def down(self):
        print('selector: down.')

        self.selection_id = (self.selection_id + 1) % len(self.modules)
        utils.ib_update_selection(self.selection_id)

    def select(self, selection_id=None):
        print('selector: select.')

        if not selection_id:
            selection_id = self.selection_id

        return registry.get_all_modules()[selection_id]

    def exit(self):
        print('selector: exit.')

        pass

    def refresh(self):
        pass

    def terminate(self):
        print('bye.')

        self.selection_id = None

registry.register_selector(Selector())