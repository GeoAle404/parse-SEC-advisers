'''
File: f1_parse_filing.py
Project: Extract Location

File Created: Tuesday, 29th June 2021 10:38:56 pm

Author: Georgij Alekseev (georgij.v.alekseev@gmail.com)
-----
Last Modified: Wednesday, 22nd September 2021 9:53:03 pm
-----
Description: Functions for parsing and preprocessing of downloaded N-SAR and N-CEN filings.
'''
# =================================================================================================
# PACKAGES
# =================================================================================================
import re                           # Regular Expressions


# =================================================================================================
# FUNCTIONS
# =================================================================================================
def safe_findall(text, fmt):
    """
    Safe wrapper for re.findall that ensures the code keeps running when nothing found.
    Arguments: text - string to be searched, fmt - regular expression.
    """
    out = re.findall(fmt, text)
    if len(out) == 0:
        out = [""]
    return out

def parse_file(file_name, data):
    """
    This function identifies the filing type and redirects to the correct parsing method.
    Arguments: data - string file containing complete SEC filing.
    """
    # extract filing type
    ftype = safe_findall(data, r'(?sm)CONFORMED SUBMISSION TYPE:\s+(.*?)\s*$')[0]
    # redirect to relevant parsing function
    if ftype.startswith("N-CEN"):
        return parse_ncen_file(file_name, data)
    if ftype.startswith("NSAR"):
        return parse_nsar_file(file_name, data)
    return None

def parse_nsar_file(file_name, data):
    """
    This function extracts general information, funds, and advisers from NSAR filings.
    Arguments: data - string file containing complete SEC filing.
    """
    # first separate header and bodies in html format
    header = safe_findall(data, r'(?s)<(?:SEC|IMS)-HEADER>(.*)</(?:SEC|IMS)-HEADER>')[0]
    # note: there may be multiple bodies, when the filing includes additional exhibits
    bodies = safe_findall(data, r'(?s)<DOCUMENT>(.*?)</DOCUMENT>')

    # extract values we care about from header:
    ftype       = safe_findall(header, r'(?sm)CONFORMED SUBMISSION TYPE:\s+(.*?)\s*$')[0]
    accession   = safe_findall(header, r'(?sm)ACCESSION NUMBER:\s+(\S+)\s*$')[0]
    cik         = safe_findall(header, r'(?sm)CENTRAL INDEX KEY:\s+(\d+)\s*$')[0]
    fdate       = safe_findall(header, r'(?sm)FILED AS OF DATE:\s+(\d+)\s*$')[0]
    rdate       = safe_findall(header, r'(?sm)CONFORMED PERIOD OF REPORT:\s+(\d+)\s*$')[0]
    reg_name    = safe_findall(header, r'(?sm)COMPANY CONFORMED NAME:\s+(.*?)\s*$')[0]
    reg_state   = safe_findall(header, r'(?sm)STATE:\s+(\S+)\s*$')[0]
    reg_zip     = safe_findall(header, r'(?sm)ZIP:\s+(\S+)\s*$')[0]
    reg_city    = safe_findall(header, r'(?sm)CITY:\s+(.*?)\s*$')[0]

    # will be filled in loop
    adviser_info = []
    fund_info = []

    # loop through bodies
    for body in bodies:
        # sequence of current body
        sequence = safe_findall(body, r'(?sm)<SEQUENCE>(.*?)$')[0]

        # funds; each fund has an ID, which will be used to match advisers
        # if there are no funds in the reporting, adviser info defaults to fund ID '01'
        # matches: (fund ID, fund name)
        funds = safe_findall(body, r'(?sm)^007 C02(\d\d+)00\s*(.*?)\s*$')
        if funds == ['']:
            funds = [['01', '']]

        # add sequence identifier to current fund number as it is only unique within a sequence
        funds = [(f'{f[0]}-S{sequence}', f[1]) for f in funds]

        # adviser information
        # reported for each fund, thus, keep track of fund ID
        # also need to keep track of adviser id to match all characteristics
        # matches: (fund id, adviser id, adviser info)
        adviser_names       = safe_findall(body, r'(?sm)^008 A00(\S+)(\d\d)\s+(.*?)\s*$')
        adviser_subadvisor  = safe_findall(body, r'(?sm)^008 B00(\S+)(\d\d)\s+(.*?)\s*$') # sub-adviser or adviser (A/S)
        adviser_cities      = safe_findall(body, r'(?sm)^008 D01(\S+)(\d\d)\s+(.*?)\s*$')
        adviser_states      = safe_findall(body, r'(?sm)^008 D02(\S+)(\d\d)\s+(.*?)\s*$')
        adviser_zips        = safe_findall(body, r'(?sm)^008 D03(\S+)(\d\d)\s+(.*?)\s*$')

        # combine adviser info
        advisers = [adviser_names, adviser_subadvisor, adviser_cities, adviser_states, adviser_zips]
        advisers = zip(advisers, ['adv_name', 'adv_subadvisor', 'adv_city', 'adv_state', 'adv_zip'])
        for info, name in advisers:
            if info != ['']:
                for cur_fund_id, cur_adviser_id, cur_value in info:
                    adviser_info += [[file_name, cik, fdate, f'{cur_fund_id}-S{sequence}',
                                      cur_adviser_id, name, cur_value]]

        # combine fund info
        fund_info += [[file_name, cik, fdate]+list(e) for e in funds if e != ['']]

    # combine registrant info
    registrant_info = [file_name, cik, fdate, rdate, ftype, accession, reg_name,
                       reg_state, reg_zip, reg_city]

    return registrant_info, fund_info, adviser_info

