import arcpy, os, shutil, zipfile, glob

####: Notes: Use arcgispro-py3
####: Notes: Update the latest_civix_shapefile variable to the newest data.
latest_civix_shapefile = 'C:\\Users\\gbunce\\Documents\\projects\\vista\\civix_data\\2021_4_27\\utah_vp_civix.shp'
shapefile_directory = latest_civix_shapefile.rsplit('\\', 1)[0]


#### BEGIN >>> Zip Shapefile function ####
def ZipShp (inShp, Delete = True):
 
    """
    Creates a zip file containing the input shapefile
    inputs -
    inShp: Full path to shapefile to be zipped
    Delete: Set to True to delete shapefile files after zip
    """
     
    #List of shapefile file extensions
    extensions = [".shp",
                  ".shx",
                  ".dbf",
                  ".sbn",
                  ".sbx",
                  ".fbn",
                  ".fbx",
                  ".ain",
                  ".aih",
                  ".atx",
                  ".ixs",
                  ".mxs",
                  ".prj",
                  ".xml",
                  ".cpg",
                  ".shp.xml"]
 
    #Directory of shapefile
    inLocation = arcpy.Describe (inShp).path
    #Base name of shapefile
    inName = arcpy.Describe (inShp).baseName
    #Create zipfile name
    zipfl = os.path.join (inLocation, inName + "_shp.zip")
    #Create zipfile object
    ZIP = zipfile.ZipFile (zipfl, "w")
     
    #Iterate files in shapefile directory
    for fl in os.listdir (inLocation):
        #Iterate extensions
        for extension in extensions:
            #Check if file is shapefile file
            if fl == inName + extension:
                #Get full path of file
                inFile = os.path.join (inLocation, fl)
                #Add file to zipfile
                ZIP.write (inFile, fl)
                break
 
    #Delete shapefile if indicated
    if Delete == True:
        arcpy.Delete_management (inShp)
 
    #Close zipfile object
    ZIP.close()
 
    #Return zipfile full path
    return zipfl
#### Zip Shapefile function  <<< END ####



#: Get unique list of values (county names)
with arcpy.da.SearchCursor(latest_civix_shapefile,"COUNTY_NAM") as SCur:
    county_names = []
    for row in SCur:
        if not row[0] in county_names: # if not in list then add to list
            county_names.append(row[0])

#: Loop through each county and export to shapefile and then zip
for county in county_names:
    inFeatures = latest_civix_shapefile
    outLocation = shapefile_directory + "\\"
    outFeatureClass = "utah_vp_civix_" + county + ".shp"
    expression = "COUNTY_NAM = '" + county + "'"
 
    #: Execute FeatureClassToFeatureClass
    arcpy.FeatureClassToFeatureClass_conversion(inFeatures, outLocation, outFeatureClass, expression)

    # zip the shapefile
    ZipShp(outLocation + "\\" + outFeatureClass, False)