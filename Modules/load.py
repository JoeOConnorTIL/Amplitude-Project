# Importing libraries
import os, logging
from dotenv import load_dotenv
from datetime import datetime
import boto3

def load_to_s3():

    # Configuring log - Note: if logger already set up in main script then that will be the default log - otherwise this will set up a log for loads. I have left this in the function incase it is to be used elsewhere.
    timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S') 
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True) 
    log_filename = f'{log_dir}/load_{timestamp}.log'

    logging.basicConfig(
        filename = log_filename,
        format = '%(asctime)s - %(levelname)s - %(message)s', 
        level = logging.INFO
    )

    logger = logging.getLogger()
    logger.info('Load Logger successfully initiated')

    # Loading access/secret keys from .env file
    load_dotenv()
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

    # Setting up s3 client to connect to AWS
    s3_client = boto3.client(
        's3',
        aws_access_key_id = AWS_ACCESS_KEY,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    )

    # Writing functionality to loop through data files and upload them, and delete them from local file when done.
    data_dir = 'data'
    files = os.listdir(data_dir)
    files.remove('quarantine')
    s3_loc = 'python-import/'      # listing files in data folder

    for file in files:                # Iterating through the listed files
        to_upload = f'{data_dir}/{file}' 
        filename=f'{s3_loc}{file}'      # Giving file path as a variable
        try:
            s3_client.upload_file(to_upload, AWS_BUCKET_NAME, filename)
            logger.info(f'{file} successfully uploaded.')
            os.remove(to_upload)               # Deleting file once it's uploaded
        except Exception as e:
            logger.error(e)