import arcpy, os, errno, datetime

#: Notes: use python3

#: Create a folder based on the date (ie: Year_Month_Day = 2021_1_15)
now = datetime.datetime.now()
year = now.year
month = now.month
day = now.day
folder_name = str(year) + "_" + str(month) + "_" + str(day)
#: create the folder
directory = "C:\\Users\\gbunce\\Documents\\projects\\vista\\civix_data\\" + folder_name
try:
    os.makedirs(directory)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

# set this folder as the work env
arcpy.env.workspace = directory
internal_sgid_connection = "C:\\Users\\gbunce\\AppData\\Roaming\\ESRI\\ArcGISPro\\Favorites\\internal@sgid@internal.agrc.utah.gov.sde"
sgid_vpcts = internal_sgid_connection + "\\SGID.POLITICAL.VistaBallotAreas"
sgid_counties = internal_sgid_connection + "\\SGID.BOUNDARIES.Counties"
sgid_congdist = internal_sgid_connection + "\\SGID.POLITICAL.USCongressDistricts2012"
sgid_utahhouse = internal_sgid_connection + ""
sgid_utahsenate = internal_sgid_connection + ""
sgid_muni = internal_sgid_connection + ""
sgid_judicial = internal_sgid_connection + ""
sgid_schooldist = internal_sgid_connection + ""

#: create civix shapefile
print("createing new civix shapefile")
arcpy.CreateFeatureclass_management(directory, "utah_vp_civix.shp", "POLYGON", 
                                    "", "DISABLED", "DISABLED", 
                                    "wgs84_projection.prj")

#: add fields using civix schema
print("adding fields to new civix shapefile")
arcpy.AddField_management("utah_vp_civix.shp", "COUNTY_NAM", "TEXT", field_length=100,
                          field_alias="County Name", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "COUNTY_NUM", "TEXT", field_length=25,
                          field_alias="County Number", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "PRECINCT", "TEXT", field_length=25,
                          field_alias="County Precinct", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "CITY_EST", "TEXT", field_length=25,
                          field_alias="Municipal Precinct", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "DIST_CONG", "TEXT", field_length=25,
                          field_alias="US Congressional District", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "DIST_STASS", "TEXT", field_length=25,
                          field_alias="State House District", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "DST_JRC", "TEXT", field_length=25,
                          field_alias="Judicial District", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "DST_USD", "TEXT", field_length=25,
                          field_alias="School District", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "DIST_BEQ", "TEXT", field_length=25,
                          field_alias="County Commissioner District", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "DIST_SUP", "TEXT", field_length=25,
                          field_alias="City Council District", field_is_nullable="NULLABLE")

#: gather the needed sgid staging data
print("importing sgid vista ballot areas to local directory")
arcpy.FeatureClassToFeatureClass_conversion(sgid_vpcts, directory, "sgid_pcts.shp")

arcpy.AddField_management("sgid_pcts.shp", "PRECINCT", "TEXT", field_length=50, field_is_nullable="NULLABLE")
print("calculate the PRECINCT (uniqueid) field based on countyid and vistaid")
arcpy.CalculateField_management("sgid_pcts.shp", "PRECINCT", "str(!CountyID!) + str(!VistaID!)", "PYTHON3")

#: dissolve the sgid vista ballot areas based on county number and vistaid
print("dissolving sgid vista ballot areas based on countyid and vistaid")
arcpy.Dissolve_management("sgid_pcts.shp", "sgid_pcts_dissolved.shp",
                          "PRECINCT", "", "MULTI_PART", 
                          "DISSOLVE_LINES")


#: SPATIAL JOINS (notes: the field mapping section is semi-colon delimeted - we're also renaming some fields in the field mapping piece (at the begining of the line))
#: spatially join the countyid and countyname
print("spatially join countyid and countyname from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved.shp", sgid_counties, "sgid_pcts_dissolved_spjoin1.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,sgid_counties,COUNTYNBR,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,sgid_counties,NAME,0,100',
"HAVE_THEIR_CENTER_IN", None, '')

#: spatially join the congressional district 2012
print("spatially join congressional district 2012 from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved_spjoin1.shp", sgid_congdist, "sgid_pcts_dissolved_spjoin2.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin1.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin1.shp",COUNTY_NUM,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin1.shp",COUNTY_NAM,0,100;DIST_CONG "DIST_CONG" true true false 2 Short 0 5,First,#,sgid_congdist,DISTRICT,-1,-1',
"HAVE_THEIR_CENTER_IN", None, '')


#: APPEND THE JOINED DATA TO THE CIVIX SCHEMA
print("append the intermediate spatially joined data to the final output civix schema")
arcpy.Append_management("sgid_pcts_dissolved_spjoin2.shp", "utah_vp_civix.shp", "NO_TEST")
