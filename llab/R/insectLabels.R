# insectLabels, Jon Peder Lindemann, 22.02.2021
# Print insectlabels from database query
# CONN | SQLite database connection
# event_id | a vector or character string, specifying eventIDs of collecting events to be printed
# filename | character string, specifying file name of output pdf




insectLabels <- function(CONN, 
                         event_id, 
                         n = 1, 
                         filename = "insectlabels.pdf", 
                         type = "chalc",
                         font_family = "sans") {

  # Make SQL query for each collecting event
  query = NULL
  for (i in 1:length(event_id)) {
    query_tmp <- dbGetQuery(CONN, paste("SELECT
      Collecting_events.eventID,
      Collecting_events.countryCode,
      Collecting_events.stateProvince,
      Collecting_events.strand_id,
      Collecting_events.municipality,
      Collecting_events.locality_1,
      Collecting_events.locality_2,
      Collecting_events.habitat,
      Collecting_events.decimalLatitude,
      Collecting_events.decimalLongitude,
      Collecting_events.coordinateUncertaintyInMeters,
      Collecting_methods.samplingProtocol,
      Collecting_events.eventDate_1,
      Collecting_events.eventDate_2,
      Collecting_events.recordedBy
      FROM Collecting_events 
      INNER JOIN Collecting_methods 
      ON Collecting_methods.ID = Collecting_events.samplingProtocol
      WHERE Collecting_events.eventID = '", event_id[i], "'", sep = ""))
    if (isTRUE(exists("query"))) {
      query = rbind(query, query_tmp)
    } else { query = query_tmp}
  }

  # Add some details to some of the columns
  ## Concatenate StateProvince and CountryCode if stateProvince is recorded
  for (i in 1:nrow(query)){
    if (query$stateProvince[i] != "" & isFALSE(is.na(query$stateProvince[i]))) {
      query$countryCode[i] <- paste(query$countryCode[i], ", ", query$stateProvince[i], ": ", sep = "")
    }
  }
  ## Country in capital letters
  query$countryCode <- toupper(query$countryCode) 
  ## Add "±" and "m" to radius if radius is recorded
  for (i in 1:nrow(query)){
    if (isFALSE(is.na(query$coordinateUncertaintyInMeters[i])) & query$coordinateUncertaintyInMeters[i] != "") {
      query$coordinateUncertaintyInMeters[i] <- paste("\u00B1",query$coordinateUncertaintyInMeters[i],"m",sep = "") 
    }
  }
  ## Add colon after method
  for (i in 1:nrow(query)) {
    if (query$samplingProtocol[i] != "")
      query$samplingProtocol[i] <- paste(query$samplingProtocol[i], ":", sep = "")
  }
  ## Add colon after municipality
  query$municipality <- paste(query$municipality, ":", sep = "") 
  # Put habitat within parenthesis where habitat is recorded
  for (i in 1:nrow(query)) {
    if (query$habitat[i] != "") {
      query$habitat[i] <- paste("(", query$habitat[i], ")", sep = "") 
    } 
  }
  for (i in 1:nrow(query)) {
    if (query$locality_2[i] != "" & query$locality_1 != "") {
      query$locality_1[i] <- paste(query$locality_1[i], ",", sep = "") # Add comma after Loc1 when Loc2 is present
    }
  }

  # If more than one collector (separated by '|'), use last names. Add "Leg." to beginning of strings
  for (i in 1:nrow(query)) {
    if (isTRUE(grep("\\|", query$recordedBy[i]) == 1)) {
      tmp <- gsub("^.* ", "", strsplit(query$recordedBy[i], " \\| |\\||\\| | \\|")[[1]])
      if (length(tmp) == 2) {
        query$recordedBy[i] <- paste("Leg. ", paste(tmp, collapse = " & ", sep = ""), sep = "")
      } else {
        query$recordedBy[i] <- paste("Leg. ", tmp[1], " et al.", sep = "")
      }
    } else {
      query$recordedBy[i] <- paste("Leg. ", query$recordedBy[i], sep = "") 
    }
  }
  
  # Create a date-column with concatinated eventDate_1 and eventDate_2
  query$eventDate <- ""
  for (i in 1:nrow(query)){
    tmp1 <- regexec("^([0-9]{4})-([0-9]{2})-([0-9]{2})", query$eventDate_1[i])
    year1 <- regmatches(query$eventDate_1[i], tmp1)[[1]][2]
    month1 <- regmatches(query$eventDate_1[i], tmp1)[[1]][3]
    date1 <- regmatches(query$eventDate_1[i], tmp1)[[1]][4]
    if (query$eventDate_2[i] != "") {
      tmp2 <- regexec("^([0-9]{4})-([0-9]{2})-([0-9]{2})", query$eventDate_2[i])
      year2 <- regmatches(query$eventDate_2[i], tmp2)[[1]][2]
      month2 <- regmatches(query$eventDate_2[i], tmp2)[[1]][3]
      date2 <- regmatches(query$eventDate_2[i], tmp2)[[1]][4]
      if (year1 == year2) {
        if (month1 == month2) {
          query$eventDate[i] <- paste(date1, "/", date2, ".", month2, ".", year2, sep = "")}
        else { query$eventDate[i] <- paste(date1, ".", month1, "/", date2, ".", month2, ".", year2, sep = "")}}
      else {query$eventDate[i] <- paste(date1, ".", month1, ".", year1, "/", date2, ".", month2, ".", year2, sep = "")}
    } else {query$eventDate[i] <- paste (date1, "." , month1, ".", year1, sep = "")}
  }
  
  if (type == "small") {
  # Write insect labels
  ## Chalcididae. Small labels with habitat 
  insectlabel::insectlabel(label_df = query, n = n, x = 55, y = 11, filename = filename, family = font_family, text_order = list(c(2, 3, 4, 5), c(6, 7), 8, c(9, 10, 11), c(12, 16), 15), 
                           QR_data = c(2,1), fontsize = 3.3, linedist = 0.95, tx = 11, ty = -1, QRd = 1.6, QRx = 4.4, 
                           QRy = 0, delim = ";", qrlevel = 0)
  }
  if (type == "medium") {
    ## Medium size labels with habitat
    insectlabel::insectlabel(label_df = query, n = n, x = 50, y = 10, filename = filename, family = font_family, text_order = list(c(2, 3, 4, 5), c(6, 7), 8, c(9, 10, 11), c(12, 16), 15), 
                             QR_data = c(2,1), fontsize = 3.3, linedist = 0.95, tx = 11, ty = -1, QRd = 1.6, QRx = 4.4, 
                             QRy = 0, delim = ";", qrlevel = 0)
  }
  if (type == "excl_habitat_s") {
  ## Mycetophilidae. Labels without habitat.
  insectlabel::insectlabel(label_df = query, n = n, x = 50, y = 10, filename = filename, family = font_family, text_order = list(c(2, 3, 4, 5), c(6, 7), c(9, 10, 11), c(12, 16), 15), 
                           QR_data = c(2,1), fontsize = 3.3, linedist = 0.95, tx = 11, ty = -1, QRd = 1.6, QRx = 4.4, 
                           QRy = 0, delim = ";", qrlevel = 0)
  }
  if (type == "excl_habitat_l") {
    ## Mycetophilidae. Labels without habitat.
    insectlabel::insectlabel(label_df = query, n = n, x = 40, y = 8, filename = filename, family = font_family, text_order = list(c(2, 3, 4, 5), c(6, 7), c(9, 10, 11), c(12, 16), 15), 
                             QR_data = c(2,1), fontsize = 3.4, linedist = 0.90, tx = 11, ty = -1, QRd = 1.6, QRx = 4.4, 
                             QRy = 0, delim = ";", qrlevel = 0)
  }
  if (type == "type") {
    ## Mycetophilidae. Labels without habitat.
    insectlabel::insectlabel(label_df = query, n = n, x = 40, y = 8, filename = filename, family = font_family, text_order = list(c(2,3,4,5),c(6,7),c(9,10,11),c(12,16),15,1), 
                             QR_data = c(2,1), font = c(1,1,1,1,1,2), fontsize = 3, linedist = 1, tx = 11, ty = -1, QRd = 1.6, QRx = 4.4, 
                             QRy = 0, delim = ";", qrlevel = 0)
  }
}
