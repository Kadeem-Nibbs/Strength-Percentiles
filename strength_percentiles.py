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
import sqlite3 as sq


# The page from which the program collects powerlifting meet results
QUOTE_PAGE = 'http://meets.revolutionpowerlifting.com/results/2016-meet-results/ny-states/'
DATABASE = 'meet_results.db'

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

def parse_result_and_categories(row):
    """
    Parses table row of BeautifulSoup object for categories (gender,
    professional status, equipment) and result (squat, bench, deadlift) of
    the associated lifter.

    Parameters:
    -----------
    row: bs4.element.tag
        A table row of BeautifulSoup object which contains category and result
        information of a lifter in the expected format (see SQUAT_COLUMN,
        BENCH_COLUMN, etc.)

    Returns:
    --------
    result, categories: Result is tuple of ints, or None, containing the
    (squat, bench, deadlift) of the lifter. categories is tuple of strings,
    containing the (gender, professional_status, equipment) of the
    lifter.  Returns None if the row contains headers and no information.

    """
    row = row.contents # list of HTML objects in row
    if row[1].get('colspan'): # row contains column headers and no data, ignore
        return
    gender = get_data_from_table(row, GENDER_COLUMN) # string
    professional_status = get_data_from_table(row, PROFESSIONAL_STATUS_COLUMN) # ...
    equipment = get_data_from_table(row, EQUIPMENT_COLUMN) # ...
    squat = get_data_from_table(row, SQUAT_COLUMN) # float or None
    bench = get_data_from_table(row, BENCH_COLUMN) # ...
    deadlift = get_data_from_table(row, DEADLIFT_COLUMN) # ...

    if squat and bench and deadlift: # Valid entries for each lift in row
        total = squat + bench + deadlift
    else:
        total = None

    result_and_categories = (gender, professional_status, equipment, squat,
        bench, deadlift, total)
    return result_and_categories

def get_data_from_table(row, column):
    """
    Retrieves data from specified location in BeautifulSoup table.

    Parameters:
    -----------
    row: list of bs4.element.Tag
    column: int
        column in which desired data should be located

    Returns:
    --------
    data: float, string, or None
        Returns a float if the column specified is one of SQUAT_COLUMN,
        BENCH_COLUMN, and DEADLIFT_COLUMN, and contains a valid numerical entry,
        returns None if the column does not contain a valid numerical entry.
        Returns a string otherwise.

    """
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

def populate_database(webpage, database):
    """
    Creates SQLite database with specified name.  Creates table inside the
    database and populates it with results of powerlifting meets.  If the
    created table has the same name as an already existing table, the already
    existed table is deleted.

    Paramaters:
    -----------
    database: string
        String specifying the name of the database in which to store meet
        results.
    webpage: string
        String specifying webpage from which to scrape meet results.

    """
    table_deletion_string = "drop table if exists meet_results"

    create_table_string = """CREATE TABLE meet_results (
    lifter_id INTEGER PRIMARY KEY, gender TEXT,
    professional_status TEXT, equipment TEXT, squat REAL,
    bench REAL, deadlift REAL, total REAL)
    """

    # IMPORTANT NOTE: Instead of using the SQLite's parameterized query
    # feature, where the ?'s are placeholders for the parameters and the
    # parameters are supplied in an iterable as the second argument to the
    # cursor's execute method, I also had the option of formatting the command
    # using Python string formatting, to insert the information I collected
    # from online into the command string.  However, this would expose my
    # computer to risks similar to those posed by Python 2's input function.
    # If I happened to collect malicious SQL code from the internet, it would
    # be formatted into the command and executed.  SQLite's parameterized
    # query feature allows me to harmlessly insert the information I collect
    # online into a database without executing it.
    result_storage_string = """INSERT INTO meet_results (
    gender,
    professional_status,
    equipment,
    squat,
    bench,
    deadlift,
    total)

    Values (
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
    )
    """
    connection = sq.connect(database)
    cursor = connection.cursor()
    cursor.execute(table_deletion_string) # Delete table if it already exists
                                    # if we attempt to create a table with a
                                    # name that is already in use an error will
                                    # result.  The remade table will be more
                                    # up-to-date anyway.
    cursor.execute(create_table_string)

    page = urllib2.urlopen(webpage)
    soup = BeautifulSoup(page, 'html.parser')
    meet_results_table = soup.find_all('tr') # all rows of meet results table,
                                             # each corresponds to an
                                             # individual's performance at the
                                             # meet
    for row in meet_results_table: # information for one lifter
        result_and_categories = parse_result_and_categories(row)
        if result_and_categories: # row contains results of meet
            cursor.execute(result_storage_string, result_and_categories)

    connection.commit()
    connection.close()

if __name__ == "__main__":
    populate_database(QUOTE_PAGE, DATABASE)
