# Importing required libraries

import time, os, logging, requests
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger()
url = 'https://analytics.eu.amplitude.com/api/2/export'
data_dir = 'data'
# Retrieving keys from .env file
load_dotenv()
api_key=os.getenv('AMP_API_KEY')
secret_key=os.getenv('AMP_SECRET_KEY')
max_retry = 3
delay = 10

def extract_amp(url, startdate:str, enddate:str, api_key, secret_key, data_dir, max_retry=3, delay=10):
    """
    Export Amplitude data for the given range.

    Args:
        startdate (str): Start time in Amplitude format, e.g. "20260704T00"
        enddate (str): End time in Amplitude format, e.g. "20260704T00"

    Notes:
        - The expected format is YYYYMMDDTHH
        - Use 24-hour time and include the "T" separator
    """

    logger.info('Extraction Logger successfully initiated')

    # Checking that date arguments have been entered correctly
    start_dt = datetime.strptime(startdate, '%Y%m%dT%H')
    end_dt = datetime.strptime(enddate, '%Y%m%dT%H')

    if start_dt >= end_dt:
        logger.error('Start date should be before End date')
        return

    os.makedirs(data_dir, exist_ok=True) ## creates a folder called 'data' - checks if it already exists and if not then creates it.

    # Setting out API call Parameters

    params = {
        'start': startdate,
        'end' : enddate
    }
    attempt = 0

    response = requests.get(url, params=params, auth=(api_key, secret_key))
    data = response.content     #This will be a zip file

    while attempt < max_retry:
        try:
            response = requests.get(url, params=params, auth=(api_key, secret_key), timeout=60)   # timeout added
        except Exception as e:
            logger.error(f'Error with API call: {e}')
        status = response.status_code
        logger.info(f'API response status: {status}')   # Adding API call status to log
        if 200 <= status < 300:
            data = response.content   #this will be a zip file
            if len(data) > 0 :
                try:
                    filename = f'{data_dir}/{startdate}-{enddate}.zip'
                    with open(filename, 'wb') as file:
                        file.write(data)
                    logger.info(f'File {filename} was successfully saved to data folder.')
                except Exception as e:
                    logger.error(f'An error occurred: {e}')
                break
            else:
                logger.error('No data returned')     # Indicates that although the API call has functioned - no data has actually been delivered.
                break
        elif 400 <= status < 500 and status != 429:
            logger.error(f'Error - {status} - check https://amplitude.com/docs/apis/analytics/export#status-codes')
            break
        elif status <= 100 or status >=500 or status == 429 :
            time.sleep(delay*attempt)      # Increases the delay each time an attempt fails
            logger.info(f'Status code {status}. Retrying. This was attempt {attempt}') # Adding info line to update log based on status of the response.
            attempt += 1  # Updates attempt no and tries again
        else:
            logger.error(f'Error - status message: {status}. Please fix')
            break
