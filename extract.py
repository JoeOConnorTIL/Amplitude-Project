# Importing required libraries

import time, os, json, logging, requests, zipfile, gzip
from datetime import datetime
from dotenv import load_dotenv

# Setting up folders and file format for logging and data

timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S') # gives the date/time now
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True) # creates a folder called 'logs' - if it already exists then it's ok - i.e. doesnt show an error or do anything.
log_filename = f'{log_dir}/{timestamp}.log' # creating a string for the filename based on the timestamp

# Configuring log
logging.basicConfig(
    filename = log_filename,
    format = '%(asctime)s - %(levelname)s - %(message)s', 
    level = logging.INFO
)

# Selecting logger
logger = logging.getLogger()
logger.info('Logger successfully initiated')

# Creating data directory
data_dir = 'data'
os.makedirs(data_dir, exist_ok=True) ## creates a folder called 'data' - if it already exists then it's ok - i.e. doesnt show an error or do anything.
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

# setting variables for API call
max_retry = 5
attempt = 0
delay = 10


response = requests.get(url, params=params, auth=(api_key, secret_key))
data = response.content     #This will be a zip file

# Write the reponse file to data folder

#filename = f'{data_dir}/{start}-{end}.zip'
#with open(filename, 'wb') as file:
  #  file.write(data)


while attempt < max_retry:
    response = requests.get(url, params=params, auth=(api_key, secret_key))
    status = response.status_code
    if status == 200:
        data = response.content   #this will be a zip file
        if len(data) > 0 :
            try:
                filename = f'{data_dir}/{start}-{end}.zip'
                with open(filename, 'wb') as file:
                    file.write(data)
                logger.info(f'File {filename} was successfully saved to data folder.')
            except Exception as e:
                logger.error(f'An error occurred: {e}')
            break
        else:
            logger.error('No data returned')
            break
    elif status == 400:
        logger.error('The file size of the exported data is too large. Shorten the time ranges and try again. The limit size is 4GB.')
        break
    elif status == 404:
        logger.error('No data available for the time range requested')
        break
    elif status == 504:
        logger.error('The amount of data is large causing a timeout')
    elif status <= 100 or status >=500:
        time.sleep(delay)
        print('retrying')
        logger.info(f'Status code {status}. Retrying. This was attempt {attempt}') # Adding info line to update log based on status of the response.
        attempt += 1
    else:
        logger.error(f'Error - status message: {status}')
        break
    
        



