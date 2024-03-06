import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
from dash import Dash, dcc, html, Input, Output, callback
import geopandas as gpd
from geodatasets import get_path
import plotly.express as px
import plotly.graph_objects as go

# Read IBD file into pandas dataframe
file = Path("IBD/ibd220.ibd.v54.1.pub.tsv")
df_ibd = pd.read_csv(file, delimiter="\t")

# Read annotation for the samples from the AADR database
file2 = Path("v54.1_1240K_public.anno")
df2 = pd.read_csv(file2, delimiter="\t")

# Extract only relevant columns: ID, date, population/nationality, lat/long
df_anno = df2.iloc[:,[0,7,13,14,15]]
df_anno.columns.values[0] = "id"
df_anno.columns.values[1] = "date"
df_anno.columns.values[2] = "population"
df_anno.columns.values[3] = "latitude"
df_anno.columns.values[4] = "longitude"
# Convert years to years before year 0
df_anno.loc[:,'date'] = df_anno['date'].apply(lambda x: x - 1950)
# Bin age in 1000 year bins
max_age = df_anno.loc[:,'date'].max()
if max_age % 1000 == 0:
    pass
else:
    max_age = max_age + 1000 - (max_age % 1000)

min_age = df_anno.loc[:,'date'].min()
if min_age % 1000 == 0:
    pass
else:
    min_age = min_age - (min_age % 1000)
bins = [x for x in range(min_age,max_age,1000)]

# Add bin info to the annotation dataframe
df_anno['age_bin'] = pd.cut(df_anno['date'], bins, labels=bins[:-1])


# Only keep annotation info for individuals that are in the provided IDB data
# Find unique IDs from the ID columns
idb_ids = np.append(df_ibd.iid1.unique(), df_ibd.iid2.unique())
idb_ids = np.unique(idb_ids) # 4104 unique individuals

# Filter out annotation dataframe based on the IDs found in the IDB file
df_anno = df_anno[df_anno['id'].isin(idb_ids)] # 4093 individuals, some are missing in the AADF database?

# Do reciprocal filtering to only keep IDB entries that are annotated in the AADF database
idb_ids = df_anno.id.unique()
def ibd_dist(id_name,year_bin):
    # Convert the year data by rounding down to closest 1000
    # Subset data frame to only contain rows with this individual in either column
    df_sub = df_ibd.loc[(df_ibd["iid1"] == id_name) | (df_ibd["iid2"] == id_name)]

    # Extract unique IDs from the id columns and delete the current individuals ID from the array
    c1_ids = df_sub.iid1.unique()
    c1_ids = np.delete(c1_ids, np.argwhere(c1_ids == id_name))

    c2_ids = df_sub.iid2.unique()
    c2_ids = np.delete(c2_ids, np.argwhere(c2_ids == id_name))

    # Fill out dictionary with the sum of the Morgan distances for each other person ID
    dict_ibd = {}
    for id1 in c1_ids:
        tmp_df = df_sub.loc[(df_sub["iid1"] == str(id1)) & (df_sub["iid2"] == id_name)]
        cm = tmp_df["lengthM"].sum(axis=0)
        dict_ibd[id1] = cm

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

    # Add back id of interest to the dataframe with "100" relatedness to themselves
    # df_dist.loc[len(df_dist.index)] = [id_name, 1]

    # Merge distance dataframe with the metadata, based on the common id column
    gdf = df_dist.merge(df_anno)
    # Filter only on the values of the user selected year bin
    gdf = gdf.loc[gdf["age_bin"] == year_bin]

    return(gdf)

# Run Dash
app = Dash(__name__)

# Format the Dash app window, with the map and a dropdown menu with all individuals in it
app.layout = html.Div([
    dcc.Graph(id='map'),

    dcc.Dropdown(idb_ids,
    "ROUQEE.SG",
    id="menu"),

    dcc.Slider(
        df_anno['age_bin'].min(),
        df_anno['age_bin'].max(),
        step=None,
        value=df_anno['age_bin'].min(),
        marks={str(year): str(year) for year in df_anno['age_bin'].unique()},
        id='year-slider'
    )
])

# Callback function to update the map based on user specified individual selection
@callback(
    Output("map","figure"),
    Input("menu","value"),
    Input('year-slider','value'))
def update_map(menu_value,year_value):
    ddf = ibd_dist(menu_value,year_value) # use ibd_dist function with the picked dropdown menu value
    fig = px.scatter_geo(ddf,
                         lon='longitude',
                         lat='latitude',
                         hover_data=['id', 'population', 'sum_lengthM','date'],
                         projection="natural earth",
                         color="sum_lengthM",
                         range_color=[ddf['sum_lengthM'].min(), ddf['sum_lengthM'].max()]
                         )
    return(fig)
if __name__ == '__main__':
    app.run(debug=True)