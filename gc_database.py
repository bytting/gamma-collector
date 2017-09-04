# Detector controller for gamma measurements
# Copyright (C) 2016  Norwegain Radiation Protection Authority
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Dag Robole,

import os, json, sqlite3
from gc_exceptions import ProtocolError
from twisted.python import log

_db_create_table_session = '''
CREATE TABLE `session` (
	`id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`name` TEXT NOT NULL UNIQUE,
	`ip` TEXT NOT NULL,
	`comment` TEXT,
	`livetime` REAL NOT NULL,
	`detector_data` TEXT NOT NULL
);
'''

_db_create_table_spectrum = '''
CREATE TABLE `spectrum` (
	`id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`session_id` INTEGER NOT NULL,
	`session_name` TEXT NOT NULL,
	`session_index` INTEGER NOT NULL UNIQUE,
	`start_time` TEXT NOT NULL,
	`latitude` REAL NOT NULL,
	`latitude_error` REAL NOT NULL,
	`longitude` REAL NOT NULL,
	`longitude_error` REAL NOT NULL,
	`altitude` REAL NOT NULL,
	`altitude_error` REAL NOT NULL,
	`track` REAL NOT NULL,
	`track_error` REAL NOT NULL,
	`speed` REAL NOT NULL,
	`speed_error` REAL NOT NULL,
	`climb` REAL NOT NULL,
	`climb_error` REAL NOT NULL,
	`livetime` REAL NOT NULL,
	`realtime` REAL NOT NULL,
	`total_count` INTEGER NOT NULL,
	`num_channels` INTEGER NOT NULL,
	`channels` TEXT NOT NULL
);
'''

def create(detector_data, msg):
    dbpath = os.path.expanduser("~/gc/")
    if not os.path.isdir(dbpath):
        os.makedirs(dbpath)
    dbpath += msg["session_name"] + ".db"
    connection = sqlite3.connect(dbpath)
    cursor = connection.cursor()
    cursor.execute(_db_create_table_session)
    cursor.execute(_db_create_table_spectrum)
    cursor.execute("insert into session (name, ip, comment, livetime, detector_data) values (?, ?, ?, ?, ?)",
           (msg['session_name'], msg['ip'], msg['comment'], msg['livetime'], json.dumps(detector_data)))
    connection.commit()
    return connection

def close(connection):
    if connection is not None:
        connection.close()

def insertSpectrum(connection, spec):
    if connection is None:
        return
    cursor = connection.cursor()
    cursor.execute("select id from session where name=?", (spec['session_name'], ))
    row = cursor.fetchone()
    cursor.execute("insert into spectrum (session_id, session_name, session_index, start_time, latitude, latitude_error, longitude, longitude_error, altitude, altitude_error, track, track_error, speed, speed_error, climb, climb_error, livetime, realtime, total_count, num_channels, channels) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
           (int(row[0]), spec['session_name'], spec['index'], spec['time'],
               spec['latitude'], spec['latitude_error'], spec['longitude'], spec['longitude_error'],
               spec['altitude'], spec['altitude_error'], spec['track'], spec['track_error'],
               spec['speed'], spec['speed_error'], spec['climb'], spec['climb_error'],
               spec['livetime'], spec['realtime'], spec['total_count'], spec['num_channels'], spec['channels']))
    connection.commit()

def getSyncSpectrums(session_name, indices_list, last_index):
    dbpath = os.path.expanduser("~/gc/")
    if not os.path.isdir(dbpath):
        os.makedirs(dbpath)
    dbpath += session_name + ".db"
    if not os.path.isfile(dbpath):
        raise ProtocolError('error', "Session database not found")
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()
    cur.execute("select * from spectrum where session_index in ({seq}) or session_index > {last}".format(seq=','.join(map(str, indices_list)), last=last_index))
    res = cur.fetchall()
    conn.close()
    return res
