# Read strandr.tmp csv file to python dictionary
import os.path
import csv
from os import path
import sys
import subprocess
import time
import unittest

def readstrand(r_script_path, lat, lon):
    p = subprocess.Popen([r_script_path, lat, lon], encoding="Latin-1", stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, universal_newlines=True)
    p.wait()
    output = [l.strip() for l in p.stdout]
    output = str(output).replace("[", "").replace("]", "").replace("'", "").replace("<U+00E5>", "å").replace("<U+00C5>", "Å").replace("<U+00E6>", "æ").replace("<U+00C6>", "Æ").replace("<U+00D8>", "Ø").replace("<U+00F8>", "ø").replace("<U+0161>", "š").replace("<U+00E1>", "á").split(",")
    return(output)

def readcsv(file):
    reader = csv.DictReader(open(file, newline=''), delimiter=' ', quotechar='"')
    dictobj = next(reader)
    return(dictobj)

# Define query function
def query(conn, sql):
    c = conn.cursor()
    c.execute(sql)
    return c.fetchall()
    
# Define query function
def headers(conn, sql):
    # Create a cursor
    c = conn.cursor()
    # Execute query
    c.execute(sql)
    # Return headers
    return list(map(lambda x: x[0], c.description))


# Make function to suggest a new eventID
def newEventID(eventID_list, prefix):
    while True:
        try:
            tmp = [i for i in eventID_list if f'{prefix}_A' == i[0:5]]
            tmp2 = []
            for i in tmp:
                tmp2.append(int(i[5:15]))
            tmp2.sort(reverse=True)
            return f'{prefix}_A{tmp2[0]+1:04d}'
            break
        except:
            return f'{prefix}_A0001'


