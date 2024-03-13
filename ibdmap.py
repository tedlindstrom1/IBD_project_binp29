#!usr/bin/python3
'''
ibdmap.py
Version: v1.0
Description: Interactive program to visualize intra-individual IBD relationships over time and geography. The program
             will take an IBD-file of the same format as the output from the program ancIBD, as well as an annotation
             file from the AADR database  or with the same column and information order as the AADR database annotation
             file. The program will find all inferred IBD segments between the user selected individual and any other
             individual in the data set. The user canspecify a milennia wherein only matches to the selected individual
             in that millenia will be displayed. The user can alsoset an upper and lower bound filter on the total
             shared IBD length for the individuals to be displayed. All information is also output in a sortable table.
             View the README for more information.
List of functions: ibd_dist() - Extracts information and creates a dataframe used to plot the matched individuals
                   update_map() - Dash callback function to update the map based on the user selected parameters
List of modules: pandas, pathlib, numpy, dash, plotly.express, plotly.graph_objects, sys
Usage: ibdmap.py <ibd_file> <annotation_file>
       the program will run on http://127.0.0.1:8050/, view through your browser of choice
Date: 13/03-2024
Author: Ted Lindström
'''

import pandas as pd
from pathlib import Path
import numpy as np
from dash import Dash, dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
import sys

# Function to generate data frame for plotting individuals on the map based on the user defined individual and filters
def ibd_dist(id_name, year_bin, filter_lower, filter_upper):
    # Subset data frame to only contain rows with this individual in either column
    df_sub = df_ibd.loc[(df_ibd["iid1"] == id_name) | (df_ibd["iid2"] == id_name)]

    # Extract unique IDs from the id columns and delete the current individuals ID from the array
    c1_ids = df_sub.iid1.unique()
    c1_ids = np.delete(c1_ids, np.argwhere(c1_ids == id_name))
    c2_ids = df_sub.iid2.unique()
    c2_ids = np.delete(c2_ids, np.argwhere(c2_ids == id_name))

    # Fill out dictionary with the sum of the Morgan distances for each other person ID
    # Check for unique IDs in both ID columns
    dict_ibd = {}
    # Check the first ID column and populate dict with each unique ID
    for id1 in c1_ids:
        tmp_df = df_sub.loc[(df_sub["iid1"] == str(id1)) & (df_sub["iid2"] == id_name)]
        cm = tmp_df["lengthM"].sum(axis=0)
        dict_ibd[id1] = cm

    # Check the second ID column. If there are IDs that were also present in the first column, add the summed segments
    # otherwise create new entry with the new ID.
    for id2 in c2_ids:
        if id2 in dict_ibd.keys():
            tmp_df = df_sub.loc[(df_sub["iid1"] == id_name) & (df_sub["iid2"] == str(id2))]
            cm = tmp_df["lengthM"].sum(axis=0)
            dict_ibd[id2] += cm
        else:
            tmp_df = df_sub.loc[(df_sub["iid1"] == id_name) & (df_sub["iid2"] == str(id2))]
            cm = tmp_df["lengthM"].sum(axis=0)
            dict_ibd[id2] = cm

    # Convert dictionary with distances to a dataframe
    df_dist = pd.DataFrame.from_dict(dict_ibd, orient='index',columns=["sum_lengthM"])
    df_dist = df_dist.rename_axis("id").reset_index()

    # Merge distance dataframe with the metadata, based on the common id column
    gdf = df_dist.merge(df_anno)

    # Find min and max age bins for constraining the age slider on the map
    min_bin = gdf['age_bin_numeric'].min()
    max_bin = gdf['age_bin_numeric'].max()

    # Specify mark names for the slider, convert age into CE/BCE. This is purely aesthetic for the age slider
    bin_marks = {}
    for year in gdf['age_bin_numeric'].unique():
        if year <= 0:
            age = str(abs(year)) + " CE"
            bin_marks[year] = age
        if year > 0:
            age = str(year) + " BCE"
            bin_marks[year] = age

    # Filter data frame to retain only on the values of the user selected year bin and within the user selected
    # filter range
    gdf = gdf.loc[(gdf["age_bin_numeric"] == year_bin) & (gdf["sum_lengthM"] >= filter_lower) & (gdf["sum_lengthM"] <= filter_upper)]

    # Return the data frame, min and max values for the slider, as well as the bins present in the current dataframe
    return gdf, min_bin, max_bin, bin_marks

# Read in files from command line launch and print usage info if no files are specified or one missing
while True:
    try:
        ibd_file = Path(sys.argv[1])
        annotation_file = Path(sys.argv[2])
        break
    except IndexError:
        print("Launch with IBD and annotation files: \nibdmap.py <ibd_file> <annotation_file>\nsee README.md for info on usage and format requirements")
        exit()

# Read IBD file into pandas dataframe
df_ibd = pd.read_csv(ibd_file, delimiter="\t")

# Read annotation for the samples from the AADR database
df2 = pd.read_csv(annotation_file, delimiter="\t")

# Extract only relevant columns from the annotation file: ID, date, population/nationality, lat/long
df_anno = df2.iloc[:,[0,7,13,14,15]] # column numbers are easier than column names because the AADR column names are a mess
df_anno.columns.values[0] = "id"
df_anno.columns.values[1] = "date"
df_anno.columns.values[2] = "population"
df_anno.columns.values[3] = "latitude"
df_anno.columns.values[4] = "longitude"
# Convert years to years before year 0 and make new "age" column in CE/BCE for user interface
df_anno.loc[:, 'date'] = df_anno['date'].apply(lambda x: x - 1950)
df_anno['age'] = df_anno['date'].apply(lambda x: str(abs(x)) + " CE" if x <= 0 else str(x) + " BCE")

