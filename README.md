# IBDmap  
*A tool for visualizing ancient IBD relationships*  
Author: Ted Lindström, ted.lindstrom@hotmail.com  
03-2024  
### Description
IBDmap allows for the geospatial visualization of inferred IBD relationships
between two individuals. The tool was developed with ancient populations
in mind but can also be used for modern individuals.

The tool takes two input files: One file containing inferred IBD between
any number of individuals, and one annotation file containing
meta-information on the individuals in the data set. This meta-information
consists of the coordinates and location where the individual was found
and their age.

The user selects one individual from the provided data set through the
user interface and the program will find and sum up all 
intra-individual IBD segments to any other individual present in the 
file.  

The program plots an interactive map on which individuals found to share 
IBD with the selected individual will be visualized as dots, colored 
by the sum of the lengths of the inferred shared IBD segments. The 
selected individual is visualized as a green dot. Hovering over any 
dot will show relevant information such as the sum of shared IBD in 
Morgans, as well as their age and coordinates. This information is also
presented in a sortable table below the map, containing all currently
visualized individuals.

The program will segment all found IBD relationships into millennia,
and the user can select any millennia where there are found relationships
to the selected individual using a time slider below the map. The user
can also specify a upper and lower filter on the total sum of IBD segments
to filter out weak or strong matches if desired.

### Installation and setup
The program consists of the single file "ibdmap.py". It was developed
using Python 3.11 and requires the following packages, all of which 
can be installed using Conda:
- Dash (2.16.1)
- Plotly (5.19.0)
- Pandas (2.2.1)
- Numpy (1.26.4)  
 
$ conda install -c conda-forge dash plotly pandas numpy

### Usage
The program is launched from the command line with the following format:  

$ ibdmap.py <ibd_file> <annotation_file>  

The format for the ibd-file has to correspond to the output format of
the tool ancIBD, described in Ringbauer et. al. (2023), available
here: https://www.nature.com/articles/s41588-023-01582-w  
Any tab-delimited file containing the following columns will work:
- ID of individual 1, column heading: iid1
- ID of individual 2, column heading: iid2
- Length of inferred IBD segment between individuals 1 and 2 in
morgans, column heading: lengthM  

The tool was developed using a dataset of inferred IBD segments between
over 4000 individuals, as described in Ringbauer et. al. (2023) and
is available for download here: https://zenodo.org/records/8417049

The format for the annotation file has to be like that of the AADR
database annotation file. The tool was developed using the AADR 
annotation file, which can be found for download here: 
https://reich.hms.harvard.edu/allen-ancient-dna-resource-aadr-downloadable-genotypes-present-day-and-ancient-dna-data  

If a user wants to provide their own annotation file it needs to fulfill 
the following format requirements: It has to be tab-delimited with the
following column order:
- Column 1: ID
- Column 7: Date of individual in years before 1950
- Column 13: Country/Political entity where the individual was found
- Column 14: Latitude coordinate for where the individual was found
- Column 15: Longitude coordinate for where the individual was found  

If there are IDs in the IBD file that is not present in the annotation 
file the program will discard these entries and warn the user. 