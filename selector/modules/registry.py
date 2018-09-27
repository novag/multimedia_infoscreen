#!/usr/bin/python3 -u

"""
multimedia: module registry

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


_dispatcher = None
_modules = []
_metadata = []
_ready_count = 0

def register_dispatcher(d):
    global _dispatcher

    _dispatcher = d

def register(module, meta):
    _modules.append(module)
    _metadata.append(meta)

def set_ready():
    global _ready_count

    _ready_count += 1

def ready():
    return _ready_count >= len(_modules)

def module_finished():
    _dispatcher.reset()

def get_all_modules():
    return _modules

def get_all_metadata():
    return _metadata

def get_length():
    return len(_modules)