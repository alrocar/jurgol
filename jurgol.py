from io import StringIO

import ipdb

import csv
import json
import os
import urllib.request

from carto.auth import APIKeyAuthClient
from carto.datasets import DatasetManager

API_KEY = os.environ["CARTO_API_KEY"]
USERNAME = "aromeu"
USR_BASE_URL = "https://{user}.carto.com/".format(user=USERNAME)
auth_client = APIKeyAuthClient(api_key=API_KEY, base_url=USR_BASE_URL)

STADIUMS_FILE_NAME = "stadiums.csv"
TVCHANNELS_FILE_NAME = "tvchannels.csv"
TEAMS_FILE_NAME = "teams.csv"
MATCHES_FILE_NAME = "matches.csv"

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
    print(obj)

for obj in write_csv(TVCHANNELS_FILE_NAME, ['id', 'name', 'icon', 'country', 'iso2', 'lang'], data_json['tvchannels']):
    obj['lang'] = ' '.join(map(str, obj['lang'])).strip()

for obj in write_csv(TEAMS_FILE_NAME, ['id', 'name', 'fifaCode', 'iso2', 'flag', 'emoji', 'emojiString'], data_json['teams']):
    print(obj)

matches = []
for group in data_json['groups']:
    # ipdb.set_trace(context=50)
    matches = matches + data_json['groups'][group]['matches']

for knockout in data_json['knockout']:
    matches = matches + data_json['knockout'][knockout]['matches']

ipdb.set_trace(context=50)
fieldnames = ['name', 'type', 'home_team', 'away_team', 'home_result', 'away_result', 'date', 'stadium', 'channels', 'finished']
for obj in write_csv(MATCHES_FILE_NAME, fieldnames, matches):
    for key in obj:
        if key not in fieldnames:
            obj
    obj['channels'] = ' ' #.join(map(str, obj['channels'])).strip()


# dataset_manager = DatasetManager(auth_client)
# dataset_manager.create(global_path(STADIUMS_FILE_NAME))
# dataset_manager.create(global_path(TVCHANNELS_FILE_NAME))
# dataset_manager.create(global_path(TEAMS_FILE_NAME))
# dataset_manager.create(global_path(MATCHES_FILE_NAME))
