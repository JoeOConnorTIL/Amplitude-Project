# Importing required libraries

import time, os, json, logging, requests
from datetime import datetime
from dotenv import load_dotenv

# Setting up folders and file format for logging and data

timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S') # gives the date/time now
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True) # creates a folder called 'logs' - if it already exists then it's ok - i.e. doesnt show an error or do anything.
log_filename = f'{log_dir}/{timestamp}.log' # creating a string for the filename based on the timestamp

data_dir = 'data'
os.makedirs(data_dir, exist_ok=True) ## creates a folder called 'logs' - if it already exists then it's ok - i.e. doesnt show an error or do anything.

# Setting out API call Parameters

url = 'https://analytics.eu.amplitude.com/api/2/export'

start = '20260707T00'
end = '20260708T00'

params = {
    'start': start,
    'end' : end
}

# Retrieving keys from .env file
load_dotenv()
api_key=os.getenv('AMP_API_KEY')
secret_key=os.getenv('AMP_SECRET_KEY')

max_retry = 5
attempt = 0
delay = 10

response = requests.get(url, params=params, auth=(api_key, secret_key))
data = response.content     #This will be a zip file

# Write the reponse file to data folder

filename = f'{data_dir}/{start}-{end}.zip'
with open(filename, 'wb') as file:
    file.write(data)

