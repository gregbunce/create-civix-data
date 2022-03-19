import arcpy, os, errno, datetime

#: Notes: use arcgispro-py3

#: Create a folder based on the date (ie: Year_Month_Day = 2021_1_15)
now = datetime.datetime.now()
year = now.year
month = now.month
day = now.day
folder_name = str(year) + "_" + str(month) + "_" + str(day)
#: create the output folder one directory up from the current
directory = "..\\" + folder_name
try:
    os.makedirs(directory)
except OSError as e:
    if e.errno != errno.EXIST:
        raise

# set this folder as the work env
arcpy.env.workspace = directory
internal_sgid_connection = "C:\\Users\\gbunce\\AppData\\Roaming\\ESRI\\ArcGISPro\\Favorites\\internal@sgid@internal.agrc.utah.gov.sde"
sgid_vpcts = internal_sgid_connection + "\\SGID.POLITICAL.VistaBallotAreas"
sgid_counties = internal_sgid_connection + "\\SGID.BOUNDARIES.Counties"
sgid_congdist = internal_sgid_connection + "\\SGID.POLITICAL.USCongressDistricts2022to2032"
sgid_utahhouse = internal_sgid_connection + "\\SGID.POLITICAL.UtahHouseDistricts2022to2032"
sgid_utahsenate = internal_sgid_connection + "\\SGID.POLITICAL.UtahSenateDistricts2022to2032"
sgid_muni = internal_sgid_connection + "\\SGID.BOUNDARIES.Municipalities"
sgid_judicial = internal_sgid_connection + "\\SGID.POLITICAL.JudicialDistricts"
sgid_schoolboarddist = internal_sgid_connection + "\\SGID.POLITICAL.UtahSchoolBoardDistricts2022to2032"

#: create civix, electionet shapefile
print("createing new civix shapefile")
arcpy.CreateFeatureclass_management(directory, "utah_vp_civix.shp", "POLYGON", 
                                    "", "DISABLED", "DISABLED", 
                                    "WGS84_4326.prj")

#: add fields using civix schema
print("adding fields to new civix shapefile")
arcpy.AddField_management("utah_vp_civix.shp", "COUNTY_NAM", "TEXT", field_length=100,
                          field_alias="County Name", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "COUNTY_NUM", "TEXT", field_length=25,
                          field_alias="County Number", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "PRECINCT", "TEXT", field_length=25,
                          field_alias="County Precinct", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "CITY_EST", "TEXT", field_length=100,
                          field_alias="Municipal Precinct", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "DIST_CONG", "TEXT", field_length=25,
                          field_alias="US Congressional District", field_is_nullable="NULLABLE")
arcpy.AddField_management("utah_vp_civix.shp", "DIST_STSEN", "TEXT", field_length=25,
                          field_alias="State Senate District", field_is_nullable="NULLABLE")
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
#arcpy.CalculateField_management("sgid_pcts.shp", "PRECINCT", "str(!CountyID!) + str(!VistaID!)", "PYTHON3") #this was the original way they wanted the data.
arcpy.CalculateField_management("sgid_pcts.shp", "PRECINCT", "str(!VistaID!)", "PYTHON3")

#: dissolve the sgid vista ballot areas based on county number and vistaid
print("dissolving sgid vista ballot areas based on countyid and vistaid")
arcpy.Dissolve_management("sgid_pcts.shp", "sgid_pcts_dissolved.shp",
                          ["CountyID", "PRECINCT"], "", "MULTI_PART", 
                          "DISSOLVE_LINES")

#: convert the voting precincts shapefile into points using 'feature to point' (use centroid, with point "inside" polygon). the step will ensure the districts get assigned correctly (using the point within the polygon)
print("converting polygon voting precincts to points")
arcpy.FeatureToPoint_management("sgid_pcts_dissolved.shp", "sgid_pcts_dissolved_points.shp", "INSIDE")

# .....DO WORK HERE..... (change below code to use the point features)



