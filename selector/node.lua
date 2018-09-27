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

node.alias("selector")

json = require "json"

util.auto_loader(_G)

local FSIZE_MESSAGE = 45
local FSIZE_ENTRY = 60
local FSIZE_ENTRY_LARGE = 70

local base_time = N.base_time or 0
local selection_id = N.selection_id or 1
local data = N.data or {entries={}, messages={}}

util.data_mapper{
    ["clock/set"] = function(time)
        base_time = tonumber(time) - sys.now()
        N.base_time = base_time
    end;

    ["selection"] = function(selection)
        selection_id = tonumber(selection)
        N.selection_id = selection_id
        schedule.update()
    end;

    ["update"] = function()
        schedule.update()
    end;
}

node.event("input", function(line, client)
    data = json.decode(line)
    N.data = data
    print("data update")

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

function draw_entries(msg_y)
    local y = 30 + msg_y

    for idx, entry in ipairs(data.entries) do
        if idx == selection_id then
            title = "› " .. entry.title
        else
            title = entry.title
        end

        util.draw_correct(_G[entry.picon], 10, y + 10, 140, y + FSIZE_ENTRY, 0.9)
        font:write(150, y, title, FSIZE_ENTRY_LARGE, 0, 0, 0, 1)
        y = y + FSIZE_ENTRY_LARGE + 5
        font:write(150, y, entry.subtitle, FSIZE_ENTRY, 0, 0, 0, 1)
        y = y + FSIZE_ENTRY_LARGE + 5

        if y > HEIGHT - 60 then
            break
        end
    end
end

function make_list()
    local frame1
    local updater

    local function update_func()
        print("updating!")
        gl.clear(0, 0, 0, 0)
        local y = draw_messages()
        draw_entries(y)
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

schedule = make_list()
util.set_interval(15, schedule.update)

function node.render()
    schedule.draw()
end
