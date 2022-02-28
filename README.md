# create-civix-data
This repo contains scripts for creating the data (zipped shapefiles) used in the Civix ElectioNet system

use arcgispro-py3

1. connect to state network to gain access to Internal SGID
2. run create_voting_precincts_civix.py
3. then, run export_by_county_and_zip_shpfile.py (remember to re-point the shapefile variable)
4. upload zipped shapefiles to google drive where the Civix team can access them
