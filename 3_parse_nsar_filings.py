'''
File: 3_parse_nsar_filings.py
Project: Extract Location

File Created: Tuesday, 29th June 2021 10:38:56 pm

Author: Georgij Alekseev (georgij.v.alekseev@gmail.com)
-----
Last Modified: Wednesday, 22nd September 2021 9:56:32 pm
-----
Description: This code parses and preprocesses all downloaded SEC filings.
'''
# =================================================================================================
# PACKAGES
# =================================================================================================
import os               # Browse directories
import csv              # CSV documents
import pandas as pd

# specify folder containing the code, that's necessary for some python interpreters
# os.chdir("C:/Users/ga2203/Dropbox/Climate Finance Project/Code/Extract Location")
from f1_parse_filing import parse_file   # selfmade functions


# =================================================================================================
# SETTINGS
# =================================================================================================
# specify path of downloaded NSAR filings
FILE_DIR = 'D:/path/subpath'
# specify output path
OUTPUT_DIR = 'D:/path/subpath'


# =================================================================================================
# LOOP THROUGH YEARS
# =================================================================================================
# years downloaded
years = [y for y in os.listdir(FILE_DIR) if y.isdigit()]

for year in years:
# =================================================================================================
# PREPARE OUTPUT FILES
# =================================================================================================
    # create empty CSV file, this will be filled
    csv_registrants = open(os.path.join(OUTPUT_DIR, f'nsar_registrants_{year}.csv'), 'w', newline='')
    csv_funds       = open(os.path.join(OUTPUT_DIR, f'nsar_funds_{year}.csv'),       'w', newline='')
    csv_advisers    = open(os.path.join(OUTPUT_DIR, f'nsar_advisers_{year}.csv'),    'w', newline='')

    # setup writer
    writer_registrants = csv.writer(csv_registrants)
    writer_funds = csv.writer(csv_funds)
    writer_advisers = csv.writer(csv_advisers)

    # make headers; the tables can be merged on cik-fdate-fund_id
    # fi (fund identifier), rh (registrant header), fh (fund header), ah (adviser header)
    # adviser info is in long format, i.e., 'adviser_info' specifies the information contained in 'value'
    rh = ['file_name', 'cik', 'fdate', 'rdate', 'ftype', 'accession', 'reg_name', 
          'reg_state', 'reg_zip', 'reg_city']
    fh = ['file_name', 'cik', 'fdate', 'fund_id', 'fund']
    ah = ['file_name', 'cik', 'fdate', 'fund_id', 'adviser_id', 'adviser_info', 'value']

    # write headers in csv files
    writer_registrants.writerow(rh)
    writer_funds.writerow(fh)
    writer_advisers.writerow(ah)


# =================================================================================================
# PARSE FILINGS
# =================================================================================================
    # loop over all SEC filings
    for file_name in os.listdir(os.path.join(FILE_DIR, year)):

        # full path to the current file
        full_path = os.path.join(FILE_DIR, year, file_name)

        # try-except block to catch errors and keep the code running
        try:
            # open and read the complete filing into a very long string
            filing = open(full_path, 'r')
            data = filing.read()
            filing.close()

            # parse the file, extract everything we need
            registrant_info, fund_info, adviser_info = parse_file(file_name, data)

            # write lines
            writer_registrants.writerow(registrant_info)
            writer_funds.writerows(fund_info)
            writer_advisers.writerows(adviser_info)

        except Exception as inst:
            print(f'In parse_file: {full_path}, error: {str(inst)}')

    # we are done, close files
    csv_registrants.close()
    csv_funds.close()
    csv_advisers.close()

    print(f"Finished year {year}.")


# =================================================================================================
# COMBINE YEARLY FILES
# =================================================================================================
# append with list comprehension; that's much more efficient than appending right away
full_registrants = pd.concat([pd.read_csv(os.path.join(OUTPUT_DIR, f'nsar_registrants_{year}.csv'))
                                    for year in years])
full_funds       = pd.concat([pd.read_csv(os.path.join(OUTPUT_DIR, f'nsar_funds_{year}.csv'))
                                    for year in years])
full_advisers    = pd.concat([pd.read_csv(os.path.join(OUTPUT_DIR, f'nsar_advisers_{year}.csv'))
                                    for year in years])

# save full output
full_registrants.to_csv(os.path.join(OUTPUT_DIR, 'nsar_registrants.csv'), index=False)
full_funds.to_csv(os.path.join(OUTPUT_DIR, 'nsar_funds.csv'), index=False)
full_advisers.to_csv(os.path.join(OUTPUT_DIR, 'nsar_advisers.csv'), index=False)
