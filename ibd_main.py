import pandas as ps
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

# Read files as a pandas dataframe
file = Path("IBD/ibd220.ibd.v54.1.pub.tsv")
df = ps.read_csv(file, delimiter="\t")
# colname = "lengthM"
# ps.DataFrame.hist(df, column=colname, bins=500)
# plt.show()
# print(df[colname].quantile(q=0.5))
# print(df[colname].quantile(q=0.25))
# print(df[colname].quantile(q=0.75))
# print(df[colname].quantile(q=0.90))

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

for key in dict_ibd:
    print(key,dict_ibd[key])
