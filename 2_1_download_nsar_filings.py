'''
File: s2_1_download_nsar_filings.py
Project: Extract Location

File Created: Tuesday, 29th June 2021 10:38:56 pm

Author: Georgij Alekseev (georgij.v.alekseev@gmail.com)
-----
Last Modified: Wednesday, 22nd September 2021 9:56:43 pm
-----
Description: This code downloads all SEC filings from 'NSAR_directory.csv', which is created by
             the previous code: '1_download_and_combine_edgar_index_files.py'
'''
# =================================================================================================
# PACKAGES
# =================================================================================================
import os
import time
import pandas as pd
import requests


# =================================================================================================
# SETTINGS
# =================================================================================================
FILING_LIST = 'D:/path/subpath/NSAR_directory.csv'
OUTPUT_DIR = 'D:/path/subpath'


# =================================================================================================
# RUN
# =================================================================================================
# load information on all prefiltered filings
filing_addresses = pd.read_csv(FILING_LIST)
# drop duplicate links
filing_addresses = filing_addresses.drop_duplicates(subset='fname')
# separate the filings by year
filing_addresses['fdate'] = pd.to_datetime(filing_addresses['fdate'], format="%Y-%m-%d")
filing_addresses['year'] = filing_addresses['fdate'].dt.year
filing_addresses = [[filing_addresses[filing_addresses['year'] == y], y] for y in filing_addresses['year'].unique()]

# keep track of progress
COUNT = 0

# loop through years
for cur_filing_addresses, year in filing_addresses:

    # make yearly folder if not existing yet
    if not os.path.exists(os.path.join(OUTPUT_DIR, str(year))):
        os.makedirs(os.path.join(OUTPUT_DIR, str(year)))

    # omit the files that are already present in OUTPUT_DIR
    finished_files = os.listdir(os.path.join(OUTPUT_DIR, str(year)))
    cur_filing_addresses = cur_filing_addresses[[e.split("/")[-1] not in finished_files
                                                 for e in cur_filing_addresses['fname']]]

    # download all filings for the current year
    for fname in cur_filing_addresses["fname"]:

        # try-except block to catch errors and keep the code running
        try:
            # generate URL
            url = 'https://www.sec.gov/Archives/'+fname
            # read URL
            r = requests.get(url)
            # write as output, i.e., save website
            with open(os.path.join(OUTPUT_DIR, str(year), fname.split("/")[-1]), 'w', 
                      encoding="utf-8") as outfile:
                outfile.write(r.text)

        # this is the error handler, something went wrong
        except Exception as inst:
            # print failed URL
            print('https://www.sec.gov/Archives/'+fname)
            # print error message and continue with next row
            print(inst)
            time.sleep(0.1)

        COUNT += 1
        if COUNT%2000 == 0:
            print(f"{COUNT} files downloaded.")

        # wait one-tenth of a second before sending another request to EDGAR
        # EDGAR in general does not allow more than 10 requests per second
        # due to the download time, a lower sleep time may be enough too
        # though 0.1 seconds is safest
        time.sleep(0.1)
