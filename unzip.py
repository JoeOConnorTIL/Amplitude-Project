import os          
import zipfile     
import gzip        
import shutil     
import tempfile    

temp_dir = tempfile.mkdtemp()   # Makes a temporary folder to extract all the folder paths out to.

data_dir= 'data'
os.makedirs(data_dir, exist_ok=True)  # Makes a local folder called 'data' if it doesn't already exist.

with zipfile.ZipFile('data/20260704T00-20260704T00.zip', 'r') as zip_ref:        # Extracts all the zip files into the temporary folder.
    zip_ref.extractall(temp_dir)

day_folder = next(f for f in os.listdir(temp_dir) if f.isdigit())  # Finds all folders with numeric names only and returns the file path as a variable to be traversed
day_path = os.path.join(temp_dir, day_folder)

# Directory walking and file processing:
for root, _, files in os.walk(day_path):
    for file in files:
        if file.endswith('.gz'):
            print(file)

# os.walk() recursively traverses all subdirectories
# tuple unpacking: roor, _, files (underscore ignores directories list)
# print returns the file name to the screen

# Now reading the contents of the .gz file and writing the content to a new json file in the data_dir
gz_path = os.path.join(root, file)
json_filename = file[:-3]
output_path = os.path.join(data_dir, json_filename)

with gzip.open(gz_path, 'rb') as gz_file, open(output_path, 'wb') as out_file:
    shutil.copyfileobj(gz_file, out_file)

# String slicing: file[:-3] removes last three characters (.gz)
# Binary file handling: 'rb' (read binary) and 'wb' (write binary)
# shutil.copyfileobj(): Efficient copying between file objects.

# Cleanup:
shutil.rmtree(temp_dir)