def parse_ncen_file(file_name, data):
    """
    This function extracts general information, funds, and advisers from N-CEN filings.
    Arguments: data - string file containing complete SEC filing.
    """
    # first separate header and body in html format
    header = safe_findall(data, r'(?s)<(?:SEC|IMS)-HEADER>(.*)</(?:SEC|IMS)-HEADER>')[0]
    body = safe_findall(data, r'(?s)<DOCUMENT>(.*)')[0]

    # now extract values we care about from header:
    ftype       = safe_findall(header, r'(?sm)CONFORMED SUBMISSION TYPE:\s+(.*?)\s*$')[0]
    accession   = safe_findall(header, r'(?sm)ACCESSION NUMBER:\s+(\S+)\s*$')[0]
    cik         = safe_findall(header, r'(?sm)CENTRAL INDEX KEY:\s+(\d+)\s*$')[0]
    fdate       = safe_findall(header, r'(?sm)FILED AS OF DATE:\s+(\d+)\s*$')[0]
    rdate       = safe_findall(header, r'(?sm)CONFORMED PERIOD OF REPORT:\s+(\d+)\s*$')[0]
    reg_name    = safe_findall(header, r'(?sm)COMPANY CONFORMED NAME:\s+(.*?)\s*$')[0]
    reg_state   = safe_findall(header, r'(?sm)STATE:\s+(\S+)\s*$')[0]
    reg_zip     = safe_findall(header, r'(?sm)ZIP:\s+(\S+)\s*$')[0]
    reg_city    = safe_findall(header, r'(?sm)CITY:\s+(.*?)\s*$')[0]

    # get fund information; advisers are part of the block
    funds = safe_findall(body, r'(?s)<managementInvestmentQuestion>(.+?)</managementInvestmentQuestion>')
    fund_names = [safe_findall(e, r'(?s)<mgmtInvFundName>(.+?)</mgmtInvFundName>')[0] for e in funds]

    # get adviser information from the fund blocks
    # note that each fund can have multiple advisers, so now we get a list of lists
    advisers = [safe_findall(e, r'(?s)<investmentAdvisers>(.+?)</investmentAdvisers>')[0] for e in funds]
    adviser_names = [safe_findall(e, r'(?s)<investmentAdviserName>(.+?)</investmentAdviserName>') for e in funds]
    adviser_secs = [safe_findall(e, r'(?s)<investmentAdviserFileNo>(.+?)</investmentAdviserFileNo>') for e in funds]
    adviser_crds = [safe_findall(e, r'(?s)<investmentAdviserCrdNo>(.+?)</investmentAdviserCrdNo>') for e in funds]
    adviser_states = [safe_findall(e, r'(?s)investmentAdviserState="(.+?)"') for e in funds]

    # do the same for subadvisers
    subadvisers = [safe_findall(e, r'(?s)<subAdvisers>(.+?)</subAdvisers>')[0] for e in funds]
    subadviser_names = [safe_findall(e, r'(?s)<subAdviserName>(.+?)</subAdviserName>') for e in funds]
    subadviser_secs = [safe_findall(e, r'(?s)<subAdviserFileNo>(.+?)</subAdviserFileNo>') for e in funds]
    subadviser_crds = [safe_findall(e, r'(?s)<subAdviserCrdNo>(.+?)</subAdviserCrdNo>') for e in funds]
    subadviser_states = [safe_findall(e, r'(?s)subAdviserState="(.+?)"') for e in funds]

    # flag subadvisers (use name here since this is always populated)
    adviser_suba = [['A']*len(a)+['S']*len(s) for a, s in zip(adviser_names, subadviser_names)]

    # combine them
    adviser_names = [a+s for a, s in zip(adviser_names, subadviser_names)]
    adviser_secs = [a+s for a, s in zip(adviser_secs, subadviser_secs)]
    adviser_crds = [a+s for a, s in zip(adviser_crds, subadviser_crds)]
    adviser_states = [a+s for a, s in zip(adviser_states, subadviser_states)]

    # manually create fund IDs, as they are not automatically matched in the filing
    fund_ids = list(range(0, len(funds)))

    # combine adviser info
    advisers = [adviser_names, adviser_secs, adviser_crds, adviser_states, adviser_suba]
    advisers = zip(advisers, ['adv_name', 'adv_sec', 'adv_crd', 'adv_state', 'adv_subadvisor'])
    adviser_info = []
    for info, name in advisers:
        # info is for all funds, so that's still a list of adviser lists
        fund_id = 0
        for sub_info in info:
            # now we have all entries for the current fund
            adviser_id = 0
            for cur_value in sub_info:
                # no need to add empty information (note: still incrementing adviser count)
                if cur_value != '':
                    adviser_info += [[file_name, cik, fdate, fund_id, adviser_id, name, cur_value]]
                adviser_id += 1
            fund_id += 1

    # combine registrant and fund info
    registrant_info = [file_name, cik, fdate, rdate, ftype, accession, reg_name, reg_state, reg_zip, reg_city]
    fund_info = [[file_name, cik, fdate, f_id, f_name] for f_id, f_name in zip(fund_ids, fund_names)]

    return registrant_info, fund_info, adviser_info
