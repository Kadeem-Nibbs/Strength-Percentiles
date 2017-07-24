# Script Name	: strength_percentiles.py
# Author		: Kadeem Nibbs
# Created		: 7/16/2017
# Last Modified	:
# Version		: 1.0

# This program scrapes revolutionpowerlifting.com for the results of a 2016
# New York powerlifting meet, and loads them into a list of tuples.
# Later versions of the program will allow users to enter their own lifting
# numbers to be compared to the lifters from the competition.  They will be
# able to see their percentile rank and where they would place among the
# competitors in their demographic.

import urllib2
from bs4 import BeautifulSoup
import re

# The page from which the program collects powerlifting meet results
QUOTE_PAGE = 'http://meets.revolutionpowerlifting.com/results/2016-meet-results/ny-states/'

# Each row of the MEET_RESULTS_TABLE contains information corresponding to
# one lifter in the competition.  Desired information is accessed
# through the appropriate column of the table.  Column numbers start at 0.
# Every other column contains a whitespace string.
GENDER_COLUMN = 1 # Column containing gender information (male or female) for
                  # all lifters
PROFESSIONAL_STATUS_COLUMN = 3 # ...
EQUIPMENT_COLUMN = 5 # ...
SQUAT_COLUMN = 15 # ...
BENCH_COLUMN = 17 # ...
DEADLIFT_COLUMN = 19 # ...

# This dictionary will contain lists of tuples.  Each tuple will contain one
# lifter's (squat, bench, deadlift, total). The lists divide the results
# by the lifters' category (ex: men, amateurs) but each lifter has
# their result repeated in four lists, ("all," one of "men" and "women," one
# of "amateur" and "professional," and one of "raw" and "equipped")
categorized_results = {'all': [],
        'amateurs': [],
        'professionals': [],
        'men': [],
        'women': [],
        'raw': [],
        'equipped': []}

def scrape_webpage_and_store_meet_results(quote_page):
    page = urllib2.urlopen(quote_page)
    soup = BeautifulSoup(page, 'html.parser')
    meet_results_table = soup.find_all('tr') # all rows of meet results table,
                                             # each corresponds to an
                                             # individual's performance at the
                                             # meet
    for row in meet_results_table: # information for one lifter
        parse_and_store_result(row)

def parse_and_store_result(row):
    row = row.contents # list of HTML objects in row
    if row[1].get('colspan'): # row contains column headers and no data, ignore
        return
    gender = get_data_from_table(row,GENDER_COLUMN) # string
    professional_status = get_data_from_table(row,PROFESSIONAL_STATUS_COLUMN) # ...
    equipment = get_data_from_table(row,EQUIPMENT_COLUMN) # ...
    squat = get_data_from_table(row,SQUAT_COLUMN) # float
    bench = get_data_from_table(row,BENCH_COLUMN) # ...
    deadlift = get_data_from_table(row,DEADLIFT_COLUMN) # ...

    if squat and bench and deadlift: # Valid entries for each lift in row
        total = squat + bench + deadlift
    else:
        total = None

    result = (squat, bench, deadlift, total)
    categories = (gender, professional_status, equipment)
    categorize_and_store_result(categorized_results,result,categories)

def get_data_from_table(row, column):
    """The input is a row containing all of the information about one lifter's
    performance at the meet, and the column at which the desired data is
    located.  This function returns a string if the requested column contains
    gender, professional status, or equipment data, and returns a float if the
    requested column contains squat, bench, or deadlift data."""
    data = row[column].string
    if column in (SQUAT_COLUMN, BENCH_COLUMN, DEADLIFT_COLUMN):
        # If the entry at the specified row and column is empty, data will
        # have value None and TypeError will be thrown.  If the entry is DNF,
        # meaning the lifter missed all their attempts at the lift, data will
        # have the value 'DNF' which can't be converted to a float, and
        # ValueError will be thrown.
        try:
            data = float(data)
        except (TypeError, ValueError):
            return None
        else:
            return data
    return data

def categorize_and_store_result(container, result, categories):
    """The input is an iterable of categories containing a gender, professional
    status, an equipment status (raw or equipped).  This function stores the
    meet results in the appropriate subsections of the container."""
    gender, professional_status, equipment = categories
    container['all'].append(result)
    if gender == 'Female':
        container['women'].append(result)
    else:
        container['men'].append(result)

    if professional_status == 'AM':
        container['amateurs'].append(result)
    else:
        container['professionals'].append(result)

    if equipment.startswith('Raw'):
        container['raw'].append(result)
    else:
        container['equipped'].append(result)

def test_scrape_webpage_and_store_meet_results(container):
    for category in container:
        print category, "~"*15
        for result in container[category]:
            print "\t", result
        print "\n"*5
    print "Number of lifters: ", len(container['all'])
    print "Number of men: ", len(container['men'])
    print "Number of women: ", len(container['women'])
    print "Number of amateurs: ", len(container['amateurs'])
    print "Number of professionals: ", len(container['professionals'])
    print "Number of raw lifters: ", len(container['raw'])
    print "Number of equipped lifters: ", len(container['equipped'])

if __name__ == "__main__":
    scrape_webpage_and_store_meet_results(QUOTE_PAGE)
