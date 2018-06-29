from io import StringIO

# import ipdb

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

PATH = os.getcwd()

STADIUMS_FILE_NAME = "stadiums.csv"
STADIUMS_PATH = "{path}/{filename}".format(path = PATH, filename = STADIUMS_FILE_NAME)

data_url = 'https://raw.githubusercontent.com/lsv/fifa-worldcup-2018/master/data.json'
response = urllib.request.urlopen(data_url)
data = response.read().decode('utf-8')
data_json = json.load(StringIO(data))

with open(STADIUMS_FILE_NAME, 'w', newline='') as csvfile:
    fieldnames = ['id', 'name', 'city', 'lat', 'lng', 'image']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    stadiums = data_json['stadiums']
    for stadium in stadiums:
        writer.writerow(stadium)

dataset_manager = DatasetManager(auth_client)
dataset = dataset_manager.create(STADIUMS_PATH)
