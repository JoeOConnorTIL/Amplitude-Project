# Importing libraries
import os, boto3, time, logging, requests, zipfile, gzip, shutil, tempfile, glob
from dotenv import load_dotenv
from datetime import datetime
from modules.extract import extract_amp
from modules.unzip import unzip_all
from modules.load import load_to_s3
from modules.logger import initiate_log

# Setting up logging for pipeline:
timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S') # gives the date/time now
log_dir = 'logs'
#os.makedirs(log_dir, exist_ok=True) # Checks if a logs folder exist, if not then makes it.
#log_filename = f'{log_dir}/amp_pipeline_{timestamp}.log' # creating a string for the log filename based on the timestamp

# Configuring log
#logging.basicConfig(
#    filename = log_filename,
#    filemode = 'a',
#    format = '%(asctime)s - %(levelname)s - %(message)s', 
#    level = logging.INFO                 # Any messages INFO or above will go into the logs.
#)
logger = initiate_log(timestamp, log_dir)
logger.info('Logger Successfully Initiated')
# Define timeframes

s = '20260602T00'
e = '20260603T00'

logger = logging.getLogger()
url = 'https://analytics.eu.amplitude.com/api/2/export'
data_dir = 'data'

# Retrieving keys from .env file
load_dotenv()
api_key = os.getenv('AMP_API_KEY')
secret_key = os.getenv('AMP_SECRET_KEY')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
s3_loc = 'python-import/'
max_retry = 3
delay = 10

# Access API and download zip to local folder
extract_amp(url, s, e, api_key, secret_key, data_dir, max_retry, delay)

# Unzip the downloaded files
unzip_all(data_dir)

# Load json files to s3 bucket
load_to_s3(data_dir, AWS_BUCKET_NAME, s3_loc)