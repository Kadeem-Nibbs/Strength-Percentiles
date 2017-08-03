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
import pandas as pd

# The page from which the program collects powerlifting meet results
QUOTE_PAGE = 'http://meets.revolutionpowerlifting.com/results/2016-meet-results/ny-states/'
DATABASE = 'meet_results.db'
MEET_RESULTS_TABLE = 'meet_results'

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
    result_and_categories: tuple of strings and floats, or None
        A tuple, the first three indices of which contain a lifter's
        categorical information (gender, professional status, and equipment),
        and the later indices of which contain their squat, bench, deadlift,
        and total.  Returns None if the input row does not contain any lifter
        information (is a header row).

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

def populate_database(webpage, database, table):
    """
    Creates SQLite database with specified name.  Creates table inside the
    database and populates it with results of powerlifting meets.  If the
    created table has the same name as an already existing table, the already
    existed table is deleted.

    Paramaters:
    -----------
    webpage: string
        String specifying webpage from which to scrape meet results.
    database: string
        String specifying the name of the database in which to store meet
        results.
    table: string
        String specifying the name of the table in the database in which
        to store meet results.

    """
    table_deletion_string = "drop table if exists %s" % table

    table_empty_string = "SELECT COUNT(*) from %s" % table

    create_table_string = """CREATE TABLE if not exists %s (
    lifter_id INTEGER PRIMARY KEY, gender TEXT,
    professional_status TEXT, equipment TEXT, squat REAL,
    bench REAL, deadlift REAL, total REAL)
    """ % table

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
    #cursor.execute(table_deletion_string) # Delete table if it already exists
                                    # if we attempt to create a table with a
                                    # name that is already in use an error will
                                    # result.  The remade table will be more
                                    # up-to-date anyway.
    cursor.execute(create_table_string)
    meet_results_table_empty = cursor.execute(table_empty_string)

    # Don't attempt to add data to table unless empty
    if not meet_results_table_empty:
        return
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

####### Pandas functions
def find_percentile(database,squat=None, bench=None, deadlift=None, total=None):
    """
    Finds the percentile of the input squat, bench, deadlift and total numbers
    among the sample of results in the database.

    Parameters:
    -----------
    database: TBD
        Database containing squat, bench, deadlift, and/or total numbers
        against which to compare the input numbers.
    squat, bench, deadlift, total: float
        Floating numbers representing a user's performance in the respective
        category.  Will be compared against the results in the database.

    Returns:
    --------
    percentile: float
        The user's percentile rank among the lifters in the database in the
        input categories.

    """
    pass

def get_population_by_categories(connection, table, **categories):
    get_population_string = """Select * from {table}
        WHERE gender LIKE "{gender}%" AND
        professional_status LIKE "{professional_status}%" and
        equipment LIKE "{equipment}%";
        """.format(table=table,**categories)
    cursor = connection.cursor()
    population_database = cursor.execute(get_population_string)
    population_dataframe = pd.read_sql(get_population_string, connection)
    return population_dataframe

def find_average(dataframe, lift):
    means = dataframe.mean()
    return means[lift]

def database_to_dataframe(connection, table_name):
    read_sql_string = "select * from %s" % table_name
    dataframe = pd.read_sql(read_sql_string, connection)
    return dataframe

def standard_deviation(dataframe, *lifts):
    pass


########################
if __name__ == "__main__":
    populate_database(QUOTE_PAGE, DATABASE, MEET_RESULTS_TABLE)
    connection = sq.connect(DATABASE)
    categories = {'gender':'Female',
        'professional_status': 'AM',
        'equipment': 'Raw'
        }
    dataframe = get_population_by_categories(connection, MEET_RESULTS_TABLE, **categories)
    print dataframe
    print find_average(dataframe, "squat")
