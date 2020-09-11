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

from . import module, registry, utils


class Selector(module.Module):
    ID = 'selector'
    TITLE = 'Selector'
    PICON_URL = None

    def __init__(self):
        self.modules = []
        self.selection_id = None

    def on_visible(self):
        self.log('on_visible')

        self.selection_id = 0
        self.modules = registry.get_all_metadata()

        utils.ib_update_selection(self.selection_id)
        utils.ib_update_selector(self.modules)
        utils.ib_notify('infoscreen/selector/visible', 'true')

    def get_entries(self):
        return [
            {
                'id': module['id'],
                'title': module['title']
            }
            for module in registry.get_all_metadata()
        ]

    def on_up(self):
        self.log('up')

        self.selection_id = (self.selection_id - 1) % len(self.modules)
        utils.ib_update_selection(self.selection_id)

    def on_down(self):
        self.log('down')

        self.selection_id = (self.selection_id + 1) % len(self.modules)
        utils.ib_update_selection(self.selection_id)

    def on_select(self, selection_id=None):
        self.log('select')

        if not selection_id:
            selection_id = self.selection_id

        return registry.get_all_modules()[selection_id]

    def on_exit(self):
        self.log('on_exit')

    def on_terminate(self):
        self.log('terminate')

        self.selection_id = None


registry.register_selector(Selector())
