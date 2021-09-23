'''
File: 2_2_download_adviser_locations.py
Project: Extract Location

File Created: Tuesday, 29th June 2021 10:38:56 pm

Author: Georgij Alekseev (georgij.v.alekseev@gmail.com)
-----
Last Modified: Wednesday, 22nd September 2021 9:56:03 pm
-----
Description: This code downloads the adviser-specific location information for
             the newer filing format N-CEN. Then it combines all previously downloaded
             adviser information files and assigns a timestamp to them.
'''
# =================================================================================================
# PACKAGES
# =================================================================================================
import os
import csv
import re                                       # Regular Expressions
from io import BytesIO                          # In-Memory Bytes Stream
from zipfile import ZipFile                     # Unwrapping Zip Files
import requests                                 # HTTP requests
from bs4 import BeautifulSoup                   # HTML parsing
from bs4.dammit import EncodingDetector         # Encoding identifier
import pandas as pd


# =================================================================================================
# SETTINGS
# =================================================================================================
# directory for the adviser files to be downloaded
OUTPUT_DIR = 'D:/path/subpath'

# years that should be included
# note that the new N-CEN format only started in 2018
YEARS = [2018, 2019, 2020]

# that's the SEC link that contains the adviser location
# do NOT change unless the link is broken
SEC_ADVISER_URL = "https://www.sec.gov/help/foiadocsinvafoiahtm.html"


# =================================================================================================
# OBTAIN LINKS FOR THE MONTHLY ADVISER FILES
# =================================================================================================
# request URL
resp = requests.get(SEC_ADVISER_URL)
# identify encoding
encoding = EncodingDetector.find_declared_encoding(resp.content, is_html=True)
# now parse
soup = BeautifulSoup(resp.content, features='lxml', from_encoding=encoding)
# extract all URLs
URLs = [link['href'] for link in soup.find_all('a', href=True)]

# keep only adviser URLs
# example: ia070120.zip, i.e., report version 01 valid for 07/2020
URLs = [e for e in URLs if bool(re.search(r'ia\d+\.zip', e))]
# add SEC URL prefix
URLs = ['https://www.sec.gov'+e for e in URLs]
# restrict on YEARS
YEARS_ABR = '|'.join([str(y)[-2:] for y in YEARS])
URLs = [e for e in URLs if bool(re.search(rf"ia\d+({YEARS_ABR})\.zip", e))]


# =================================================================================================
# DOWNLOAD AND EXTRACT ZIP FILES
# =================================================================================================
for link in URLs:
    # download file
    resp = requests.get(link)
    # identify as zip
    f = ZipFile(BytesIO(resp.content))
    # unwrap
    f.extractall(OUTPUT_DIR)


# =================================================================================================
# ENSURE CONSISTENT FILE NAMING
# =================================================================================================
# get file names
file_names = [f for f in os.listdir(OUTPUT_DIR) if bool(re.search('.xlsx$', f))]

def update_name(file_name):
    """
    This function ensures that file names follow the convention 'ia%m//d//d%y.xlsx' (e.g., ia070119.xlsx)
    Args: file_name - string
    """
    # if satisfies format, return unchanged
    if bool(re.search(r'ia\d{6}\.xlsx', file_name)):
        return file_name
    # Other format used so far is: 'SEC Registered Investment Adviser Report 2018-11-1.xlsx'
    year, month, version = re.findall(r'(\d{4})-(\d{1,2})-(\d{1}).xlsx', file_name)[0]
    # use parsed year, month, version information to create standard file name
    new_file_name = f"ia{month.zfill(2)}{version.zfill(2)}{year[-2:]}.xlsx"
    return new_file_name

# change naming to be consistent with ia...xlsx
new_file_names = [update_name(f) for f in file_names]
# change only the file names that need to be changed
file_changes = [(old_f, new_f) for old_f, new_f in zip(file_names, new_file_names) if old_f != new_f]
# now change names
for old_f, new_f in file_changes:
    os.rename(os.path.join(OUTPUT_DIR,old_f), os.path.join(OUTPUT_DIR,new_f))


# ======================================================================================================================
# COMBINE ALL FILES
# ======================================================================================================================
# prepare CSV file that will be filled, csv writer, and csv header
csv_adv_panel = open(os.path.join(OUTPUT_DIR, 'adviser_panel.csv'), 'w', newline='')
writer_adv_panel = csv.writer(csv_adv_panel)
writer_adv_panel.writerow(['crd', 'sec', 'name', 'city', 'state', 'zip', 'year_month'])
csv_adv_panel.close()

# loop through all files
files = [e for e in os.listdir(OUTPUT_DIR) if re.search(r'\.xlsx$', e)]
for f in files:

    # extract month and year from current file name
    month, year = re.findall(r'ia(\d{2})(?:\d{2})(\d{2})\.xlsx', f)[0]
    # load current file
    cur_data = pd.read_excel(os.path.join(OUTPUT_DIR, f))
    # keep only relevant columns
    cur_data = cur_data[['Organization CRD#', 'SEC#', 'Primary Business Name',
                         'Main Office City', 'Main Office State', 'Main Office Postal Code']]
    # add timestamp
    cur_data['year_month'] = f"{year}-{month}"
    # append to final data
    cur_data.to_csv(os.path.join(OUTPUT_DIR, 'adviser_panel.csv'), mode='a', header=False, index=False)
    # track progress
    print(f"Finished file {f}.")
