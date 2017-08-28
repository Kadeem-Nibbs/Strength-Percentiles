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
import numbers

# The page from which the program collects powerlifting meet results
QUOTE_PAGE = 'http://meets.revolutionpowerlifting.com/results/2016-meet-results/ny-states/'
DATABASE = 'meet_results.db'
MEET_RESULTS_TABLE = 'meet_results'

# Lifter categories
GENDER = 'gender'
FEMALE = 'Female'
MALE = 'Male'
AMATEUR = 'AM'
PROFESSIONAL_STATUS = 'professional_status'
PROFESSIONAL = 'Pro'
EQUIPMENT = 'equipment'
RAW = 'Raw'
EQUIPPED = 'Ply' # There are two classifications for equipped lifters,
                # single-ply and multi-ply. In this program I lump them into
                # one group by their shared suffix

# Lifts
SQUAT = 'squat'
BENCH = 'bench'
DEADLIFT = 'deadlift'
TOTAL = 'total'

# Possible values for each category
CATEGORY_VALUES = {GENDER: (FEMALE, MALE),
                   PROFESSIONAL_STATUS: (AMATEUR, PROFESSIONAL),
                   EQUIPMENT: (RAW, EQUIPPED)}

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

FORMAT_DICTIONARY = {GENDER: GENDER_COLUMN,
                    PROFESSIONAL_STATUS: PROFESSIONAL_STATUS_COLUMN,
                    EQUIPMENT: EQUIPMENT_COLUMN,
                    SQUAT: SQUAT_COLUMN,
                    BENCH: BENCH_COLUMN,
                    DEADLIFT: DEADLIFT_COLUMN}

def parse_row(row):
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
    results_dictionary = {field: get_data_from_table(row, field_column) \
        for field, field_column in FORMAT_DICTIONARY.items()}

    if squat and bench and deadlift: # Valid entries for each lift in row
        results_dictionary[TOTAL] = squat + bench + deadlift
    else:
        results_dictionary[TOTAL] = None

    return results_dictionary

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
    table_empty_string = "SELECT COUNT(*) from %s" % table

    create_table_string = """CREATE TABLE if not exists %s (
    lifter_id INTEGER PRIMARY KEY, gender TEXT,
    professional_status TEXT, equipment TEXT, squat REAL,
    bench REAL, deadlift REAL, total REAL)
    """ % table

    result_storage_string = """INSERT INTO meet_results (
    gender,
    professional_status,
    equipment,
    squat,
    bench,
    deadlift,
    total)

    Values (
    :gender,
    :professional_status,
    :equipment,
    :squat,
    :bench,
    :deadlift,
    :total
    )
    """
    connection = sq.connect(database)
    cursor = connection.cursor()
    cursor.execute(create_table_string)
    cursor.execute(table_empty_string)

    # Here cursor returns a list containing the number of rows in the table
    # I access that number with [0]
    meet_results_table_populated = cursor.fetchone()[0]

    # Don't attempt to add data to table unless empty
    if meet_results_table_populated:
        return

    page = urllib2.urlopen(webpage)
    soup = BeautifulSoup(page, 'html.parser')
    meet_results_table = soup.find_all('tr') # all rows of meet results table,
                                             # each corresponds to an
                                             # individual's performance at the
                                             # meet
    for row in meet_results_table: # information for one lifter
        result_and_categories = parse_row(row)
        if result_and_categories: # row contains results of meet
            cursor.execute(result_storage_string, result_and_categories)

    connection.commit()
    connection.close()

####### Pandas functions
def find_percentile(lifts_df, user_lifts):
    """
    Finds the percentile of the input squat, bench, deadlift and total numbers
    among the sample of results in the database.

    Parameters:
    -----------
    lifts_df: pandas dataframe
        Dataframe containing squat, bench, deadlift, and/or total numbers
        against which to compare the input numbers.
    user_lifts: dictionary with string keys and float (or None) values
        A dictionary that contains keys ('squat', 'bench', 'deadlift', 'total').
        The values are floats representing someone's performance in the lift.

    Returns:
    --------
    percentile: dictionary with string keys string values
        Dictionary where key is one of "squat", "bench", and "deadlift" and
        the value is either a string relaying the input lifts percentile
        among the lifts in the database, or "N/A" if a valid number was not
        input for the lift.

    """
    percentiles = {SQUAT: None, BENCH: None, DEADLIFT: None}
    for lift in (SQUAT, BENCH, DEADLIFT, TOTAL):
        if isinstance(user_lifts[lift], numbers.Real): # valid numeric entry for lift
            entered_lift = user_lifts[lift]
            all_competitor_lifts = lifts_df[lift]
            number_of_lifts = all_competitor_lifts.count()
            number_of_smaller_lifts = all_competitor_lifts[all_competitor_lifts < entered_lift].count()
            percentile = (float(number_of_smaller_lifts)/number_of_lifts) * 100
            percentiles[lift] = ("%4.2f" % percentile) + " percentile"
        else: # no lift was entered
            percentiles[lift] = "N/A"
    return percentiles

