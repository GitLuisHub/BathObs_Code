# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os
import pandas as pd
import arcpy
import requests
import geopandas
from shapely.geometry import Point
from StringIO import StringIO
from datetime import datetime


   
# =============================================================================
# FUNCTIONS
# =============================================================================
 

def removeNaN(dataframe,filterWord):
    subsetColumns = list(dataframe.filter(regex=(filterWord))) #Look at columns for invertebrates
    dataframe_edited = dataframe.dropna(subset=subsetColumns, how='all') #If all columns are NaN remove row from dataframe
    return dataframe_edited

def replaceHeader(dataframe,headerRow,dataStart):
    new_header = dataframe.iloc[headerRow] #grab the row for the header
    dataframe = dataframe[dataStart:] #take the data less the header row
    dataframe.columns = new_header #set the header row as the df header
    return dataframe

def panda_to_shp(file_name, dataframe,data_origin):
    import copy
    df_copy = copy.deepcopy(dataframe) # create copy of the original dataframe to avoid any errors
    if (data_origin == 'inaturalist'): 
        root_archive = r"D:\LuisData\Personal\BathSpa\Data\SHP"
        shp = root_archive + os.sep + file_name + datetime.now().strftime("%Y%m%d") + ".shp"
        df_copy['geometry'] = df_copy.apply(lambda x: Point((float(x.longitude), float(x.latitude))), axis=1) # Create extra column with geometry and the coordinates
        df_copy = geopandas.GeoDataFrame(df_copy,geometry='geometry') # Create the geodataframe
        df_copy.crs = {'init' :'epsg:4326'} # Set the coordinate systems to WGS84 for geodataframe
        ShapeFile = df_copy.to_file(shp, driver='ESRI Shapefile') # Create the shapefile
        return shp
    else:
        root_archive = r"D:\LuisData\Personal\BathSpa\Data\SHP"
        shp = root_archive + os.sep + file_name + datetime.now().strftime("%Y%m%d") + ".shp"
        df_copy['geometry'] = df_copy.apply(lambda x: Point((float(x.X), float(x.Y))), axis=1) # Create extra column with geometry and the coordinates
        df_copy = geopandas.GeoDataFrame(df_copy,geometry='geometry') # Create the geodataframe
        df_copy.crs = {'init' :'epsg:27700'} # Set the coordinate systems to WGS84 for geodataframe
        df_copy.to_crs(epsg=4326)
        ShapeFile = df_copy.to_file(shp, driver='ESRI Shapefile') # Create the shapefile
        return shp

def shp_to_fc(shp_path,fc_name):
    root_gdb = r"D:\LuisData\Personal\BathSpa\Data\bath_obs.gdb"
    if arcpy.Exists(root_gdb + os.sep + 'inaturalist'):
        arcpy.Delete_management(root_gdb + os.sep + fc_name) # Delete if feature class already exists   
    arcpy.FeatureClassToFeatureClass_conversion(shp_path, root_gdb + os.sep, fc_name) # Create the new feature class

def projection(bng_shp,wgs84_shpName):
    root_gdb = r"D:\LuisData\Personal\BathSpa\Data\bath_obs.gdb"
    input_features = bng_shp # input data is in NAD 1983 UTM Zone 11N coordinate system
    output_feature_class = root_gdb + os.sep + wgs84_shpName # output data
    out_coordinate_system = arcpy.SpatialReference(4326) # create a spatial reference object for the output coordinate system
    arcpy.Project_management(input_features, output_feature_class, out_coordinate_system) # run the tool
   
# =============================================================================
# START OF CODE
# =============================================================================
 
try:
    startTime = datetime.now()
   
    # =============================================================================
    # WORKING WITH INATURALIST DATA
    # =============================================================================
    inat_data = raw_input("Enter path to the csv file i.e. c:\\files\\file.csv:    ")
    google_data = raw_input("Enter URL for google sheet:    ")
    print ' Starting with inaturalist data...'
    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'
        
####    Reading file
    df = pd.read_csv(inat_data)

####    Cleansing the data from unnecesary columns
    inaturalist_data=df.drop(['observed_on_string','time_zone','out_of_range', 'user_id', 
                       'user_login', 'created_at', 'updated_at','url',
                       'tag_list','id_please','captive_cultivated', 'oauth_application_id', 
                       'place_guess','coordinates_obscured', 'positioning_method', 
                       'positioning_device', 'species_guess'], axis=1)
       
    # =============================================================================
    # TRANSFORMING THE DATA FRAME TO A FEATURE CLASS 
    # =============================================================================
    print ' Creating inaturalist feature class...'
    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'
    
####    Creating Shapefile
    inat_shp = panda_to_shp('inaturalist',inaturalist_data,'inaturalist')
        
####    Conver Shapefile to Feature class
    shp_to_fc(inat_shp,'inaturalist')
        
    print ' inaturalist feature class created...'
    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'


    # =============================================================================
    # WORKING WITH GOOGLE SHEET DATA
    # =============================================================================
    print ' Starting with google sheet data...'
    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'
####    Get access to the google sheet
    gData = requests.get(google_data)
    data = gData.content

####    Read data as csv file
    df = pd.read_csv(StringIO(data))

####    Create dataframes for invertebrates and water quality
    df_inv = df.filter(regex=("GEN|INV"))
    df_wq = df.filter(regex=("GEN|WQ"))
    
####    Dropping NaN Values - Removes rows where all columns for Inv or WQ are NaN
    df_invEdited = removeNaN(df_inv,"INV")
    df_wqEdited = removeNaN(df_wq,"WQ")
    
####    Fixing headers - Set the right headers for the Inv and WQ dataframes
    inv_final = replaceHeader(df_invEdited,2,3)
    wq_final = replaceHeader(df_wqEdited,0,1)

####    Removing rows without coordinates
    inv_df = removeNaN(inv_final,"X|Y")
    wq_df = removeNaN(wq_final,"X|Y")
    
    print ' Creating google sheet feature class...'
    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'


    # =============================================================================
    # TRANSFORMING THE DATA FRAME TO A FEATURE CLASS 
    # =============================================================================
    print ' Creating inaturalist feature class...'
    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'
    
####    Creating Shapefile
    inv_shp = panda_to_shp('bsu_obs_water_inv',inv_df,'google_sheet')
    wq_shp = panda_to_shp('bsu_obs_water_wq',wq_df,'google_sheet')

####    Change coordinate system from BNG to WGS84 and save as feature class
    projection(inv_shp,'inv_shp_wgs84')
    projection(wq_shp,'wq_shp_wgs84')
    
        
    print ' bsu_obs_water feature classes created...'
    print '--------------------------'  
    print '--------------------------' 
    print '--------------------------'


except:
    print 'wrong, read below'
    raise

print ' Done!'
print '--------------------------'  
print '--------------------------' 
print '--------------------------'  
print 'Time running the script' + ' ' + str(datetime.now() - startTime)



#print data
#print result


