#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

"""
multimedia: YouTube

 Copyright (C) 2021 Etienne Fieg

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import threading
import youtube_dl
from flask import Flask, render_template_string, request, current_app

from . import module, registry, streamer, utils

app = Flask(__name__)
search_page = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>YouTube Home</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
    <style>
      html {
        background-color: #000000;
      }

      body {
        background-color: #000000;
      }

      .input-text {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
      }
      
      input {
        font-size: 40px;
        font-family: "HelveticaNeue-Light", sans-serif;
        font-weight: 600;
        padding: 10px;
        border-style: none;
      }

      .button {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
      }

      .fa-youtube {
        color: #FF0000;
        border-style: none;
        background-color: #000000;
      }

      .fa-check-circle {
        color: #33ffd4;
      }

      .fa-times-circle {
        color: #FF0000;
      }

      .fa-spinner {
        color: #e56c27;
        animation: rotation 1s infinite linear;
      }

      @keyframes rotation {
        from {
          transform: rotate(0deg);
        }

        to {
          transform: rotate(359deg);
        }
      }
    </style>
  </head>
  <body>
    <div class="input-text">
      <input type="text" name="youtube_url" id="youtube_url" placeholder="YouTube URL">
    </div>
    <div class="input-text">
      <input type="text" name="start_time" id="start_time" placeholder="Start time mm:ss">
    </div>
    <div class="button">
      <button class="fab fa-youtube" onclick="play()" style="font-size:100px;"></button>
    </div>
    <p id="check_icon" style="text-align: center"></p>
    <script>
      function play() {
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
          if (this.readyState == 4) {
            if (this.status == 200) {
              document.getElementById('check_icon').innerHTML = '<div class="far fa-check-circle" style="font-size: 100px;"> </div>';
            } else {
              document.getElementById('check_icon').innerHTML = '<div class="far fa-times-circle" style="font-size: 100px;"> </div>';
            }
          } else {
            document.getElementById('check_icon').innerHTML = '<div class="fas fa-spinner" style="font-size: 100px;"> </div>';
          }
        };
        xhr.open('POST', '/data', true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        var youtubeUrl = document.getElementById('youtube_url').value;
        var timeSplit = document.getElementById('start_time').value.split(':');
        var startTime = parseInt(timeSplit[0]) * 60 + parseInt(timeSplit[1]);
        var data = 'youtube_url=' + encodeURIComponent(youtubeUrl) + '&start_time=' + startTime;
        xhr.send(data);
      }
    </script>
  </body>
</html>"""


def start(yt_module):
    app.config["yt_module"] = yt_module
    app.run(host='0.0.0.0', port=4999)


@app.route('/')
def index():
    return render_template_string(search_page)


@app.route('/data', methods=["POST"])
def data():
    youtube_url = request.form['youtube_url']
    start_time = request.form['start_time']

    ydl = youtube_dl.YoutubeDL()
    try:
        with ydl:
            res = ydl.extract_info(youtube_url, download=False)
            formats = [
                f for f in res['formats']
                if f['vcodec'].startswith('avc1') and int(f['format_note'].replace('p', '')) <= 1080
            ]
            formats.sort(key=lambda f: f['format_note'])
            media_url = formats[-1]['url']
    except youtube_dl.utils.DownloadError:
        return 'failed', 400

    registry.module_self_activate(current_app.config["yt_module"])
    streamer.play(url=media_url, start_time=start_time)

    return 'success'


class YouTube(module.Module):
    ID = 'youtube'
    TITLE = 'YouTube'
    SUBTITLE = 'http://{}:4999'.format(utils.get_primary_ip())
    PICON_URL = 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/YouTube_Logo_2017.svg/320px-YouTube_Logo_2017.svg.png'

    def __init__(self):
        self.webserver = threading.Thread(target=start, args=[self])
        self.webserver.setDaemon(True)
        self.webserver.start()

    def on_visible(self):
        self.log('on_visible')

    def on_exit(self):
        self.log('on_exit')

        if streamer.is_playing():
            streamer.stop()

        registry.module_finished()

    def on_terminate(self):
        self.log('on_terminate')
        streamer.stop()


if __name__ != '__main__':
    YouTube.register()
