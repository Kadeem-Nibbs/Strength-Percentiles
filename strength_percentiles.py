# Script Name	: strength_percentiles.py
# Author		: Kadeem Nibbs
# Created		: 7/16/2017
# Last Modified	:
# Version		: 1.0

# This program will define a program to scrape powerlifting websites for
# lifters' squat, bench, deadlift numbers.  People who use this
# program will be able to enter their own lift numbers and see where their
# percentile rank among the competitive strength training population

import urllib2
from bs4 import BeautifulSoup
import re

# Results for New York State Powerlifting meet

quote_page = 'http://meets.revolutionpowerlifting.com/results/2016-meet-results/ny-states/'
# contains list of tuples, each tuple (squat, bench, deadlift, total),
# represents lifts made by individual of group corresponding to dictionary key
lifts = {'all': [] ,
        'amateur': [],
        'professional': [] ,
        'men': [],
        'women': [],
        'raw': [],
        'equipped': []}

page = urllib2.urlopen(quote_page)
soup = BeautifulSoup(page, 'html.parser')

# list of HTML table row tag objects, each corresponds to an individual's
# performance at this meet
meet_results_table = soup.find_all('tr')

gender_column = 1
professional_status_column = 3
equipment_column = 5
squat_column = 15 # column containing lifters' squat numbers, counting from 0
bench_column = 17 # ...
deadlift_column = 19 # ...

for result in meet_results_table: # information for one lifter
    contents = result.contents # list of HTML objects in row
    if contents[1].get('colspan'): # row is column headers, no data, ignore
        continue
    else:
        # Extract lifts from appropriate column in desired format, store
        gender = contents[gender_column].string
        professional_status = contents[professional_status_column].string
        equipment = contents[equipment_column].string
        try:
            squat = float(contents[squat_column].string)
        # No entry for this lift or 'DNF', meaning competitor missed all 3 attempts
        except (TypeError, ValueError):
            squat = None

        try:
            bench = float(contents[bench_column].string)
        except (TypeError, ValueError):
            bench = None

        try:
            deadlift = float(contents[deadlift_column].string)
        except (TypeError, ValueError):
            deadlift = None

        if squat and bench and deadlift:
            total = squat + bench + deadlift
        else:
            total = None

        numbers = (squat, bench, deadlift, total)
        lifts['all'].append(numbers)

        if gender == 'Female':
            lifts['women'].append(numbers)
        else:
            lifts['men'].append(numbers)

        if professional_status == 'AM':
            lifts['amateur'].append(numbers)
        else:
            lifts['professional'].append(numbers)

        if equipment.startswith('Raw'):
            lifts['raw'].append(numbers)
        else:
            lifts['professional'].append(numbers)

for set_of_lifts in lifts['all']:
    print set_of_lifts
