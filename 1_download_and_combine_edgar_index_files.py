'''
File: 1_download_and_combine_edgar_index_files.py
Project: Extract Location

File Created: Wednesday, 22nd September 2021 5:05:38 pm

Author: Georgij Alekseev (georgij.v.alekseev@gmail.com)
-----
Last Modified: Wednesday, 22nd September 2021 9:55:58 pm
-----
Description: This code downloads SEC index files from EDGAR and combines the
             N-SAR and N-CEN reportings into a single csv file.
             Downloading is based on code by Martin Dewitt
             https://gist.github.com/madewitt/29bceb51c494ef9ea1d34f9474aa4b3c.
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
# specify list of years to be searched
YEARS = [2000 + x for x in range(0,21)]

# specify list of quarters to be searched
QUARTERS = ['QTR1', 'QTR2', 'QTR3', 'QTR4']

# the absolute path to the folder for saving the index files and the final csv
FILE_DIR = 'D:/path/subpath'


# =================================================================================================
# DOWNLOAD INDEX FILES
# =================================================================================================
# get a list of the files already saved; they will be skipped
saved_files = os.listdir(FILE_DIR)

# loop over the years and quarters. For each year/quarter combination, get the corresponding
# index file from EDGAR, and save it as a text file
for yr in YEARS:
    for qtr in QUARTERS:
        # filename pattern to store the index files locally
        cur_file_name =  f'form-index-{yr}-{qtr}.txt'

        # absolute path for storing the index file
        cur_file_path = os.path.join(FILE_DIR, cur_file_name)

        # only download if not already saved
        if cur_file_name in saved_files:
            print(f'Skipping index file for {yr}, {qtr} because it is already saved.')
            continue

        # SEC url leading to the index file
        url = f'https://www.sec.gov/Archives/edgar/full-index/{yr}/{qtr}/form.idx'

        # save the index file as txt
        r = requests.get(url, stream=True)
        with open(cur_file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=10240):
                f.write(chunk)

        # wait 0.1 seconds to not get blocked
        time.sleep(0.1)


# =================================================================================================
# COMBINE DOWNLOADED SEC INDEX FILES
# =================================================================================================
# loop through all filings
filings = os.listdir(FILE_DIR)

# keep files ending with txt
filings = [f for f in filings if f.endswith(".txt")]

for filing_name in filings:

    # Open the current file and split it into lines
    filing = os.path.join(FILE_DIR, filing_name)
    filing = open(filing, "r")
    filing = filing.read().splitlines()

    # the EDGAR index file format is unusual; it doesn't use a column separator
    # a columns starts always at a predefined distance from the line start
    # identify this distance by finding the location of the headers
    form_loc = filing[8].find('Form Type')
    company_loc = filing[8].find('Company Name')
    cik_loc = filing[8].find('CIK')
    fdate_loc = filing[8].find('Date Filed')
    fname_loc = filing[8].find('File Name')

    # now loop through the lines in the file and extract the information
    # from the previously identifed positional characters
    entries = []
    for line in filing[10:]:
        entries.append([line[form_loc:company_loc].strip(),
                        line[company_loc:cik_loc].strip(),
                        line[cik_loc:fdate_loc].strip(),
                        line[fdate_loc:fname_loc].strip(),
                        line[fname_loc:].strip()])

    # convert to data frame
    index_table = pd.DataFrame(entries, 
                               columns=["form_type", "comp_name", "cik", "fdate", "fname"])

    # keep only relevant filings; restrict form_type on starting with "NSAR" or "N-CEN"
    index_table = index_table[index_table.form_type.str.startswith(("NSAR", "N-CEN"))]

    # save as csv
    output_name = os.path.join(FILE_DIR, filing_name.split(".")[0]+"_NSAR.csv")
    index_table.to_csv(output_name, index=False)

    # print progress
    print("File " + filing_name.split(".")[0] + " successfully exported as csv.")

# finally, combine all csv to single file; first get filenames
filings_csv = [f for f in os.listdir(FILE_DIR) if f.endswith(".csv")]

# now combine to single file and save
all_filings = pd.concat([pd.read_csv(os.path.join(FILE_DIR, f)) for f in filings_csv])
all_filings.to_csv(os.path.join(FILE_DIR, "NSAR_directory.csv"), index=False)
