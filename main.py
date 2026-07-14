# Importing libraries
import os, boto3, time, logging, requests, zipfile, gzip, shutil, tempfile, glob
from dotenv import load_dotenv
from datetime import datetime
from modules.extract import extract_amp
from modules.unzip import unzip_all
from modules.load import load_to_s3

# Setting up logging for pipeline:
timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S') # gives the date/time now
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True) # Checks if a logs folder exist, if not then makes it.
log_filename = f'{log_dir}/amp_pipeline_{timestamp}.log' # creating a string for the log filename based on the timestamp

# Configuring log
logging.basicConfig(
    filename = log_filename,
    filemode = 'a',
    format = '%(asctime)s - %(levelname)s - %(message)s', 
    level = logging.INFO                 # Any messages INFO or above will go into the logs.
)

# Define timeframes

s = '20260602T00'
e = '20260603T00'

# Access API and download zip to local folder
extract_amp(s, e)

# Unzip the downloaded files
unzip_all()

# Load json files to s3 bucket
load_to_s3()

