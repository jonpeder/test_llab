create table datasets (
    datasetName varchar(255) primary key,
    datasetDescription text,
    specimenIDs text,
    datasetManager varchar(255),
    rightsHolder varchar(255),
    license varchar(255),
    createdByUserID int,
    databased datetime default current_timestamp,
    foreign key (createdByUserID) references user(id)
);

create table drawers (
    drawerName varchar(25) primary key,
    databased datetime default current_timestamp,
    createdByUserID int,
    foreign key (createdByUserID) references user(id)
);

create table units (
    unitID varchar(80) primary key,
    drawerName varchar(25),
    createdByUserID int,
    taxonInt int,
    identificationQualifier varchar(10),
    sex varchar(6),
    databased datetime default current_timestamp,
    updated timestamp,
    foreign key (createdByUserID) references user(id),
    foreign key (drawerName) references drawers(drawerName)
);

create table unit_id_counter (
    id int NOT NULL AUTO_INCREMENT primary key
);


-- Queries to get full QR-data from Taxon labels
select distinct a.unit_id, b.identificationQualifier, b.sex, c.taxonInt from occurrences a inner join identification_events b on a.identificationID = b.identificationID inner join taxa c on b.scientificName = c.scientificName where a.unit_id is not NULL and a.unit_id != '' and a.unit_id != 'test' and a.unit_id != 'no-unit' and a.unit_id != 'unitid' and b.identificationQualifier is not NULL;
-- Queries to get full QR-data from Taxon labels
SELECT distinct
    CONCAT_WS(':', c.taxonInt, b.identificationQualifier, b.sex, a.unit_id) AS concatenated_result
FROM 
    occurrences a 
INNER JOIN identification_events b ON a.identificationID = b.identificationID 
INNER JOIN taxa c ON b.scientificName = c.scientificName 
WHERE 
    a.unit_id IS NOT NULL 
    AND a.unit_id != '' 
    AND a.unit_id != 'test' 
    AND a.unit_id != 'no-unit' 
    AND a.unit_id != 'unitid' 
    AND b.identificationQualifier IS NOT NULL;

-- Insert result from query to units-table
INSERT INTO units (unitID, drawerName, createdByUserID)
SELECT distinct
    CONCAT_WS(':', c.taxonInt, b.identificationQualifier, b.sex, a.unit_id) AS unitID,
    NULL AS drawerName,
    1 AS createdByUserID
FROM 
    occurrences a 
INNER JOIN identification_events b ON a.identificationID = b.identificationID 
INNER JOIN taxa c ON b.scientificName = c.scientificName 
WHERE 
    a.unit_id IS NOT NULL 
    AND a.unit_id != '' 
    AND a.unit_id != 'test' 
    AND a.unit_id != 'no-unit' 
    AND a.unit_id != 'unitid' 
    AND b.identificationQualifier IS NOT NULL;

-- Queries to update unit-id column in occurrences-table
UPDATE occurrences a
INNER JOIN (
    SELECT 
        a.identificationID,
        CONCAT_WS(':', c.taxonInt, b.identificationQualifier, b.sex, a.unit_id) AS concatenated_result
    FROM 
        occurrences a 
    INNER JOIN identification_events b ON a.identificationID = b.identificationID 
    INNER JOIN taxa c ON b.scientificName = c.scientificName
) AS subquery ON a.identificationID = subquery.identificationID
SET a.unit_id = subquery.concatenated_result;

-- Add det. prefix to unit-id columns
UPDATE occurrences
SET unit_id = CONCAT('det.', unit_id)
WHERE unit_id IS NOT NULL;

update units
set unitID = CONCAT('det.', unitID)

-- Fill inn taxonInt column in units-table from unitID
update units set taxonInt = SUBSTRING_INDEX(SUBSTRING_INDEX(unitID,":",1),".",-1);

-- Fill inn identificationQualifier column in units-table from unitID
update units set identificationQualifier = SUBSTRING_INDEX(SUBSTRING_INDEX(unitID,":",2),":",-1);

-- Fill inn sex column in units-table from unitID
update units set sex = SUBSTRING_INDEX(SUBSTRING_INDEX(unitID,":",3),":",-1);


-- Find all collecting events with that are not associated with any occurrence
SELECT REPLACE(eventID, "JPL_A", "JPL") FROM collecting_events WHERE eventID NOT IN (SELECT eventID FROM occurrences);
-- Replace eventID in collecting_events that are not associated with any occurrence
update collecting_events set eventID = REPLACE(eventID, "JPL_A", "JPL") WHERE eventID NOT IN (SELECT eventID FROM occurrences);
-- Replace eventID in event_images that are not associated with any occurrence
update event_images set eventID = REPLACE(eventID, "JPL_A", "JPL") WHERE eventID NOT IN (SELECT eventID FROM occurrences);