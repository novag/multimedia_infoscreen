-- Copyright (C) 2018 Hendrik Hagendorn

-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.

-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.

-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.

gl.setup(NATIVE_WIDTH, NATIVE_HEIGHT)

node.alias("infoscreen")

json = require "json"

util.auto_loader(_G)

local SIDEBAR_WIDTH = 400

local data = N.data or {news={}}

node.event("input", function(line, client)
    data = json.decode(line)
    N.data = data
    print("sidebar data update")
end)

function wrap(str, limit, indent, indent1)
    limit = limit or 72
    local here = 1
    local wrapped = str:gsub("(%s+)()(%S+)()", function(sp, st, word, fi)
        if fi-here > limit then
            here = st
            return "\n"..word
        end
    end)

    local splitted = {}
    for token in string.gmatch(wrapped, "[^\n]+") do
        splitted[#splitted + 1] = token
    end

    return splitted
end

function easeInOut(t, b, c)
    c = c - b
    return -c * math.cos(t * (math.pi / 2)) + c + b;
end

Time = (function()
    local base_time = 0 - sys.now()
    local midnight

    local function unixtime()
        return base_time + sys.now()
    end

    local function walltime()
        if not midnight then
            return 0, 0
        else
            local time = (midnight + sys.now()) % 86400
            return math.floor(time / 3600), math.floor(time % 3600 / 60)
        end
    end

    util.data_mapper{
        ["clock/unix"] = function(time)
            print("new time: ", time)
            base_time = tonumber(time) - sys.now()
        end;
        ["clock/midnight"] = function(since_midnight)
            print("new midnight: ", since_midnight)
            midnight = tonumber(since_midnight) - sys.now()
        end;
    }

    return {
        unixtime = unixtime;
        walltime = walltime;
    }
end)()

Music = (function()
    local mPlaying = false
    local mTitle = ""
    local mArtists = ""
    local mImage = "null"

    local function playing()
        return mPlaying
    end

    local function title()
        return mTitle
    end

    local function artists()
        return mArtists
    end

    local function image()
        return mImage
    end

    util.data_mapper{
        ["music/playing"] = function(playing)
            print("music playing: ", playing)
            if playing == "true" then
                mPlaying = true
            else
                mPlaying = false
            end
        end;
        ["music/title"] = function(title)
            print("new music title: ", title)
            mTitle = title
        end;
        ["music/artists"] = function(artists)
            print("new music artists: ", artists)
            mArtists = artists
        end;
        ["music/image"] = function(image)
            print("new music image: ", image)
            mImage = image
        end;
    }

    return {
        playing = playing;
        title = title;
        artists = artists;
        image = image;
    }
end)()

Weather = (function()
    local wTemp_low = "0 °C"
    local wTemp_high = "0 °C"
    local wTemp_current = "0 °C"
    local wIcon = "sunny"
    local wSunrise = "00:00"
    local wSunset = "00:00"

    local function low_temperature()
        return wTemp_low
    end

    local function high_temperature()
        return wTemp_high
    end

    local function current_temperature()
        return wTemp_current
    end

    local function icon()
        return wIcon
    end

    local function sunrise()
        return wSunrise
    end

    local function sunset()
        return wSunset
    end

    util.data_mapper{
        ["weather/icon"] = function(icon)
            print("weather: new icon: ", icon)
            wIcon = icon
        end;
        ["weather/temp_low"] = function(temp)
            print("weather: new low temperature: ", temp)
            wTemp_low = temp
        end;
        ["weather/temp_high"] = function(temp)
            print("weather: new high temperature: ", temp)
            wTemp_high = temp
        end;
        ["weather/temp_current"] = function(temp)
            print("weather: new current temperature: ", temp)
            wTemp_current = temp
        end;
        ["weather/sunrise"] = function(sunrise)
            print("weather: new sunrise: ", sunrise)
            wSunrise = sunrise
        end;
        ["weather/sunset"] = function(sunset)
            print("weather: new sunset: ", sunset)
            wSunset = sunset
        end;
    }

    return {
        low_temperature = low_temperature;
        high_temperature = high_temperature;
        current_temperature = current_temperature;
        icon = icon;
        sunrise = sunrise;
        sunset = sunset;
    }
end)()

Sidebar = (function()
    local visibility = 0
    local target = 0
    local restore = sys.now() + 1

    local white = resource.create_colored_texture(0, 0, 0, 1)

    local function hide(duration)
        target = 0
        restore = sys.now() + duration
    end

    util.data_mapper{
        ["sidebar/hide"] = function(t)
            hide(tonumber(t))
        end;
    }

    local function draw_news()
        local y = 500
        local max_lines = 3

        for idx, entry in ipairs(data.news) do
            if idx > 3 then
                break
            end

            local published_width = _G["font"]:width(entry.published, 30)
            _G["font"]:write(15, y, entry.published, 30, 0, 0, 0, 1)

            for idx, line in ipairs(wrap(entry.title, 27)) do
                if idx > max_lines then
                    break
                end

                if idx == 3 then
                    max_lines = 2
                end

                if idx > 1 then
                    y = y + 40
                end

                if entry.today then
                    _G["font"]:write(15 + published_width + 15, y, line, 35, 0, 0, 0, 1)
                else
                    _G["font"]:write(15 + published_width + 15, y, line, 35, 0, 0, 0, 0.8)
                    if idx == 2 then
                        local relative_width = _G["font"]:width(entry.relative, 20)
                        _G["font"]:write(15 + (published_width - relative_width) / 2, y - 10, entry.relative, 20, 0, 0, 0, 1)
                    end
                end
            end

            y = y + 50
        end
    end

    local function draw()
        local max_rotate = 130
        if visibility > 0.01 then
            gl.pushMatrix()
            gl.translate(WIDTH, 0)
            gl.rotate(max_rotate - visibility * max_rotate, 0, 1, 0) 
            gl.translate(-SIDEBAR_WIDTH, 0)
            white:draw(0, 0, SIDEBAR_WIDTH, HEIGHT, 0.2) --Fadeout.alpha()))

            -- music
            if Music.playing() then
                if Music.image() ~= "null" then
                    util.draw_correct(_G[Music.image()], 50, 20, SIDEBAR_WIDTH - 50, 200)
                end
                local title_width = _G["font"]:width(Music.title(), 50)
                _G["font"]:write((SIDEBAR_WIDTH - title_width) / 2, 210, Music.title(), 50, 0, 0, 0, 1)
                local artists_width = _G["font"]:width(Music.artists(), 40)
                _G["font"]:write((SIDEBAR_WIDTH - artists_width) / 2, 260, Music.artists(), 40, 0, 0, 0, 1)
            else
                util.draw_correct(_G[Weather.icon()], 50, 20, SIDEBAR_WIDTH - 50, 300)
            end

            -- weather
            _G["font"]:write(40, 320, Weather.low_temperature(), 70, 0, 0, 0, 1)
            local high_width = _G["font"]:width(Weather.high_temperature(), 70)
            _G["font"]:write(SIDEBAR_WIDTH - high_width - 40, 320, Weather.high_temperature(), 70, 0, 0, 0, 1)
            local current_width = _G["font"]:width(Weather.current_temperature(), 70)
            _G["font"]:write((SIDEBAR_WIDTH - current_width) / 2, 400, Weather.current_temperature(), 70, 0, 0, 0, 1)

            -- news
            draw_news()

            -- clock
            local hour, min = Time.walltime()
            local time = string.format("%d:%02d", hour, min)
            local time_width = _G["font"]:width(time, 100)
            _G["font"]:write((SIDEBAR_WIDTH - time_width) / 2, HEIGHT - 200, time, 100, 0, 0, 0, 1)

            -- sunrise / sunset
            util.draw_correct(_G["sunrise"], 15, HEIGHT - 84, 79, HEIGHT - 20, 1)
            _G["font"]:write(80, HEIGHT - 77, Weather.sunrise(), 50, 0, 0, 0, 1)
            local sunset_width = _G["font"]:width(Weather.sunset(), 50)
            util.draw_correct(_G["sunset"], SIDEBAR_WIDTH - 79, HEIGHT - 84, SIDEBAR_WIDTH - 15, HEIGHT - 20, 1)
            _G["font"]:write(SIDEBAR_WIDTH - sunset_width - 80, HEIGHT - 77, Weather.sunset(), 50, 0, 0, 0, 1)
            gl.popMatrix()
        end
    end

    local current_speed = 0
    local function tick()
        if sys.now() > restore then
            target = 1
        end

        local current_speed = 0.05
        visibility = visibility * (1 - current_speed) + target * (current_speed)

        draw()
    end

    return {
        tick = tick;
        hide = hide;
        width = SIDEBAR_WIDTH;
    }
