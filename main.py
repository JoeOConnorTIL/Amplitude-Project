# Importing libraries
import os, boto3, time, logging, requests, zipfile, gzip, shutil, tempfile, glob
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from modules.extract import extract_amp
from modules.unzip import unzip_all
from modules.load import load_to_s3
from modules.logger import initiate_log

# Setting up logging for pipeline:
timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S') # gives the date/time now
log_dir = 'logs'
logger = initiate_log(timestamp, log_dir)
logger.info('Logger Successfully Initiated')

# Define timeframes
# If running today - give me all of yesterday's data
now = datetime.now(timezone.utc)
yesterday = now - timedelta(days=1)
s = yesterday.strftime('%Y%m%dT00')
e = yesterday.strftime('%Y%m%dT23')

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