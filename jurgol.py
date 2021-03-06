from io import StringIO

import ipdb

import csv
import json
import os
import sys
import urllib.request

from carto.auth import APIKeyAuthClient
from carto.datasets import DatasetManager
from carto.sql import SQLClient


API_KEY = os.environ["CARTO_API_KEY"]
USERNAME = "aromeu"
USR_BASE_URL = "https://{user}.carto.com/".format(user=USERNAME)
auth_client = APIKeyAuthClient(api_key=API_KEY, base_url=USR_BASE_URL)

STADIUMS_FILE_NAME = "stadiums.csv"
TVCHANNELS_FILE_NAME = "tvchannels.csv"
TEAMS_FILE_NAME = "teams.csv"
MATCHES_FILE_NAME = "matches.csv"
MATCHES_POLYGONS_FILE_NAME = "matches_polygons.csv"

data_url = 'https://raw.githubusercontent.com/lsv/fifa-worldcup-2018/master/data.json'
response = urllib.request.urlopen(data_url)
data = response.read().decode('utf-8')
data_json = json.load(StringIO(data))

def write_csv(output_filename, fieldnames, obj_array):
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for obj in obj_array:
            yield(obj)
            writer.writerow(obj)

def global_path(filename):
    return "{path}/{filename}".format(path = os.getcwd(), filename = filename)

for obj in write_csv(STADIUMS_FILE_NAME, ['id', 'name', 'city', 'lat', 'lng', 'image'], data_json['stadiums']):
    continue

for obj in write_csv(TVCHANNELS_FILE_NAME, ['id', 'name', 'icon', 'country', 'iso2', 'lang'], data_json['tvchannels']):
    obj['lang'] = ' '.join(map(str, obj['lang'])).strip()

for obj in write_csv(TEAMS_FILE_NAME, ['id', 'name', 'fifaCode', 'iso2', 'flag', 'emoji', 'emojiString'], data_json['teams']):
    continue

matches = []
for group in data_json['groups']:
    # ipdb.set_trace(context=50)
    matches = matches + data_json['groups'][group]['matches']

for knockout in data_json['knockout']:
    matches = matches + data_json['knockout'][knockout]['matches']

for obj in matches:
    if not 'home_penalty' in obj or not obj['home_penalty']:
        obj['home_penalty'] = 0
    if not 'away_penalty' in obj or not obj['away_penalty']:
        obj['away_penalty'] = 0
    # ipdb.set_trace(context=50)
    if obj['home_result'] is not None and obj['away_result'] is not None:
        if obj['home_result'] + obj['home_penalty'] > obj['away_result'] + obj['away_penalty']:
            obj['win'] = obj['home_team']
            obj['los'] = obj['away_team']
        elif obj['home_result'] + obj['home_penalty'] < obj['away_result'] + obj['away_penalty']:
            obj['win'] = obj['away_team']
            obj['los'] = obj['home_team']
        # else:
        #     obj['win'] = obj['away_team']
        #     obj['los'] = obj['home_team']

matches_per_team = {}
qual = {}
knockout_matches = data_json['knockout']['round_16']['matches']
try:
    for obj in matches:
        w = str(obj['home_team'])
        l = str(obj['away_team'])
        if not w in matches_per_team:
            matches_per_team[w] = 0

        if not l in matches_per_team:
            matches_per_team[l] = 0

        matches_per_team[w] = matches_per_team[w] + 1
        matches_per_team[l] = matches_per_team[l] + 1

        if 'type' in obj and obj['type'] == 'qualified':
            qual[str(obj['winner'])] = True

        for kmatch in knockout_matches:
            qual[str(kmatch['home_team'])] = True
            qual[str(kmatch['away_team'])] = True

    matches_polygons = []

    count = {}
    opacity = {}
    for team in matches_per_team:
        count[team] = 0
        opacity[team] = 1

    # ipdb.set_trace(context=50)
    for obj in matches:
        win = obj.copy()
        los = obj.copy()

        if 'win' in win:
            ww = str(win['win'])
            if not ww in qual:
                opacity[ww] = opacity[ww] - round((1 / matches_per_team[ww]), 2)
                win['opacity'] = max(opacity[ww], 0)
                count[ww] = count[ww] + 1
            else:
                win['opacity'] = 1
        else:
            away = str(win['away_team'])

            ww = away
            if not away in qual:
                ww = away
                opacity[away] = opacity[away] - (1 / matches_per_team[away])
                win['opacity'] = max(opacity[away], 0)
                count[away] = count[away] + 1
            else:
                win['opacity'] = 1

        if count[ww] == matches_per_team[ww]:
            win['opacity'] = 0

        if 'los' in los:
            ll = str(los['los'])
            if not ll in qual:
                opacity[ll] = opacity[ll] - round((1 / matches_per_team[ll]), 2)
                los['opacity'] = max(opacity[ll], 0)
                count[ll] = count[ll] + 1
            else:
                los['opacity'] = 1
        else:
            home = str(los['home_team'])

            ll = home
            if not home in qual:
                ll = home
                opacity[home] = opacity[home] - (1 / matches_per_team[home])
                los['opacity'] = max(opacity[home], 0)
                count[home] = count[home] + 1
            else:
                los['opacity'] = 1

        if count[ll] == matches_per_team[ll]:
            los['opacity'] = 0

        if win['type'] == 'qualified':
            win['opacity'] = 1
            los['opacity'] = 0

        win['team'] = ww
        los['team'] = ll
        matches_polygons.append(win)
        matches_polygons.append(los)

        for team in opacity:
            if team != ww and team != ll:
                new_team = win.copy()
                new_team['opacity'] = opacity[team]
                new_team['team'] = team
                matches_polygons.append(new_team)

