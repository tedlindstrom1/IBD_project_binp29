import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
from dash import Dash, dcc, html, Input, Output, callback, dash_table
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
df_anno['age'] = df_anno['date'].apply(lambda x: str(abs(x)) + " CE" if x <= 0 else str(x) + " BCE")

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
df_anno['age_bin_numeric'] = pd.cut(df_anno['date'], bins, labels=bins[:-1])

# Only keep annotation info for individuals that are in the provided IDB data
# Find unique IDs from the ID columns
idb_ids = np.append(df_ibd.iid1.unique(), df_ibd.iid2.unique())
idb_ids = np.unique(idb_ids) # 4104 unique individuals

# Filter out annotation dataframe based on the IDs found in the IDB file
df_anno = df_anno[df_anno['id'].isin(idb_ids)] # 4093 individuals, some are missing in the AADF database?

# Do reciprocal filtering to only keep IDB entries that are annotated in the AADF database
idb_ids = df_anno.id.unique()
def ibd_dist(id_name,year_bin,cM_filter):
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

    # Merge distance dataframe with the metadata, based on the common id column
    gdf = df_dist.merge(df_anno)

    # Find min and max age bins for constraining the age slider on the map
    min_bin = gdf['age_bin_numeric'].min()
    max_bin = gdf['age_bin_numeric'].max()

    # Specify mark names for the slider, convert age into CE/BCE
    bin_marks = {}
    for year in gdf['age_bin_numeric'].unique():
        if year <= 0:
            age = str(abs(year)) + " CE"
            bin_marks[year] = age
        if year > 0:
            age = str(year) + " BCE"
            bin_marks[year] = age

    # Filter data frame to retain only on the values of the user selected year bin
    gdf = gdf.loc[(gdf["age_bin_numeric"] == year_bin) & (gdf["sum_lengthM"] >= cM_filter)]

    return(gdf,min_bin,max_bin,bin_marks)
# Run Dash
app = Dash(__name__)

# Format the Dash app window, with the map and a dropdown menu with all individuals in it
app.layout = html.Div([
    dcc.Graph(id='map'),

    dcc.Dropdown(idb_ids,
    "ROUQEE.SG",
    id="menu"),

    dcc.Slider(
        min=df_anno['age_bin_numeric'].min(),
        max=df_anno['age_bin_numeric'].max(),
        step=None,
        value=df_anno['age_bin_numeric'].min(),
        marks=None,
        id='year-slider'
    ),
    html.Div([dcc.Input(id='filter',
                        value=0,
                        type='text',
                        minLength=1,
                        debounce=True)]),


    html.Div(id="table")
])

# Callback function to update the map based on user specified individual selection
@callback(
    Output("map","figure"),
    Output("table", "children"),
    Output("year-slider", "min"), Output("year-slider", "max"),
    Output("year-slider", "marks"),
    Input("menu","value"),
    Input('year-slider','value'),
    Input("filter","value"))
def update_map(menu_value,year_value,cM_filter):
    # Get the age and id filtered dataframe, as well as min and max age bins for matches for this individual and slider marks
    ddf, slider_min, slider_max, slider_marks = ibd_dist(menu_value, year_value, float(cM_filter))
    # Prepare figure

    fig = px.scatter_geo(ddf,
                         lon='longitude',
                         lat='latitude',
                         hover_data=['id', 'population', 'sum_lengthM','age'],
                         projection="natural earth",
                         color="sum_lengthM",
                         #range_color=[0,1]
                         range_color=[ddf['sum_lengthM'].min(), ddf['sum_lengthM'].max()] # to change to relative color scale instead of absolute
                         )
    # Also plot info on selected individual as a green dot with some selected hover info
    ind_row = df_anno.loc[df_anno['id'] == menu_value].to_dict('records')
    fig.add_trace(go.Scattergeo(name='Selected',
                                lon=[ind_row[0]['longitude']],
                                lat=[ind_row[0]['latitude']],
                                marker={'color':'green'},
                                hoverinfo='text',
                                hovertext=f"Selected ID: {ind_row[0]['id']}, Population: {ind_row[0]['population']}, Age: {ind_row[0]['age']}"
                                ))
    # Print table of matches, make it sortable
    ddf = ddf.drop(['date','age_bin_numeric'],axis=1)
    tbl = dash_table.DataTable(ddf.to_dict('records'),
                               [{"name": i, "id": i} for i in ddf.columns],
                               sort_action='native')

    return(fig,tbl,slider_min,slider_max,slider_marks)
if __name__ == '__main__':
    app.run(debug=True)