'''

Copy fuij + canon Raw files and JPEGS to HDD under dated folders 

Currently finds SD folder with FUJI name.
Uses JPEGS to find exif data.

The goal is to have a standalone automated pi or sbc to copy images at whim.

'''

import os
import shutil
from datetime import datetime
import exifread
import pathlib

#the folder where all your images are stored
destination_root_folder = "/media/richard/My Book/photos"

def find_fuji_folder():
    folders = []
    try:
        user = os.getlogin()
    except:
        print("no user found")

    media_path = pathlib.Path(f'/media/{user}/')

    for dcim_folder in media_path.glob('*/DCIM'):
        for fuji_folder in dcim_folder.iterdir():
            print(fuji_folder)
            # IN FUTURE add in other folder names or catch folders with raw files in
            # rather that using fuji name
            if fuji_folder.is_dir() and fuji_folder.name.upper().endswith("FUJI"):
                folders.append(fuji_folder)
    return folders


# List of supported RAW file extensions (add ".raf" to the list)
imagetypes = [".raw", ".jpg", ".raf", ".mov", "cr2"]
raw_files = [".raw", "cr2"]

# Function to extract creation date from the EXIF metadata
def get_creation_date_from_exif(file_path):
    try:
        with open(file_path, "rb") as image_file:
            tags = exifread.process_file(image_file)
            if "EXIF DateTimeOriginal" in tags:
                date_taken = tags["EXIF DateTimeOriginal"].values
                return datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")
    except:
        pass
    return None

# Function to get the file creation date
def get_file_creation_date(file_path):
    return datetime.fromtimestamp(os.path.getctime(file_path))

# Function to find a JPEG counterpart for a RAF file
def find_jpeg_counterpart(raf_path):
    base, ext = os.path.splitext(raf_path)
    jpeg_path = base + ".JPG"
    if os.path.exists(jpeg_path):
        return jpeg_path
    return None

def process(sd_card_path):

    # Get a list of all RAW photo files on the SD card
    image_files = [file for file in os.listdir(sd_card_path) if any(file.lower().endswith(ext) for ext in imagetypes)]

    # Create destination root folder if it doesn't exist
    if not os.path.exists(destination_root_folder):
        os.makedirs(destination_root_folder)


    # Organize RAW files by date into subfolders
    for file in image_files:

        print(f"opening {file}")

        source_path = os.path.join(sd_card_path, file)
        
        # Try to extract EXIF date, fallback to file creation date for RAF files
        creation_date = get_creation_date_from_exif(source_path)
        if not creation_date:
            if any(file.lower().endswith(ext) for ext in raw_files):
                print("useing counterpart jpg for exif data")
                jpeg_counterpart = find_jpeg_counterpart(source_path)
                if jpeg_counterpart:
                    creation_date = get_creation_date_from_exif(jpeg_counterpart)
                else:
                    print("no jpg? Using file creation date.")
                    creation_date = get_file_creation_date(source_path)
            if not creation_date and file.lower().endswith(".mov"):
                creation_date = get_file_creation_date(source_path)
            
        if creation_date:
            year_folder = creation_date.strftime("%Y")
            date_folder = creation_date.strftime("%Y-%m-%d")
            destination_year_folder = os.path.join(destination_root_folder, year_folder)
            destination_date_folder = os.path.join(destination_year_folder, date_folder)
            # Only create the destination folder if it doesn't exist
            if not os.path.exists(destination_date_folder):
                print(f"creating new folder for {destination_date_folder}")
                os.makedirs(destination_date_folder)
            #else:
                #print(f"Folder - {destination_date_folder} exists already")

            destination_path = os.path.join(destination_date_folder, file)
            
            # Check if the file already exists in the destination folder
            if not os.path.exists(destination_path):
                print(f"Copying: {file} to {destination_path}")
                shutil.copy2(source_path, destination_path)  # Copy file while preserving metadata
            else:
                #print(f"Skipping: {file} (File already exists in {destination_path})")
                pass

            # Wait for keypress to proceed to the next file
            #input("Press Enter to continue to the next file...")

    print("RAW photos copied and organized by date successfully!")

folders = find_fuji_folder()

if folders:
    for folder in folders:
        while True:
            process_folder = input(f"Process folder {folder}? (y/n): ")
            if process_folder.lower() in ["y", "yes"]:
                # Process the folder here
                print("Processing folder...")
                process(folder)
                break
            elif process_folder.lower() in ["n", "no"]:
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
else:
    print("No FUJI folders found.")

