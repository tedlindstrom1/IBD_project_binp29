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
df = pd.read_csv(file, delimiter="\t")

# Read annotation for the samples from the AADR database
file2 = Path("v54.1_1240K_public.anno")
df2 = pd.read_csv(file2, delimiter="\t")

# Extract only relevant columns: ID, date, population/nationality, lat/long
df_anno = df2.iloc[:,[0,7,13,14,15]]
df_anno.columns.values[0] = "id"
df_anno.columns.values[1] = "date" # this is years before 1950. !NB! Adjust theese values
df_anno.columns.values[2] = "population"
df_anno.columns.values[3] = "latitude"
df_anno.columns.values[4] = "longitude"

# Set ID name for individual you want to look at. !NB Change this to user input later!
id_name = "2H17.SG"

# Subset data frame to only contain rows with this individual in either column
df_test1 = df.loc[(df["iid1"]==id_name) | (df["iid2"] == id_name)]

# Extract unique IDs from the id columns and delete the current individuals ID from the array
c1_ids = df_test1.iid1.unique()
c1_ids = np.delete(c1_ids, np.argwhere(c1_ids == id_name))

c2_ids = df_test1.iid2.unique()
c2_ids = np.delete(c2_ids, np.argwhere(c2_ids == id_name))

# Fill out dictionary with the sum of the Morgan distances for each other person ID
dict_ibd = {}
for id1 in c1_ids:
    tmp_df = df_test1.loc[(df_test1["iid1"]==str(id1)) & (df_test1["iid2"]==id_name)]
    cm = tmp_df["lengthM"].sum(axis=0)
    dict_ibd[id1] = cm

for id2 in c2_ids:
    if id2 in dict_ibd.keys():
        tmp_df = df_test1.loc[(df_test1["iid1"] == id_name) & (df_test1["iid2"] == str(id2))]
        cm = tmp_df["lengthM"].sum(axis=0)
        dict_ibd[id2] += cm

    else:
        tmp_df = df_test1.loc[(df_test1["iid1"] == id_name) & (df_test1["iid2"] == str(id2))]
        cm = tmp_df["lengthM"].sum(axis=0)
        dict_ibd[id2] = cm

# Convert dictionary with distances to a dataframe
df_dist = pd.DataFrame.from_dict(dict_ibd, orient='index',columns=["sum_lengthM"])
df_dist = df_dist.rename_axis("id").reset_index()
# Add back id of interest to the dataframe with "100" relatedness to themselves
df_dist.loc[len(df_dist.index)] = [id_name, 1]

# Merge distance dataframe with the metadata, based on the common id column
df_joined = df_dist.merge(df_anno)

# Convert dataframe into a geopandas geodataframe by converting the lat/long to
# a geometry data type
gdf = gpd.GeoDataFrame(
    df_joined,geometry=gpd.points_from_xy(df_joined.longitude, df_joined.latitude),crs="EPSG:4326"
)

# Plot interactive map using plotly scatter_geo on a world map, color by value of sum_lengthM
fig = px.scatter_geo(gdf,
        lon = 'longitude',
        lat = 'latitude',
        hover_data = ['id','population','sum_lengthM'],
        projection="natural earth",
        color = "sum_lengthM",
        range_color = [0,0.4] # this should be changed to be based on the highest value in the dataframe
        )
fig.show()