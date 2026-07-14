# Importing required libraries

import time, os, logging, requests
from datetime import datetime
from dotenv import load_dotenv

def extract_amp(startdate:str, enddate:str):
    """
    Export Amplitude data for the given range.

    Args:
        startdate (str): Start time in Amplitude format, e.g. "20260704T00"
        enddate (str): End time in Amplitude format, e.g. "20260704T00"

    Notes:
        - The expected format is YYYYMMDDTHH
        - Use 24-hour time and include the "T" separator
    """

    # Setting up folders and file format for logging and data

    timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S') # gives the date/time now
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True) # creates a folder called 'logs' - if it already exists then it's ok - i.e. doesnt show an error or do anything.
    log_filename = f'{log_dir}/extract_{timestamp}.log' # creating a string for the filename based on the timestamp

    # Configuring log
    logging.basicConfig(
        filename = log_filename,
        filemode = 'a',
        format = '%(asctime)s - %(levelname)s - %(message)s', 
        level = logging.INFO
    )

    # Selecting logger
    logger = logging.getLogger()
    logger.info('Logger successfully initiated')

    # Checking that date arguments have been entered correctly
    start_dt = datetime.strptime(startdate, '%Y%m%dT%H')
    end_dt = datetime.strptime(enddate, '%Y%m%dT%H')

    if start_dt >= end_dt:
        logger.error('Start date should be before End date')
        return

    # Creating data directory
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True) ## creates a folder called 'data' - checks if it already exists and if not then creates it.
    # Setting out API call Parameters

    url = 'https://analytics.eu.amplitude.com/api/2/export'

    start = f'{startdate}'
    end = f'{enddate}'
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
                    filename = f'{data_dir}/{start}-{end}.zip'
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
