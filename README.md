# Amplitude-Project

A data engineering project to practice ELT using Amplitude data available through the API.

## Pipeline Overview

The workflow is designed to run in this order:

1. Extract raw Amplitude export data into ZIP files in `data/`.
2. Unzip those archives and convert the compressed payloads into JSON files.
3. Upload the JSON files to S3 for downstream ingestion.
4. Use Snowflake to load the staged data into a raw table.

## Extraction Process

This project uses `extract.py` to export raw Amplitude analytics data for a specified time range.

### How it works

1. Call the function using start and end dates formatted `YYYYMMDDTHH`.
2. The function creates `logs/` and `data/` folders if they do not exist.
3. It loads Amplitude credentials from a `.env` file:
   - `AMP_API_KEY`
   - `AMP_SECRET_KEY`
4. The function calls the Amplitude export API and downloads a ZIP archive.
5. If the request succeeds, the ZIP file is saved to `data/` using the date range in the filename.
6. The script logs progress and errors to a timestamped file under `logs/`.
7. The next step is to unzip the archive and produce JSON files that can be uploaded.

## Unzipping Process

The project uses `unzip.py` to unpack the ZIP archives downloaded by `extract.py` and produce JSON files ready for upload.

### How it works

- Finds all `.zip` files under the `data/` directory (recursively).
- Extracts archives into a temporary directory and removes the original ZIP on success.
- Walks the extracted files, decompresses any `.gz` files into the `data/` root as `.json` files.
- If extraction or decompression fails for a file, the script moves the problematic ZIP into `data/quarantine/` for inspection and retains the temp folder for debugging.
- The script logs progress and errors to a timestamped file under `logs/`.

This step runs after `extract.py` and before the upload step so the loader gets plain JSON files in `data/`.

## Key `extract.py` sections

### 1. Logging and output directories

Creates directories for data and logs and generates a timestamped log file:

```python
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_filename = f'{log_dir}/{timestamp}.log'
logging.basicConfig(
    filename=log_filename,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

### 2. Date validation

Ensures the supplied start and end values are in the expected Amplitude format and that the range is valid:

```python
start_dt = datetime.strptime(startdate, '%Y%m%dT%H')
end_dt = datetime.strptime(enddate, '%Y%m%dT%H')
if start_dt >= end_dt:
    logger.error('Start date should be before End date')
    return
```

### 3. API request and retry handling

Fetches the export ZIP and retries on server errors or connection issues:

```python
while attempt < max_retry:
    try:
        response = requests.get(url, params=params, auth=(api_key, secret_key), timeout=60)
    except Exception as e:
        logger.error(f'Error with API call: {e}')
    status = response.status_code
    logger.info(f'API response status: {status}')
    if 200 <= status < 300:
        data = response.content
        if len(data) > 0:
            filename = f'{data_dir}/{start}-{end}.zip'
            with open(filename, 'wb') as file:
                file.write(data)
            logger.info(f'File {filename} was successfully saved to data folder.')
            break
```

### 4. Saving the exported data

Writes the downloaded ZIP content to the `data/` folder:

```python
filename = f'{data_dir}/{start}-{end}.zip'
with open(filename, 'wb') as file:
    file.write(data)
```

### `extract.py` flow diagram

```text
start
  |
  v
validate dates (YYYYMMDDTHH)
  |
  v
init logging and folders
  |
  v
load .env credentials
  |
  v
build API request
  |
  v
call Amplitude export endpoint
  |
  v
check response status
  |    |        |
  |    |        +--> 429 / 500+ --> retry with backoff --> loop
  |    |
  |    +--> 400-499 --> log client error --> end
  |
  +--> 200-299 --> save ZIP --> end
  |
  +--> else --> log unknown status --> end
```

## Key `unzip.py` sections

### 1. Temporary workspace and logging

Creates a temporary extraction directory and starts a timestamped log file:

```python
timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_filename = f'{log_dir}/unzip_{timestamp}.log'

logging.basicConfig(
    filename = log_filename,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    level = logging.INFO
)
```

### 2. Discovering and extracting ZIP archives

Finds ZIPs under `data/`, extracts them into a temporary folder, and removes the source archive on success:

```python
zip_paths = glob.glob(os.path.join(data_dir, '**', '*.zip'), recursive=True)

for zip_path in zip_paths:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    os.remove(zip_path)
```

### 3. Decompressing `.gz` files into JSON

Walks the extracted files and writes each `.gz` payload to the `data/` root as a `.json` file:

```python
for root, _, files in os.walk(temp_dir):
    for file in files:
        if file.endswith('.gz'):
            gz_path = os.path.join(root, file)
            out_name = file[:-3]
            out_path = os.path.join(data_dir, out_name)

            with gzip.open(gz_path, 'rb') as gz_in, open(out_path, 'wb') as out_f:
                shutil.copyfileobj(gz_in, out_f)
