# Read strandr.tmp csv file to python dictionary
import csv


def readcsv(file):
    reader = csv.DictReader(open(file, newline=''),
                            delimiter=' ', quotechar='"')
    dictobj = next(reader)
    return (dictobj)

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

# Function: suggest new eventID
def newEventID(eventID_list, prefix):
    while True:
        try:
            tmp = [i for i in eventID_list if f'{prefix}_A' == i[0:5]]
            tmp2 = []
            for i in tmp:
                tmp2.append(int(i[5:15]))
            tmp2.sort(reverse=True)
            return f'{prefix}_A{tmp2[0]+1:04d}'
        except:
            return f'{prefix}_A0001'
