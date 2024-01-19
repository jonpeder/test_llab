# Read strandr.tmp csv file to python dictionary
import csv
# Importing libraries for QrReader
import cv2
import numpy as np
import pandas as pd
import datetime as dt
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol


# Arrange data from db-query in dict for presentation in bar-plot
def bar_plot_dict(dataframe, gr, percentage):
    # Group occurrences by predefined group
    if gr == "year" or gr == "month" or gr == "yearmonth":
        dataframe["date"] = dataframe["date"].astype("datetime64[ns]")
        if gr == "month":
            gr = "date"
            group = dataframe[gr].groupby(dataframe["date"].dt.month).count()
        if gr == "year":
            gr = "date"
            group = dataframe[gr].groupby(dataframe["date"].dt.year).count()
        if gr == "yearmonth":
            gr = "date"
            group = dataframe[gr].groupby([dataframe["date"].dt.year, dataframe["date"].dt.month]).count()
    else:
        group = dataframe[gr].groupby(dataframe[gr]).count()
    # Create dataframe
    groups_df = pd.DataFrame({"count":list(group)}, index=list(group.index))
    groups_df = groups_df.sort_values(by=['count'])
    # Add percentages to new column
    groups_df['perc'] = groups_df['count']/groups_df['count'].sum()*100
    # Concatenate columns containing less than 5% of occurrences into new column called 'other'
    # Set percentage limit
    p = percentage
    # New column values
    other_sum = groups_df['count'][groups_df['perc']<p].sum()
    other_perc = groups_df['perc'][groups_df['perc']<p].sum()
    # Remove columns containing less than 5% of occurrences
    groups_df = groups_df[groups_df['perc']>p]
    groups_df.loc['Other groups'] = [other_sum, other_perc]
    # Sort rows by count
    groups_df = groups_df.sort_values(by=['count'])
    # Drop rows with empty index name
    if '' in groups_df.index:
        groups_df = groups_df.drop([''])
    # Drop other groups if count = 0
    if groups_df.loc["Other groups"]["count"] == 0:
        groups_df = groups_df.drop(["Other groups"])
    # Transform back to dict
    dict_out = {"label":list(groups_df.index), "count":list(groups_df["count"])}
    return(dict_out)


# Read CSV
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


# Make one method to decode thcone barcode
def BarcodeReader(image):

    # read the image in numpy array using cv2
    #img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
    img = image
    
    # Create two differently processed images
    test1 = img
    test2 = img
    # Image process 1 
    # Blur
    test1 = cv2.GaussianBlur(test1, (5, 5), 0.8)
    # Contrast
    alpha = 1.5 # Contrast control (1.0-3.0)
    beta = 0 # Brightness control (0-100)
    test1 = cv2.convertScaleAbs(test1, alpha=alpha, beta=beta)

    # Image process 2
    # Scale down
    scale = 0.4
    width = int(test1.shape[1] * scale)
    height = int(test1.shape[0] * scale)
    test2 = cv2.resize(test2, (width, height))
    # Binerize
    test2 = cv2.adaptiveThreshold(test2,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
    
    # Decode the barcode image
    # Decode test1
    decoded1 = decode(test1, symbols = [ZBarSymbol.QRCODE])
    test1_data = []
    for i in decoded1:
        test1_data.append(i.data)
    
    # Decode test2
    decoded2 = decode(test2, symbols = [ZBarSymbol.QRCODE])
    test2_data = []
    for i in decoded2:
        test2_data.append(i.data)
    
    

    # If not detected then print the message
    if not set(test1_data).union(test2_data):
        #print("Barcode Not Detected!")
        return ""
    else:
        # Print the barcode data
        #print(set(test1_data).union(test2_data))
        
        # Convert image from grayscale to color
        img=cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        # Polygon variables
        isClosed = True # Closed polygon
        color = (0, 0, 288) # Red color in BGR
        thickness = 10  # Line thickness of 2 px

        # Add detected barcodes
        for barcode in decoded1:  
            # Locate the barcode position in image
            (a, b, c, d) = barcode.polygon
            pts = np.array([[a.x, a.y], [b.x, b.y], [c.x, c.y], [d.x, d.y]],np.int32)
            img = cv2.polylines(img, [pts], isClosed, color, thickness)


        # Add barcodes detected from the down-scaled image
        scale=2.5
        for barcode in decoded2:  
            # Locate the barcode position in image
            (a, b, c, d) = barcode.polygon
            pts = np.array([[a.x*scale, a.y*scale], [b.x*scale, b.y*scale], [c.x*scale, c.y*scale], [d.x*scale, d.y*scale]], np.int32)
            img = cv2.polylines(img, [pts], isClosed, color, thickness)
        
        # Return combined barcode-data-sets and image with decoded barcodes
        return set(test1_data).union(test2_data), img
"""
    #Display the image
    cv2.imshow("Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
# Take the image from user
    image="Img.jpg"
    BarcodeReader(image)
"""