#! /usr/bin/Rscript --vanilla

# Input variables
args=commandArgs(trailingOnly=TRUE)
LAT = as.numeric(args[1])
LON = as.numeric(args[2])

# Strand function
tmp = strandr::strandr(lat=LAT,lon=LON)

# Print to st. output
cat(unlist(tmp[,2:5]), sep=",")