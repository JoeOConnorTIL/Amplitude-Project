import os
import zipfile
import gzip
import shutil
import tempfile
import glob

# Create a temporary extraction directory

def unzip_all():
    temp_dir = tempfile.mkdtemp()

    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)

    # Find all .zip files under `data/` (including subdirectories)
    zip_paths = glob.glob(os.path.join(data_dir, '**', '*.zip'), recursive=True)
    if not zip_paths:
        print('No zip files found in data/')

    for zip_path in zip_paths:
        print(f'Extracting {zip_path} into {temp_dir}')
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            # If extraction succeeded, remove the source zip file
            try:
                os.remove(zip_path)
                print(f'Deleted source zip {zip_path}')
            except Exception as e:
                print(f'Failed to delete {zip_path}: {e}')
        except Exception as e:
            print(f'Failed to extract {zip_path}: {e}')
            # Move the bad or non-zip file to a quarantine folder for inspection
            quarantine_dir = os.path.join(data_dir, 'quarantine')
            os.makedirs(quarantine_dir, exist_ok=True)
            try:
                dest = os.path.join(quarantine_dir, os.path.basename(zip_path))
                shutil.move(zip_path, dest)
                print(f'Moved failed zip to quarantine: {dest}')
            except Exception as me:
                print(f'Failed to move {zip_path} to quarantine: {me}')

    # Walk extracted content, decompress .gz files and write .json files into the root of `data/`
    # Skip decompression if the target already exists. If all extractions and decompressions
    # succeed, remove the temporary directory.
    all_ok = True
    decompressed_any = False
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.gz'):
                gz_path = os.path.join(root, file)
                out_dir = data_dir  # flatten into data/ root as requested
                os.makedirs(out_dir, exist_ok=True)

                out_name = file[:-3]
                out_path = os.path.join(out_dir, out_name)

                if os.path.exists(out_path):
                    print(f'Skipping {gz_path}: {out_path} already exists')
                    continue

                try:
                    with gzip.open(gz_path, 'rb') as gz_in, open(out_path, 'wb') as out_f:
                        shutil.copyfileobj(gz_in, out_f)
                    decompressed_any = True
                    print(f'Decompressed {gz_path} -> {out_path}')
                except Exception as e:
                    all_ok = False
                    print(f'Failed to decompress {gz_path}: {e}')

    # Remove temporary directory only if all operations succeeded
    if all_ok:
        try:
            shutil.rmtree(temp_dir)
            print(f'Removed temporary directory {temp_dir}')
        except Exception as e:
            print(f'Failed to remove temp directory {temp_dir}: {e}')
    else:
        print(f'Temporary directory retained at {temp_dir} for inspection (some operations failed)')
