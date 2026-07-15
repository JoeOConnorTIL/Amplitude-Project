# Importing libraries
import os, logging
from dotenv import load_dotenv
from datetime import datetime
import boto3

logger = logging.getLogger()
load_dotenv()
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
data_dir = 'data'
s3_loc = 'python-import/' 

def load_to_s3(data_dir, AWS_BUCKET_NAME, s3_loc):

    logger.info('Load Logger successfully initiated')

    # Setting up s3 client to connect to AWS
    s3_client = boto3.client(
        's3',
        aws_access_key_id = AWS_ACCESS_KEY,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    )

    # Writing functionality to loop through data files and upload them, and delete them from local file when done.
    # data_dir = 'data'
    files = os.listdir(data_dir)
    files.remove('quarantine')
    # s3_loc = 'python-import/'      # listing files in data folder

    for file in files:                # Iterating through the listed files
        to_upload = f'{data_dir}/{file}' 
        filename=f'{s3_loc}{file}'      # Giving file path as a variable
        try:
            s3_client.upload_file(to_upload, AWS_BUCKET_NAME, filename)
            logger.info(f'{file} successfully uploaded.')
            os.remove(to_upload)               # Deleting file once it's uploaded
        except Exception as e:
            logger.error(e)