import os
from PIL import Image

# list all files in folder
files = os.listdir("specimens/")

for file in files:
	image = Image.open(os.path.join("specimens/", file))
	image.save(os.path.join("compressed/", file),quality=20,optimize=True)

