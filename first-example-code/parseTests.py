import osmium
import argparse
from OSMHandler import *

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)



parser = argparse.ArgumentParser(description="Extract information for tag=restaurant from osm files for current map and history file")
parser.add_argument("-i", "--history", help = "history input file (.osh.pbf)", required=True)
parser.add_argument("-m", "--map", help = "current map input file (.osm.pbf)", required=True)
parser.add_argument("-o", "--outfile", help = "output will be written in this file, default=[mapfile]_out.csv")

args = parser.parse_args()

mapfile = args.map

histfile = args.history

outputfile = ""
if args.outfile:
    outputfile = args.outfile
else:
    outputfile = mapfile+"_out.csv"





#create osmium handlers to parse input files

tlhandler = TimelineHandler()
tlhandler.apply_file(histfile)

rhandler = RestauHandler()
rhandler.apply_file(mapfile)



#get elements from both handlers and create the history file
#assumption: elements that do not occur in the restauHandler do not exists anymore, so their end date is the last timestamp in the history file ( which might be a wrong assumption!)
#elements that still exist get the current year as end year

elements_hist = tlhandler.getElements()
elements_cur = rhandler.getElements()


CURYEAR = 2022 #this is the current year to know which endyear to put in the output file

nversion = []
startyear = []
endyear = []
altnames = []
users = []
tags = []

hist2tab = dict() #history file: nodeID to summarized line
single2tab = dict() #nodes in history file that don't exist in current nodeIDs


#current restaurant list
ids = list(elements_cur['id'].values)
#should be unique ids in the current data set
lats = list(elements_cur['lat'].values)
lons = list(elements_cur['lon'].values)
restonames = list(elements_cur['name'].values)

#start with history
nIDs = elements_hist['id'].values
nIDs_uniq = list(set(nIDs))

for nodeid in nIDs_uniq:
    subtab = elements_hist.loc[elements_hist['id'] == nodeid] #current row
    #check name changes
    names = subtab['name'].values
    names_uniq = list(set(names))
    curname = names[-1]
    #check versions
    versions = subtab['version'].values
    maxversion = versions[-1]
    #check timestamps
    ts = subtab['ts'].values
    years = []
    for t in ts:
        tstr = str(t)
        lt = tstr.split('-')
        years.append(lt[0])
    minyear = years[0]
    maxyear = years[-1]
    #check user ids
    uids = subtab['uid'].values
    uids_uniq = list(set(uids))
    num_users = len(uids_uniq)
    #check ntags
    ntags = subtab['ntags'].values
    maxtags = ntags[-1]
    #extract lat and lon
    tlats = subtab['lat'].values
    curlat = tlats[0]
    tlons = subtab['lon'].values
    curlon = tlons[0]
    #maxversion minyear maxyear(2021 if exists in tab2) namelist(some names have changed but node ID is the same) numUsers maxNtags
    curlist = [curname, str(curlat), str(curlon), str(maxversion), str(minyear), str(maxyear), str(names_uniq), str(num_users), str(maxtags)]
    #curstr = f'{maxversion}\t{minyear}\t{maxyear}\t{names_uniq}\t{num_users}\t{maxtags}'
    if(nodeid in ids):
        hist2tab[nodeid] = curlist
    else:
        single2tab[nodeid] = curlist


    #create a dataframe with all restaurants and Lat, Lon informaton

for i in range(0,len(ids)):
    #here, ids,restonames, lat and lon already exist, we just have to add the additional data
    if(ids[i]) in hist2tab.keys(): #element appears in history and current data set
        cl = hist2tab[ids[i]]
        nversion.append(cl[3])
        startyear.append(cl[4])
        endyear.append(CURYEAR)
        altnames.append(cl[6])
        users.append(cl[7])
        tags.append(cl[8])
    else: #element appears only in the current data set
        nversion.append("1")
        startyear.append(CURYEAR)
        endyear.append(CURYEAR)
        altnames.append(str([restonames[i]]))
        users.append("1")
        tags.append("1")

#append restaurants that are not present anymore, only in the history data set
for sk in single2tab.keys():
    cl = single2tab[sk]
    ids.append(sk)
    restonames.append(cl[0])
    lats.append(cl[1])
    lons.append(cl[2])
    nversion.append(cl[3])
    startyear.append(cl[4])
    endyear.append(cl[5])
    altnames.append(cl[6])
    users.append(cl[7])
    tags.append(cl[8])

#create data frame
data = pd.DataFrame(list(zip(ids, restonames, lats, lons, nversion, startyear, endyear, altnames, users, tags)), columns =["NodeID","Name","Lat","Lon","Versions","Startyear","Endyear","NameAlternatives","Users","Tags"])
data.to_csv(outputfile, sep="\t")
