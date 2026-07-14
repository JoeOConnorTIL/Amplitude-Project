# Importing libraries
import os, boto3, time, logging, requests, zipfile, gzip, shutil, tempfile, glob
from dotenv import load_dotenv
from datetime import datetime
from extract import extract_amp
from unzip import unzip_all
from load import load_to_s3

# Define timeframes

s = '20260605T00'
e = '20260606T00'

# Access API and download zip to local folder
extract_amp(s, e)

# Unzip the downloaded files
unzip_all()

# Load json files to s3 bucket
load_to_s3()

