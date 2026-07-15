import os, logging

def initiate_log(timestamp:str, log_dir:str):
    """
    This initialises the logger for the rest of the script. Put it before you run other functions.

    Args:
        timestamp(str): For the filenames of the logs.
        log_dir(str): Where the logs should be stored.
    """
    
    os.makedirs(log_dir, exist_ok=True) # creates a folder called 'logs' if it doesn't already exist.
    log_filename = f'{log_dir}/amp_pipeline_{timestamp}.log' # creating a string for the filename based on the timestamp and log directory entered.

    # Configutring logging - anything INFO level and higher will be included
    logging.basicConfig(
        filename = log_filename,
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
        level = logging.INFO
    )

    # Assign the logger
    return logging.getLogger()
    # logger.info('Logger successfully initiated')