end)()

VNC = (function()
    local vServer = ""
    local vVisible = false
    local sSession = nil

    local function visible()
        return vVisible
    end

    local function session()
        return sSession
    end

    util.data_mapper{
        ["vnc/server"] = function(server)
            print("vnc server: ", server)
            vServer = server
        end;
        ["vnc/visible"] = function(visible)
            print("vnc visible: ", visible)

            if visible == "true" then
                sSession = resource.create_vnc(vServer)
            else
                sSession = nil
            end

            vVisible = visible == "true"
        end;
    }

    return {
        visible = visible;
        session = session;
    }
end)()

OVERLAY = (function()
    local oVisible = false
    local oColor = "black"

    local function visible()
        return oVisible
    end

    local function color()
        return oColor
    end

    util.data_mapper{
        ["overlay/color"] = function(color)
            print("overlay color: ", color)
            oColor = color
        end;
        ["overlay/visible"] = function(visible)
            print("overlay visible: ", visible)
            oVisible = visible == "true"
        end;
    }

    return {
        visible = visible;
        color = color;
    }
end)()

SELECTOR = (function()
    local iVisible = false

    local function visible()
        return iVisible
    end

    util.data_mapper{
        ["selector/visible"] = function(visible)
            print("selector visible: ", visible)
            iVisible = visible == "true"
        end;
    }

    return {
        visible = visible;
    }
end)()

VIDEO = (function()
    local vVideo = nil
    local vVisible = false

    local function visible()
        return vVisible
    end

    local function video()
        return vVideo
    end

    util.data_mapper{
        ["video/file"] = function(file)
            print("video file: ", file)
            vVideo = resource.load_video{
                file = file;
                audio = true;
            }
        end;

        ["video/visible"] = function(visible)
            print("video visible: ", visible)
            vVisible = visible == "true"
        end;
    }

    return {
        visible = visible;
        video = video;
    }
end)()

function node.render()
    gl.clear(1, 1, 1, 1)

    if OVERLAY.visible() then
        gl.clear(0, 0, 0, 1)
    elseif SELECTOR.visible() then
        Sidebar.tick()

        resource.render_child("selector"):draw(10, 45, WIDTH - SIDEBAR_WIDTH, HEIGHT)
    elseif VNC.visible() then
        util.draw_correct(VNC.session(), 0, 0, WIDTH, HEIGHT)
    elseif VIDEO.visible() then
        Sidebar.tick()

        util.draw_correct(VIDEO.video(), 0, 0, WIDTH - SIDEBAR_WIDTH, HEIGHT)
    else
        Sidebar.tick()

        resource.render_child("muc-oepnv"):draw(10, 45, WIDTH - SIDEBAR_WIDTH, HEIGHT)
    end
end
