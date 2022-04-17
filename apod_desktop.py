""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py image_dir_path [apod_date]

Parameters:
  image_dir_path = Full path of directory in which APOD image is stored
  apod_date = APOD image date (format: YYYY-MM-DD)

History:
  Date        Author      Description
  2022-03-11  J.Dalby     Initial creation
  2022-03-20  A.Asturias  create_image_db and get_apod_info functions completed
  2022-03-24  A.Asturias  if statement added to validate the connection to APOD
  2022-03-27  A.Asturias  prints added to create_image_db
  2022-04-07  A.Asturias  download_apod_image, get_image_path, print_apod_info, and image_already_in_db functions completed
  2022-04-17  A.Asturias  save_image_file and set_desktop_background_image functions completed, add_image_to_db started
"""

from sys import argv, exit
from datetime import datetime, date
from hashlib import sha256
from os import path
from sqlite3 import connect
from requests import get
import ctypes

def main():

    # Determine the paths where files are stored
    image_dir_path = get_image_dir_path()
    db_path = path.join(image_dir_path, 'apod_images.db')

    # Get the APOD date, if specified as a parameter
    apod_date = get_apod_date()

    # Create the images database if it does not already exist
    create_image_db(db_path)

    # Get info for the APOD
    apod_info_dict = get_apod_info(apod_date)

    # Download today's APOD
    image_url = apod_info_dict['url']
    image_msg = download_apod_image(image_url)
    image_sha256 = sha256(image_msg.content).hexdigest()
    image_size = len(image_msg.content)
    image_path = get_image_path(image_url, image_dir_path)

    # Print APOD image information
    print_apod_info(image_url, image_path, image_size, image_sha256)

    # Add image to cache if not already present
    if not image_already_in_db(db_path, image_sha256):
        save_image_file(image_msg, image_path)
        ########add_image_to_db(db_path, image_path, image_size, image_sha256)

    # Set the desktop background image to the selected APOD
    set_desktop_background_image(image_path)

def get_image_dir_path():
    """
    Validates the command line parameter that specifies the path
    in which all downloaded images are saved locally.

    :returns: Path of directory in which images are saved locally
    """
    if len(argv) >= 2:
        dir_path = argv[1]
        if path.isdir(dir_path):
            print("\nImages directory:", dir_path)
            return dir_path
        else:
            print('Error: Non-existent directory', dir_path)
            exit('Script execution aborted')
    else:
        print('Error: Missing path parameter.')
        exit('Script execution aborted')

def get_apod_date():
    """
    Validates the command line parameter that specifies the APOD date.
    Aborts script execution if date format is invalid.

    :returns: APOD date as a string in 'YYYY-MM-DD' format
    """   

    if len(argv) >= 3:
        # Date parameter has been provided, so get it
        apod_date = argv[2]

        # Validate the date parameter format
        try:
            datetime.strptime(apod_date, '%Y-%m-%d')
        except ValueError:
            print('Error: Incorrect date format; Should be YYYY-MM-DD')
            exit('Script execution aborted')
    else:
        # No date parameter has been provided, so use today's date
        apod_date = date.today().isoformat()
    
    print("APOD date:", apod_date)
    return apod_date

def get_image_path(image_url, dir_path):
    """
    Determines the path at which an image downloaded from
    a specified URL is saved locally.

    :param image_url: URL of image
    :param dir_path: Path of directory in which image is saved locally
    :returns: Path at which image is saved locally
    """

    print("Determining image local path...", end=" ")

    #split image URL to get the section after the last / to use as image name
    img_name = image_url.split("/")[-1]

    #creates a valid path to store an image file in the directory selected
    image_path = path.join(dir_path, img_name)
    print("done!")

    return image_path

def get_apod_info(date):
    """
    Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.

    :param date: APOD date formatted as YYYY-MM-DD
    :returns: Dictionary of APOD info
    """    

    #define constants with link to API and key
    APOD_URL = "https://api.nasa.gov/planetary/apod"
    APOD_KEY = "lMDGG0bANZOe9caY59RJmVoaviTTzzdTDRihVaw5"

    #dictionary with parameters to send to APOD
    parameters = {'api_key': APOD_KEY, 'date': date}

    #make request to APOD
    api_response = get(APOD_URL, params=parameters)

    #verify the connection was successful
    if api_response.status_code == 200:
        print("Request to APOD successful!")
        return api_response.json()
    elif api_response.status_code == 404:
        print("Unable to establish connection: " + str(api_response.status_code) + "\nMake sure to input an existing past date.")
        exit('Script execution aborted')
    else:
        print("Unable to establish connection: " + str(api_response.status_code))
        exit('Script execution aborted')

def print_apod_info(image_url, image_path, image_size, image_sha256):
    """
    Prints information about the APOD

    :param image_url: URL of image
    :param image_path: Path of the image file saved locally
    :param image_size: Size of image in bytes
    :param image_sha256: SHA-256 of image
    :returns: None
    """    

    #print all the known information about the APOD image
    print("\n---------- APOD Image Information ----------")
    print('URL: ' + image_url)
    print('Local path: ' + image_path)
    print('Size: ' + str(image_size) + " bytes")
    print('SHA-256 digest: ' + image_sha256)
    print("--------------------------------------------\n")

def download_apod_image(image_url):
    """
    Downloads an image from a specified URL.

    :param image_url: URL of image
    :returns: Response message that contains image data
    """
    
    #get a response from the url directing to APOD's image
    response = get(image_url, stream = True)

    #make sure the response was successful
    if response.status_code == 200:
        print('Image sucessfully downloaded from', image_url)
        return response
    else:
        print('Error: Unable to retrieve image from URL.')
        exit('Script execution aborted')

def save_image_file(image_msg, image_path):
    """
    Extracts an image file from an HTTP response message
    and saves the image file to disk.

    :param image_msg: HTTP response message
    :param image_path: Path to save image file
    :returns: None
    """

    print("Saving image to local folder...", end=" ")

    #open (create if non existent) a file with the local path specified, in write binary mode
    image_file = open(image_path, 'wb')
    #write binary string to file and close it
    image_file.write(image_msg.content)
    image_file.close()

    print("done!")

def create_image_db(db_path):
    """
    Creates an image database if it doesn't already exist.

    :param db_path: Path of .db file
    :returns: None
    """

    print("Validating existance of database...", end=" ")

    #establish connection with the target database or creates it if it does not exist
    db_connection = connect(db_path)

    #create a cursor for the db in order to make queries
    db_cursor = db_connection.cursor()

    #query to create images table
    query = """CREATE TABLE IF NOT EXISTS images (
        id integer PRIMARY KEY NOT NULL,
        full_path text NOT NULL,
        file_size int NOT NULL,
        hash_value text NOT NULL,
        date_downloaded datetime NOT NULL
        );"""

    #execute query using the cursor object
    db_cursor.execute(query)

    #save changes and close connection
    db_connection.commit()
    db_connection.close()

    print("done!")

def add_image_to_db(db_path, image_path, image_size, image_sha256):
    """
    Adds a specified APOD image to the DB.

    :param db_path: Path of .db file
    :param image_path: Path of the image file saved locally
    :param image_size: Size of image in bytes
    :param image_sha256: SHA-256 of image
    :returns: None
    """

    print("Saving data to database...", end=" ")

    #establish connection with the target database
    db_connection = connect(db_path)

    #create a cursor for the db in order to make queries
    db_cursor = db_connection.cursor()

    #query to insert values in the images table
    query = """INSERT INTO images (
        full_path,
        file_size,
        hash_value,
        date_downloaded)
        VALUES (?, ?, ?, ?)
        );"""

    #tuple to substitute placeholders in query
    placeholder = (image_path, image_size, image_sha256, datetime.now())

    #execute query using the cursor object and values for placeholders
    db_cursor.execute(query, placeholder)

    #save changes and close connection
    db_connection.commit()
    db_connection.close()

    print("done!")

def image_already_in_db(db_path, image_sha256):
    """
    Determines whether the image in a response message is already present
    in the DB by comparing its SHA-256 to those in the DB.

    :param db_path: Path of .db file
    :param image_sha256: SHA-256 of image
    :returns: True if image is already in DB; False otherwise
    """ 

    print("Validating existance of APOD image entry in database...", end=" ")

    #establish connection with the images database
    db_connection = connect(db_path)

    #create a cursor for the db in order to make queries
    db_cursor = db_connection.cursor()

    #query to count images matching the hash
    query = """SELECT COUNT(id) from images
               WHERE hash_value = :hash;"""

    #placeholder to replace the image hash in the query
    placeholder = {'hash': image_sha256}
    
    #execute query using the cursor object and substituting the placeholder
    db_cursor.execute(query, placeholder)

    #get all results from query
    query_result = db_cursor.fetchall()

    #close connection
    db_connection.close()

    #determine if there was a match or not
    if query_result[0][0] == 0:
        print("image not in database!")
        return False
    else:
        print("image already in database!")
        return True

def set_desktop_background_image(image_path):
    """
    Changes the desktop wallpaper to a specific image.

    :param image_path: Path of image file
    :returns: None
    """

    print("Setting new desktop background...", end=" ")

    #set current desktop background to be the APOD image
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)

    print("done!")

main()