```

### 4. Quarantine fallback for failed files

If extraction or decompression fails, the archive is moved to `data/quarantine/` for later inspection:

```python
quarantine_dir = os.path.join(data_dir, 'quarantine')
os.makedirs(quarantine_dir, exist_ok=True)
dest = os.path.join(quarantine_dir, os.path.basename(zip_path))
shutil.move(zip_path, dest)
```

## S3 and Snowflake Setup

This project uses an AWS S3 bucket as the landing zone for uploaded data and Snowflake to read that data for downstream loading and analysis.

### Overview

The flow works like this:

1. A local Python script uploads files to an S3 bucket.
2. The script uses an AWS IAM user with access keys stored locally in a `.env` file.
3. The S3 bucket is encrypted with a KMS key.
4. Snowflake reads files from S3 through a storage integration and external stage.
5. A Snowflake `COPY INTO` command loads the staged data into a raw table.

### AWS S3 setup

First, create an S3 bucket to store uploaded files. In this project, the bucket is configured with KMS encryption so that objects are encrypted at rest.

Next, create an IAM user for the local Python script. This user needs an IAM policy with the permissions required to upload and manage objects in the bucket.

Typical S3 permissions include:

- `s3:ListBucket`
- `s3:GetObject`
- `s3:PutObject`
- `s3:DeleteObject`
- `s3:ListMultipartUploadParts`

If the bucket uses KMS encryption, the policy should also include the relevant KMS permissions:

- `kms:Encrypt`
- `kms:Decrypt`
- `kms:GenerateDataKey`

The policy should be scoped to the bucket ARN, and if access to subfolders is needed, the object ARN should include `/*`.

After the policy is created, attach it to the IAM user and generate an access key and secret access key for local development.

### Local Python upload script

The Python script uses `boto3` to connect to AWS and upload files to S3.

The following values are stored in a `.env` file:

- AWS access key
- AWS secret access key
- bucket name

The local environment is usually set up with:

- a virtual environment
- `python-dotenv`
- `boto3`

### Snowflake setup

Snowflake accesses the S3 bucket using an IAM role and a storage integration.

The Snowflake-side setup includes:

- creating an IAM role in AWS for Snowflake access
- creating a storage integration in Snowflake
- running `DESC INTEGRATION` to retrieve the Snowflake IAM user ARN and external ID
- updating the AWS role trust policy with those values
- creating an external stage that points to the S3 bucket

Example Snowflake SQL:

```sql
CREATE STORAGE INTEGRATION your_project_storage_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<your-account-number>:role/your-project-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://your-storage-location');

DESC INTEGRATION your_project_storage_integration;

CREATE OR REPLACE STAGE your_project_stage
  URL = 's3://your-storage-location'
  STORAGE_INTEGRATION = your_project_storage_integration
  FILE_FORMAT = (
    TYPE = JSON
    ALLOW_DUPLICATE = FALSE
    STRIP_OUTER_ARRAY = TRUE
  );
```

### Loading data into Snowflake

Once files are available in the stage, Snowflake can list them and load them into a raw table.

```sql
LIST @your_project_stage;

CREATE TABLE your_project_raw
(
  json VARIANT,
  filename STRING
);

COPY INTO your_project_raw
FROM (
  SELECT
    $1,
    metadata$filename
  FROM @your_project_stage
)
FILE_FORMAT = (
  TYPE = JSON
  ALLOW_DUPLICATE = FALSE
  STRIP_OUTER_ARRAY = TRUE
);
```

### Result

This setup provides a secure, repeatable pipeline for moving data from local Python code into S3 and then into Snowflake for analysis.

Key benefits:

- credentials stay out of source code
- S3 objects are encrypted with KMS
- Snowflake access is controlled through a storage integration
- raw data is loaded in a consistent, auditable way

## Load Process

The `load.py` script uploads decompressed JSON files from `data/` into an S3 bucket so downstream tools (for example Snowflake) can stage and ingest them.

### How it works

- Reads AWS credentials and the bucket name from the local `.env` file:
  - `AWS_ACCESS_KEY`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_BUCKET_NAME`
- Creates a `boto3` S3 client using those credentials.
- Iterates the files in `data/`, skipping the `quarantine` folder.
- Uploads each file to a target prefix (configured in the script as `python-import/`) and deletes the local file on successful upload.
- Logs uploads and any errors to a timestamped file under `logs/`.

Place this step after you have set up the S3 bucket and IAM user (see "AWS S3 setup" above) so the script has a valid destination and permissions to upload objects.

## Key `load.py` sections

### 1. Logging and environment configuration

Starts a timestamped log file and loads credentials from the local `.env` file:

```python
timestamp = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_filename = f'{log_dir}/load_{timestamp}.log'

logging.basicConfig(
    filename = log_filename,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    level = logging.INFO
)

load_dotenv()
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
```

### 2. S3 client setup

Creates the AWS S3 client used to upload files:

```python
s3_client = boto3.client(
    's3',
    aws_access_key_id = AWS_ACCESS_KEY,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
)
```

### 3. Upload loop and local cleanup

Iterates through the JSON files in `data/`, uploads each file to S3, and deletes the local copy after a successful upload:

```python
for file in files:
    to_upload = f'{data_dir}/{file}'
    filename = f'{s3_loc}{file}'
    s3_client.upload_file(to_upload, AWS_BUCKET_NAME, filename)
    os.remove(to_upload)
```

## Notes

- Ensure your `.env` file contains valid Amplitude API credentials.
- The export endpoint is `https://analytics.eu.amplitude.com/api/2/export`.
- Logs are created in `logs/` so you can troubleshoot API responses and retry behavior.