# Bin age in 1000 year bins
max_age = df_anno.loc[:, 'date'].max()
if max_age % 1000 == 0:
    pass
else:
    max_age = max_age + 1000 - (max_age % 1000)

min_age = df_anno.loc[:, 'date'].min()
if min_age % 1000 == 0:
    pass
else:
    min_age = min_age - (min_age % 1000)

bins = [x for x in range(min_age, max_age, 1000)]

# Add bin info to the annotation dataframe
df_anno['age_bin_numeric'] = pd.cut(df_anno['date'], bins, labels=bins[:-1])

# Only keep annotation info for individuals that are in the provided IDB data
# Find unique IDs from the ID columns
idb_ids = np.append(df_ibd.iid1.unique(), df_ibd.iid2.unique())
idb_ids = np.unique(idb_ids)
num_id_pre_filter = len(idb_ids)
# Filter out annotation dataframe based on the IDs found in the IDB file
df_anno = df_anno[df_anno['id'].isin(idb_ids)]

# Do reciprocal filtering to only keep IDB entries that are annotated in the annotation file
idb_ids = df_anno.id.unique()
num_id_post_filter = len(idb_ids)

# Warn user if there are IBD IDs that are not present in the annotation file
if num_id_pre_filter != num_id_post_filter:
    print(f'WARNING: {num_id_pre_filter - num_id_post_filter} IDB IDs not in annotation file. Discarding IDs.')

# Filter dataframe based on individuals found in the annotation file
df_ibd = df_ibd.loc[(df_ibd.iid1.isin(idb_ids)) & (df_ibd.iid2.isin(idb_ids))]

# Run Dash
app = Dash(__name__)

# Format the Dash app window
app.layout = html.Div(children=[
    # Interactive map
    html.Div([
        html.H3('IBD matches',style={'textAlign':'center'}),
        dcc.Graph(id='map')
    ]),
    # Dropdown menu to select display individual
    html.Div([
        html.H4("Individual"),
        dcc.Dropdown(idb_ids,
        value=idb_ids[0],
        id="menu"),
    ],style={"width": "15%"}),
    # Age slider
    dcc.Slider(
        min=df_anno['age_bin_numeric'].min(),
        max=df_anno['age_bin_numeric'].max(),
        step=None,
        value=df_anno['age_bin_numeric'].min(),
        marks=None,
        id='year-slider'
    ),
    # IBD cutoff filters
    html.Div([
        html.H5('IBD filter (M) (Lower|Upper): ',
                style={'display': 'inline-block'}),
        dcc.Input(id='lower_filter',
                    value=0,
                    type='text',
                    minLength=1,
                    debounce=True,
                    style={'display': 'inline-block'}),
        dcc.Input(id='upper_filter',
                    value=100,
                    type='text',
                    minLength=1,
                    debounce=True,
                    style={'display': 'inline-block'})
    ]),
    # Table of individuals with inferred IBD to selected individual
    html.Div([
        html.H4('Found IBD matches'),
        html.Div(id="table")
    ])
])

# Callback function to update the map based on user specified individual selection
@callback(
    Output("map","figure"),
    Output("table", "children"),
    Output("year-slider", "min"), Output("year-slider", "max"),
    Output("year-slider", "marks"),
    Input("menu","value"),
    Input('year-slider','value'),
    Input("lower_filter","value"),
    Input("upper_filter","value"))
def update_map(menu_value,year_value,cM_filter_lower,cM_filter_upper):
    # Get the age and id filtered dataframe, as well as min and max age bins for matches for this individual and slider marks
    ddf, slider_min, slider_max, slider_marks = ibd_dist(menu_value, year_value, float(cM_filter_lower), float(cM_filter_upper))

    # Prepare interactive map
    fig = px.scatter_geo(ddf,
                         lon='longitude',
                         lat='latitude',
                         hover_data=['id', 'population', 'sum_lengthM','age'],
                         projection="natural earth",
                         color="sum_lengthM",
                         range_color=[ddf['sum_lengthM'].min(), ddf['sum_lengthM'].max()]
                         )

    # Also plot info on selected individual as a green dot with some selected hover info
    ind_row = df_anno.loc[df_anno['id'] == menu_value].to_dict('records')
    fig.add_trace(go.Scattergeo(name='Selected',
                                lon=[ind_row[0]['longitude']],
                                lat=[ind_row[0]['latitude']],
                                marker={'color':'green'},
                                hoverinfo='text',
                                hovertext=f"Selected ID: {ind_row[0]['id']}, Population: {ind_row[0]['population']}, Age: {ind_row[0]['age']}",
                                showlegend=False
                                ))

    # Print table of matches and make it sortable
    # Drop irrelevant columns
    ddf = ddf.drop(['date', 'age_bin_numeric'], axis=1)
    # Convert the column names for nicer output format
    coldat = ['id', 'sum_lengthM', 'population', 'latitude', 'longitude', 'age']
    colnames= ['ID', 'Shared IBD (M)', 'Population', 'Latitude', 'Longitude', 'Age']
    # Create table
    tbl = dash_table.DataTable(ddf.to_dict('records'),
                               columns=[{
                                   'name': col,
                                   'id': coldat[idx]
                               } for (idx, col) in enumerate(colnames)],
                               sort_action='native',
                               style_cell={'textAlign': 'left'},
                               style_as_list_view=True,
                               style_data_conditional=[
                                   {
                                       'if': {'row_index': 'odd'},
                                       'backgroundColor': 'rgb(220, 220, 220)',
                                   }
                               ],
                               )

    return fig, tbl, slider_min, slider_max, slider_marks
if __name__ == '__main__':
    app.run(debug=True)