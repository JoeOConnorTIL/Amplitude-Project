# Amplitude-Project

A data engineering project to practice ELT using Amplitude data available through the API.

## Extraction Process

This project uses `extract.py` to define a function used to export raw Amplitude analytics data for a specified time range.

### How it works

1. Call the function using start and end dates formatted `YYYYMMDDTHH` - indication added to the function to inform the user of the required date format.
2. The function creates `logs/` and `data/` folders if they do not exist.
3. It loads Amplitude credentials from a `.env` file:
   - `AMP_API_KEY`
   - `AMP_SECRET_KEY`
4. The function calls the Amplitude export API and downloads a ZIP archive.
5. If the request succeeds, the ZIP file is saved to `data/` using the date range in the filename.
6. The script logs progress and errors to a timestamped file under `logs/`.
7. A second script to unzip the various layers within these zip files will then follow to leave the json files unpacked and stored locally.

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

## Notes

- Ensure your `.env` file contains valid Amplitude API credentials.
- The export endpoint is `https://analytics.eu.amplitude.com/api/2/export`.
- Logs are created in `logs/` so you can troubleshoot API responses and retry behavior.