except KeyError as t:
    ipdb.set_trace(context=50)
    print(t)


fieldnames = ['name', 'type', 'home_team', 'away_team', 'home_result', 'away_result', 'date', 'stadium', 'channels', 'finished', 'win', 'los']
for obj in write_csv(MATCHES_FILE_NAME, fieldnames, matches):
    keys = list(obj.keys()).copy()
    for key in keys:
        if key not in fieldnames:
            del obj[key]
    obj['channels'] = ' '.join(map(str, obj['channels'])).strip()

fieldnames = ['date', 'opacity', 'team']
for obj in write_csv(MATCHES_POLYGONS_FILE_NAME, fieldnames, matches_polygons):
    keys = list(obj.keys()).copy()
    for key in keys:
        if key not in fieldnames:
            del obj[key]

dataset_manager = DatasetManager(auth_client)

# pass any parameter to generate all files
if len(sys.argv) > 1:
    teams = dataset_manager.get('teams')
    if teams:
        teams.delete()
    tvchannels = dataset_manager.get('tvchannels')
    if tvchannels:
        tvchannels.delete()
    stadiums = dataset_manager.get('stadiums')
    if stadiums:
        stadiums.delete()
    dataset_manager.create(global_path(STADIUMS_FILE_NAME))
    dataset_manager.create(global_path(TVCHANNELS_FILE_NAME))
    dataset_manager.create(global_path(TEAMS_FILE_NAME))

    sql = SQLClient(auth_client)

    sql.send('UPDATE teams SET the_geom = cdb_geocode_admin0_polygon(name)')
    sql.send("UPDATE tvchannels SET country = 'United Kingdom' WHERE country = 'UK'")
    sql.send('UPDATE tvchannels SET the_geom = cdb_geocode_admin0_polygon(country)')
    sql.send("UPDATE teams SET the_geom = (SELECT the_geom FROM england) WHERE name = 'England'")


matches = dataset_manager.get('matches')
if matches:
    matches.delete()
dataset_manager.create(global_path(MATCHES_FILE_NAME))

# matches_polygons = dataset_manager.get('matches_polygons')
# if matches_polygons:
#     matches_polygons.delete()
dataset_manager.create(global_path(MATCHES_POLYGONS_FILE_NAME))

sql = SQLClient(auth_client)

sql.send("DELETE FROM matches_lines");
sql.send("with teams as \
            (SELECT the_geom, id, name FROM teams), \
            lines as \
            (SELECT cartodb_id, type, home_team, away_team, home_result, away_result, date, stadium, finished, win, los, ST_Segmentize(ST_MakeLine(st_centroid((SELECT the_geom FROM teams WHERE id = win)), st_centroid((SELECT the_geom FROM teams WHERE id = los)))::geography, 100000)::geometry as the_geom \
                FROM matches), \
            tosplit AS ( \
              SELECT * FROM lines \
              WHERE ST_XMax(the_geom) - ST_XMin(the_geom) > 180 \
            ), \
            nosplit AS ( \
              SELECT * FROM lines \
              WHERE ST_XMax(the_geom) - ST_XMin(the_geom) <= 180 \
            ), \
            split AS ( \
              SELECT \
                cartodb_id, type, home_team, away_team, home_result, away_result, date, stadium, finished, win, los, \
                ST_Difference(ST_Shift_Longitude(the_geom), \
                              ST_Buffer(ST_GeomFromText('LINESTRING(180 90, 180 -90)',4326), \
                                        0.00001)) AS the_geom \
              FROM tosplit \
            ), \
            final AS ( \
              SELECT * FROM split \
              UNION ALL \
              SELECT * FROM nosplit \
            ) \
            INSERT INTO matches_lines (SELECT row_number() over() as cartodb_id, the_geom, type, home_team, away_team, home_result, away_result, date, stadium, finished, win, los from final)")