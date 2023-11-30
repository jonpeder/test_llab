# Importing library
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol

# Make one method to decode the barcode
def BarcodeReader(image):

    # read the image in numpy array using cv2
    img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
    
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
        print("Barcode Not Detected!")
    else:
        # Print the barcode data
        print(set(test1_data).union(test2_data))
        
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
                
    #Display the image
    cv2.imshow("Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
# Take the image from user
    image="Img.jpg"
    BarcodeReader(image)