#: SPATIAL JOINS (notes: the field mapping section is semi-colon delimeted - we're also renaming some fields in that piece (at the begining of the mapping string for that field). it' easier to view the field mapping as separate lines and then pull them back together before running the script)
#: spatially join countyid and countyname
print("spatially join countyid and countyname from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved_points.shp", sgid_counties, "sgid_pcts_dissolved_spjoin1.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,sgid_counties,COUNTYNBR,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,sgid_counties,NAME,0,100',"HAVE_THEIR_CENTER_IN", None, '')

#: spatially join congressional district 2022 to 2032
print("spatially join congressional district 2022 to 2032 from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved_spjoin1.shp", sgid_congdist, "sgid_pcts_dissolved_spjoin2.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin1.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin1.shp",COUNTY_NUM,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin1.shp",COUNTY_NAM,0,100;DIST_CONG "DIST_CONG" true true false 2 Short 0 5,First,#,sgid_congdist,DISTRICT,-1,-1',"HAVE_THEIR_CENTER_IN", None, '')

#: spatially join utah state senate 2022 to 2032
print("spatially join utah state senate 2022 to 2032 from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved_spjoin2.shp", sgid_utahsenate, "sgid_pcts_dissolved_spjoin3.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin2.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin2.shp",COUNTY_NUM,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin2.shp",COUNTY_NAM,0,100;DIST_CONG "DIST_CONG" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin2,DIST_CONG,-1,-1;DIST_STSEN "DIST_STSEN" true true false 2 Short 0 5,First,#,sgid_utahsenate,DIST,-1,-1',"HAVE_THEIR_CENTER_IN", None, '')

#: spatially join utah state house 2022 to 2032
print("spatially join utah state house 2022 to 2032 from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved_spjoin3.shp", sgid_utahhouse, "sgid_pcts_dissolved_spjoin4.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin3.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin3.shp",COUNTY_NUM,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin3.shp",COUNTY_NAM,0,100;DIST_CONG "DIST_CONG" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin3,DIST_CONG,-1,-1;DIST_STSEN "DIST_STSEN" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin3,DIST_STSEN,-1,-1;DIST_STASS "DIST_STASS" true true false 2 Short 0 5,First,#,sgid_utahhouse,DIST,-1,-1',"HAVE_THEIR_CENTER_IN", None, '')

#: spatially join municipalities
print("spatially join utah muni from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved_spjoin4.shp", sgid_muni, "sgid_pcts_dissolved_spjoin5.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin4.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin4.shp",COUNTY_NUM,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin4.shp",COUNTY_NAM,0,100;DIST_CONG "DIST_CONG" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin4,DIST_CONG,-1,-1;DIST_STSEN "DIST_STSEN" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin4,DIST_STSEN,-1,-1;DIST_STASS "DIST_STASS" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin4,DIST_STASS,-1,-1;CITY_EST "CITY_EST" true true false 100 Text 0 0,First,#,sgid_muni,SHORTDESC,0,100',"HAVE_THEIR_CENTER_IN", None, '')

#: spatially join judicial districts
print("spatially join judicial from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved_spjoin5.shp", sgid_judicial, "sgid_pcts_dissolved_spjoin6.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin5.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin5.shp",COUNTY_NUM,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin5.shp",COUNTY_NAM,0,100;DIST_CONG "DIST_CONG" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin5,DIST_CONG,-1,-1;DIST_STSEN "DIST_STSEN" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin5,DIST_STSEN,-1,-1;DIST_STASS "DIST_STASS" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin5,DIST_STASS,-1,-1;CITY_EST "CITY_EST" true true false 100 Text 0 0,First,#,sgid_pcts_dissolved_spjoin5,CITY_EST,0,100;DST_JRC "DST_JRC" true true false 10 Text 0 0,First,#,sgid_judicial,DISTRICT,0,10',"HAVE_THEIR_CENTER_IN", None, '')

#: spatially join school board districts 2022 to 2032
print("spatially join school board districts from sgid county layer")
arcpy.analysis.SpatialJoin("sgid_pcts_dissolved_spjoin6.shp", sgid_schoolboarddist, "sgid_pcts_dissolved_spjoin7.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL",
r'PRECINCT "PRECINCT" true true false 50 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin6.shp",PRECINCT,0,50;COUNTY_NUM "COUNTY_NUM" true true false 2 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin6.shp",COUNTY_NUM,0,2;COUNTY_NAM "COUNTY_NAM" true true false 100 Text 0 0,First,#,"sgid_pcts_dissolved_spjoin6.shp",COUNTY_NAM,0,100;DIST_CONG "DIST_CONG" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin6,DIST_CONG,-1,-1;DIST_STSEN "DIST_STSEN" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin6,DIST_STSEN,-1,-1;DIST_STASS "DIST_STASS" true true false 2 Short 0 5,First,#,sgid_pcts_dissolved_spjoin6,DIST_STASS,-1,-1;CITY_EST "CITY_EST" true true false 100 Text 0 0,First,#,sgid_pcts_dissolved_spjoin6,CITY_EST,0,100;DST_JRC "DST_JRC" true true false 10 Text 0 0,First,#,sgid_pcts_dissolved_spjoin6,DST_JRC,0,10;DST_USD "DST_USD" true true false 60 Text 0 0,First,#,sgid_schoolboarddist,DIST,0,60',"HAVE_THEIR_CENTER_IN", None, '')

#: Joint the point data back to polygons (join sgid_pcts_dissolved.shp (polygon) to sgid_pcts_dissolved_spjoin7.shp (point)).
sgid_pct_dissolved_joined = arcpy.JoinField_management(in_data="sgid_pcts_dissolved.shp", in_field="FID", join_table="sgid_pcts_dissolved_spjoin7.shp", join_field="TARGET_FID", fields="FID;Join_Count;TARGET_FID;PRECINCT;COUNTY_NUM;COUNTY_NAM;DIST_CONG;DIST_STSEN;DIST_STASS;CITY_EST;DST_JRC;DST_USD")

#: APPEND THE JOINED DATA TO THE CIVIX SCHEMA (use the last spatially joined output file for the input)
print("append the intermediate spatially joined data to the final output civix schema")
arcpy.Append_management(sgid_pct_dissolved_joined, "utah_vp_civix.shp", "NO_TEST")
