# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 21:28:41 2021

@author: Iveta
"""
'''
with SQL 
'''

import pandas as pd
import os 
import sys 
import json
from bokeh.io import output_notebook, show, output_file, curdoc, output_notebook
from bokeh.plotting import figure
from bokeh.models import IndexFilter, CDSView, GroupFilter, TapTool, PanTool, CustomJS, Div, ColumnDataSource, GeoJSONDataSource, LinearColorMapper, ColorBar, ResetTool, HoverTool, WheelZoomTool, SaveTool, BoxZoomTool
from bokeh.palettes import brewer, Category20c
from bokeh.layouts import column, gridplot, row
from bokeh.models.widgets import DataTable, TableColumn
import geopandas as gpd
import pyodbc

#Display plot in .html file that will be saved in the directory where the script is 
output_file('IBSmap.html')


keys = ['server_name', 'database_name', 'driver']
values = ['IVETS\SQLEXPRESS', 'V05_', '{SQL Server Native Client 11.0}']
serverargs = dict(zip(keys,values))


def sql_data(table, server_name, database_name, driver, geodata = False): 
    cnxn_str = ("Driver={};"
                "Server={};"
                "Database={};"     # database name 
                "Trusted_Connection=yes;").format(driver,server_name, database_name)  
    conn = pyodbc.connect(cnxn_str)
    query = 'SELECT * FROM ' + table
    if geodata:
        data = gpd.read_postgis(query, conn, geom_col='geometry')
    else: 
        data = pd.read_sql(query, conn)
    conn.close()
    return data 

# raw orders table with the cities and all other info we want 
all_orders = sql_data('OrderData', **serverargs)
all_orders.drop('level_0', axis = 1, inplace = True)

# in SQL we grouped the coords data with the orders data, with ISO_alph2 code being the foreign key 
# and summed 
grouped_country_sum = sql_data('View_1', **serverargs, geodata = True)

def add_percent(row):
    # create new column that holds what percent of the total is the sale 
    if isinstance(row['SumOrder'], float):
        return ((row['SumOrder']/total_order)*100).round(3)


min_order = grouped_country_sum['SumOrder'].min()
max_order = grouped_country_sum['SumOrder'].max()
average_order = grouped_country_sum['SumOrder'].mean()
total_order = grouped_country_sum['SumOrder'].sum()


grouped_country_sum['PercentTotal'] = grouped_country_sum.apply(lambda row: add_percent(row), axis=1)

#groupedsource = ColumnDataSource(grouped_country_sum)


def json_data(merged): 
    # in geopandas, fillna is to fill the na rows with a GEOMETRY 
    merged['SumOrder'].fillna('No data', inplace = True)
    merged['PercentTotal'].fillna('No data', inplace = True)
    merged_json = json.loads(merged.to_json())
    json_data = json.dumps(merged_json)
    return json_data

json_example = json_data(grouped_country_sum)

### bokeh part 
#Input GeoJSON source that contains features for plotting.
geosource = GeoJSONDataSource(geojson = json_data(grouped_country_sum))        ## use interactivity fcn we defined above
# define a sequential multi-hue colour palette
palette = brewer['YlOrRd'][8]
#Reverse color order so that dark blue is highest value.
palette = palette[::-1]
#Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
color_mapper = LinearColorMapper(palette = palette, low = min_order, high = max_order, nan_color = '#d9d9d9')   # change these later


#Add hover tool                                        
# tooltips - what will be displayed when hover 
hover = HoverTool(tooltips = [('Държава','@country'),
                              ('Сума продажби', '@SumOrder'),
                              ('Процент от общи', '@PercentTotal{0.00 a}')])



#Create color bar. 
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8,width = 500, height = 20,
                     border_line_color=None,location = (0,0), orientation = 'horizontal') 
                     #major_label_overrides = tick_labels)

#Create figure object.
p = figure(title = 'Общи продажби по държави', plot_height = 600, 
           plot_width = 1000, sizing_mode='scale_width', 
           toolbar_location = 'above', 
           tools = [hover, PanTool(), BoxZoomTool(match_aspect = True), SaveTool(), ResetTool()])

#Specify figure layout.
p.add_layout(color_bar, 'below')

#p.toolbar.active_drag = 
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
            
#Add patch renderer to figure.                                  
cr = p.patches('xs','ys', source = geosource,fill_color = {'field' :'SumOrder', 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)


divimg = Div(text = """<a href="https://v05.bg"><img src = 'static/Victoria_logo.png'></a>""", 
          default_size = 50)


layout = column(row(p, divimg))
#layout = row(p, column(divimg,table))
# curdoc - returns documents for current default state 

curdoc().add_root(layout)


#Display plot
show(layout)







