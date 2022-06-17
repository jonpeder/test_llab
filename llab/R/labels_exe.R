#! /usr/bin/Rscript --vanilla

# Input variables
args=commandArgs(trailingOnly=TRUE)
eventIDs = unlist(strsplit(x=args[1], split=","))
labels_n = unlist(strsplit(x=args[2], split=","))
labeltype = args[3]



# Load functions
library(RSQLite)
tmu_db <- dbConnect(SQLite(), "/var/www/llab/llab/insects.db")
source("/var/www/llab/llab/R/insectLabels.R")
sysfonts::font_add_google("Quicksand", "quick")
showtext::showtext_auto()

# Plot labels
insectLabels(tmu_db, eventIDs, labels_n, filename = "/var/www/llab/llab/insect_labels/labels.pdf", type = labeltype, font_family = "quick")