def get_population_by_categories(connection, table, categories):
    """
    Returns a dataframe containing the powerlifting results of the people who
    fit the input categories.
    Parameters:
    -----------
    connection: sqlite3 connection object
        Connection to the database containing desired table
    table: string
        string specifying the name of the table containing desired
        powerlifting meet results
    categories: dictionary
        Contains values for gender, professional_status, and equipment
        fields to use to query the table
    Returns:
    --------
    population_dataframe: pandas dataframe
        dataframe containing the meet results of all lifters who fit the
        input criteria.

    """
    get_population_string = """Select * from {table}
        WHERE gender LIKE "{gender}%" AND
        professional_status LIKE "{professional_status}%" and
        equipment LIKE "{equipment}%";
        """.format(table=table,**categories)
    cursor = connection.cursor()
    population_database = cursor.execute(get_population_string)
    population_dataframe = pd.read_sql(get_population_string, connection)
    return population_dataframe

def get_categories_from_user():
    """
    Prompts users for information on their gender, professional status, and
    equipment category that they compete in. Returns a dictionary containing
    the user's responses.
    Returns:
    --------
    user_categories: dictionary
        A dictionary with category names ('gender', 'professional_status'
        and 'equipment') as keys and the users responses as values.

    """
    print "Please respond to the following prompts. "
    gender = 'gender'
    professional_status = 'professional_status'
    equipment = 'equipment'
    user_categories = {GENDER: None, PROFESSIONAL_STATUS: None, EQUIPMENT: None}
    for category_name, accepted_values in CATEGORY_VALUES.iteritems():
        prompt_for_category = "What is your %s? Please enter one of %r, " \
            % (category_name, accepted_values) + " or press Return to be " + \
            "compared to both."
        while True:
            response = raw_input(prompt_for_category)
            # User should either enter the category they want to be compared
            # against, or an empty string to be compared to both.  If their
            # response was not one of these, prompt them to try again.
            if response not in accepted_values and response:
                print "Your entry was not valid.  Please try again."
                continue
            user_categories[category_name] = response
            break
    return user_categories


def get_lifts_from_user():
    """
    Prompts users for information on their lifts.  Returns a dictionary
    containing the user's responses.
    Returns:
    --------
    lifts: dictionary
        A dictionary with lift names ('squat', 'bench', 'deadlift') and
        'total' as keys and the users responses as values, with the exception
        of lifts['total'].  The lifters total is calculated and loaded into
        the dictionary if valid numeric values were given for all three lifts,
        and None is loaded for the total if there are missing values.

    """
    print "Please enter your lifts below in lbs."
    lifts = {SQUAT: None, BENCH: None, DEADLIFT: None}
    for lift in lifts:
        prompt_for_lift = "What is your %s? Hit return to skip this lift." \
            % lift
        while True:
            try:
                response = raw_input(prompt_for_lift)
                if not response: # user entered empty string
                    response = None
                    break
                response = float(response)
                if response < 0: # user is a smartass
                    print "Don't be so hard on yourself.  Please answer seriously."
                    continue
                if response > 1500: # lift is higher than world records,
                                    # user is lying or is superman
                    print "Okay Ronnie Coleman ... I'll ask you one more time."
                    continue
            except ValueError: # user didn't enter a number
                print "You did not enter a number.  Please try again."
            else:
                lifts[lift] = response
                break
    user_entered_lifts = [lifts[SQUAT], lifts[BENCH], lifts[DEADLIFT]]
    # True if user entered valid numbers for all lifts, False otherwise
    valid_entries_for_all_lifts = \
        reduce(lambda x, y: isinstance(x, numbers.Real) \
        and isinstance(y, numbers.Real), user_entered_lifts)
    if valid_entries_for_all_lifts:
        lifts[TOTAL] = lifts[SQUAT] + lifts[BENCH] + lifts[DEADLIFT]
    else:
        lifts[TOTAL] = None
    return lifts

def main():
    populate_database(QUOTE_PAGE, DATABASE, MEET_RESULTS_TABLE)
    connection = sq.connect(DATABASE)
    categories = get_categories_from_user()
    lifts = get_lifts_from_user()
    competition = get_population_by_categories(connection, MEET_RESULTS_TABLE, categories)
    print competition
    percentiles = find_percentile(competition, lifts)
    print percentiles
    connection.close()

########################
if __name__ == "__main__":
    main()
