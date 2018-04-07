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

gl.setup(870, 979)

node.alias("departures")

json = require "json"

util.auto_loader(_G)

local FSIZE_MESSAGE = 45
local FSIZE_DEPARTURE = 60
local FSIZE_DEPARTURE_LARGE = 70

local base_time = N.base_time or 0
local data = N.data or {departures={}, messages={}}

util.data_mapper{
    ["clock/set"] = function(time)
        base_time = tonumber(time) - sys.now()
        N.base_time = base_time
    end;

    ["update"] = function()
        schedule.update()
    end;
}

node.event("input", function(line, client)
    data = json.decode(line)
    N.data = data
    print("departures data update")

    schedule.update()
end)

function unixnow()
    return base_time + sys.now()
end

function draw_messages()
    local y = 0

    for idx, msg in ipairs(data.messages) do
        util.draw_correct(_G["alert"], 10, y, 140, y + FSIZE_MESSAGE, 0.9)
        font:write(150, y, msg, FSIZE_MESSAGE, 0, 0, 0, 1)

        y = y + 60
        if y > HEIGHT - 60 then
            break
        end
    end

    return y
end

function draw_departures(msg_y, now)
    local y = 30 + msg_y
    local now = unixnow()
    local lcount = 0

    for idx, dep in ipairs(data.departures) do
        if dep.timestamp > now then
            local time = dep.nice_date
            local remaining = math.floor((dep.timestamp - now) / 60)
            local append = ""

            if remaining < 0 then
                time = "gone"
            elseif remaining < 1 then
                time = "now"
                append = dep.nice_date
            elseif remaining < 5 or lcount < 2 then
                time = string.format("%d min", ((dep.timestamp - now) / 60))
                append = dep.nice_date
            end

            if remaining < 5 or lcount < 2 then
                lcount = lcount + 1
                util.draw_correct(_G[dep.icon], 10, y, 140, y + FSIZE_DEPARTURE, 0.9)
                font:write(150, y, "› " .. dep.destination, FSIZE_DEPARTURE_LARGE, 0, 0, 0, 1)
                y = y + FSIZE_DEPARTURE_LARGE + 5
                font:write(150, y, time .. " / " .. append, FSIZE_DEPARTURE, 0, 0, 0, 1)
                y = y + FSIZE_DEPARTURE_LARGE + 5
            else
                util.draw_correct(_G[dep.icon], 10, y, 140, y + FSIZE_DEPARTURE, 0.9)
                font:write(150, y, time, FSIZE_DEPARTURE, 0, 0, 0, 1)
                font:write(300, y, dep.destination, FSIZE_DEPARTURE, 0, 0, 0, 1)
                y = y + FSIZE_DEPARTURE_LARGE + 5
            end

            if y > HEIGHT - 60 then
                break
            end
        end
    end
end

function make_schedule()
    local frame1
    local updater

    local function update_func()
        print("updating!")
        gl.clear(0, 0, 0, 0)
        local y = draw_messages()
        draw_departures(y, now)
        frame1 = resource.create_snapshot()
    end

    local function update()
        updater = coroutine.wrap(update_func)
    end

    local function draw()
        if updater then
            updater()
            updater = nil
        end
        gl.clear(0, 0, 0, 0)
        if frame1 then
            frame1:draw(0, 0, WIDTH, HEIGHT, 1)
        end
    end

    return {
        draw = draw;
        update = update;
    }
end

schedule = make_schedule()
util.set_interval(15, schedule.update)

function node.render()
    schedule.draw()
end
