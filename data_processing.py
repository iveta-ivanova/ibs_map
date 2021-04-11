# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 09:09:21 2021

@author: Iveta
"""

'''

This script holds a record of the processing steps of both the geocoordinates 
and the order files. 

'''

import pandas as pd 
import geopandas as gpd
import pyodbc
'''
download coordinates
'''
import os 

os.chdir('C:\\Users\Iveta\Desktop\PROGRAMMING\IBSmap')


shapefile = '110m_coords/ne_110m_admin_0_countries.shp'
# read only the country name, iso2 code and geometry coordinates
gdf = gpd.read_file(shapefile)[['ADMIN', 'ISO_A2', 'geometry']]

'''
pre-processing geospatial data
'''
# rename columns 
gdf.columns = ['country','ISOA2_code','geometry']

# check which are the countries with a false ISO_A2 value
for country,code in (zip(gdf['country'], gdf['ISOA2_code'])): 
    try: 
        checkint = int(code)
        print(country, checkint)
    except ValueError: 
        pass

gdf.columns

# check the index by locating the row we want 
#gdf.loc[gdf['country'] == 'Norway']
#gdf.loc[gdf['country'] == 'France']
#gdf.loc[gdf['country'] == 'Somaliland']
#gdf.loc[gdf['country'] == 'North Cyprus']

# replace ISO code with the correct alpha-2 iso code
gdf.loc[21, 'ISOA2_code'] = 'NO'
gdf.loc[43, 'ISOA2_code'] = 'FR'
gdf.loc[167, 'ISOA2_code'] = 'YY'  # Somaliland does not have a iso2 code 

# drop Northern Cyprus
gdf = gdf.drop(gdf[gdf.country == 'Northern Cyprus'].index)
# drop Antactica 
gdf = gdf.drop(gdf[gdf.country == 'Antarctica'].index)

# check if really dropped
#gdf.loc[gdf['country'] == 'Northern Cyprus']
#gdf.loc[gdf['country'] == 'Antarctica']

# sort in alphabetical order
gdf = gdf.sort_values(by='country', ascending = True).reset_index()

'''
Processing of order data 
'''

data = pd.read_excel('tblOrdersByCountriesAndCities.xlsx', engine = 'openpyxl')
data.columns   # 'ISO', 'Country', 'City', 'Order_Summary'

# add Serbia and Kosovo iso code 
data.loc[data['Country'] == 'Serbia']
data.loc[2, 'ISO'] = 'RS'
data.loc[data['Country'] == 'Kosovo']
data.loc[1, 'ISO'] = 'XK'
data.loc[0, 'ISO'] = 'XK'

data.isnull().sum()
data['City'].fillna('Няма данни', inplace = True)

# fix UK to GB 
data.loc[data['ISO'] == 'UK']
UKindex = [157,158,159,160,161,162,163,164]

for i in UKindex: 
    print(i)
    data.loc[i,'ISO'] = 'GB'
data.loc[data['ISO'] == 'UK']

# rename ISO col name to match that in geo data
data.rename(columns = {"ISO": "ISOA2_code"}, inplace = True)


data = data.sort_values(by = 'Country', ascending = True).reset_index()

# save the data 

#data.to_csv('ProcessedtblOrdersByCountriesCities.csv')
#gdf.to_csv('ProcessedCoords.csv')

query = 'SELECT * FROM OrderData '  


##### connection with alchemy 
import sqlalchemy as sal

### pandas to_sql does not support MS SQL Server connection directly, you need to use sqlalchemy to connect 

engine = sal.create_engine('mssql+pyodbc://IVETS\SQLEXPRESS/V05_?trusted_connection=yes&driver=SQL+Server+Native+Client+11.0')
connection = engine.connect()

# via alchemy 
data.to_sql('OrderData', con = engine, schema = 'dbo', if_exists = 'replace')   ## interface error 

engine.execute(query).fetchone()     


# Function to generate WKB hex
def wkb_hexer(line):
    return line.wkb_hex
# Convert `'geom'` column in GeoDataFrame `gdf` to hex
    # Note that following this step, the GeoDataFrame is just a regular DataFrame
    # because it does not have a geometry column anymore. Also note that
    # it is assumed the `'geom'` column is correctly datatyped.
gdf['geometry'] = gdf['geometry'].apply(wkb_hexer)

gdf.to_sql('geocoords', con = engine, schema = 'dbo', if_exists = 'replace')

# Convert the `'geom'` column back to Geometry datatype, from text
#sql = """ALTER TABLE dbo.geocoords_
#               ALTER COLUMN geometry TYPE Geometry(LINESTRING,0)
#               USING ST_SetSRID(geometry::Geometry,0) """
                 
########### LEAVE this as a WKB type because later will read it with geopandas , which requires a WKB type anyway (!) 


sql = "UPDATE View_1 SET geometry = 'No data' WHERE geometry IS NULL"

engine.execute(sql)

