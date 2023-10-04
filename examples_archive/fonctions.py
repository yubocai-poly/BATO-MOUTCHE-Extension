import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
import folium
import pandas as pd
import urllib3
from zipfile import ZipFile
import requests
import osmnx as ox
import networkx as nx
import numpy as np
from tqdm.auto import tqdm 
from palettable.colorbrewer.qualitative import Pastel1_7


##########################################
##### LOOKING AT RESTAURANTS ONLY ########
##########################################



def get_place(place : str) : 
    
    #récupération des données piétons
    place += ", Paris, Ile-de-France, France" 
    g_place = ox.graph_from_place(place, buffer_dist=1000, network_type="walk", retain_all=True, truncate_by_edge=True)
    
    tags = {"amenity":["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"]}
    # Voir : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques 
    # ce qui nous interresse est probablement le plus : 
    # https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#Consommation
    
    gdf_pois = ox.geometries_from_place(place, tags, buffer_dist=1000)
    #certains lieux (comme une ville) ont un polygone associée : 
    # on peut donc récupérer les POI sans indiquer de dist
    
    gdf_pois["center"]=gdf_pois.centroid
    #chaque ligne peut être soit un polygone (par exemple pour le champ de Mars), soit un point comme un restaurant : on calcul le centre pour avoir une référence unique
    
    return gdf_pois
    #On récupère directement un geodataframe
    

def count_amenities(place) :
    
    tab = get_place(place)
    column_amenity = tab['amenity']
    
    amenities = np.array(["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"])
    amenities = np.append(amenities, "total")
    amenities = amenities.astype('object')
    amenities = np.array([amenities, np.zeros(len(amenities))])

    for i in column_amenity : 
        for j in range(len(amenities[0])) : 
            if i == amenities[0][j] :
                amenities[1][j] += 1

    amenities[1][-1] = np.sum(amenities[1][0 : len(amenities[0]) - 1])
    
    df_amenities = pd.DataFrame(np.transpose(amenities), columns = ['amenity', 'how many'])
    return df_amenities




############################################################
##### LOOKING AT RESTAURANTS, CULTURE AND EDUCATION ########
############################################################



def get_place2(place : str) : 
    
    #récupération des données piétons
    place += ", Paris, Ile-de-France, France" 
    g_place = ox.graph_from_place(place, buffer_dist=1000, network_type="walk", retain_all=True, truncate_by_edge=True)
    
    tags = {"amenity":["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten", 
                       "college", "driving_school", "kindergarten", "language_school", "library", "toy_library", 
                       "training", "music_school", "school", "university",
                      "arts_centre", "cinema", "conference_centre", "events_venue", "planetarium", "public_bookcase", "studio", "theatre"]}
    # Voir : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques 
    # ce qui nous interresse est probablement le plus : 
    # https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#Consommation
    
    gdf_pois = ox.geometries_from_place(place, tags, buffer_dist=1000)
    #certains lieux (comme une ville) ont un polygone associée : 
    # on peut donc récupérer les POI sans indiquer de dist
    
    gdf_pois["center"]=gdf_pois.centroid
    #chaque ligne peut être soit un polygone (par exemple pour le champ de Mars), soit un point comme un restaurant : on calcul le centre pour avoir une référence unique
    
    return gdf_pois
    #On récupère directement un geodataframe

def count_amenities2(place) :
    
    list_restaurants = ["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"]
    list_culture = ["library", "toy_library", "music_school","arts_centre", "cinema", "conference_centre", "events_venue", "planetarium", "public_bookcase", "studio", "theatre"]
    list_education = ["college", "driving_school", "kindergarten", "language_school", "training", "school", "university"]
    
    tab = get_place2(place)
    column_amenity = tab['amenity']
    
    amenities = np.array(["restaurant", "culture and art", "education", "total"])
    amenities = amenities.astype('object')
    amenities = np.array([amenities, np.zeros(len(amenities))])

    for i in column_amenity :
        if i in list_restaurants :
            amenities[1][0] += 1
        if i in list_culture :
            amenities[1][1] += 1
        if i in list_education :
            amenities[1][2] += 1

    amenities[1][-1] = np.sum(amenities[1][0 : len(amenities[0]) - 1])
    
    df_amenities = pd.DataFrame(np.transpose(amenities), columns = ['amenity', 'how many'])
    return df_amenities

############################################################
##### DONUT CHART FOR LOOKING AT RESTAURANTS ONLY ##########
############################################################

"""
def Donut chart 
"""

def composition_chart(place): 
    names = count_amenities(place)[(count_amenities(place)["amenity"] != "total") & (count_amenities(place)["how many"] != 0)]["amenity"]
    size = count_amenities(place)[(count_amenities(place)["amenity"] != "total") & (count_amenities(place)["how many"] != 0)]["how many"]
    #Remove values equal to 0

    # add a circle at the center to transform it in a donut chart
    my_circle=plt.Circle( (0,0), 0.7, color='white')


    # Give color names
    plt.pie(size, labels=names, autopct='%1.1f%%', pctdistance=0.85,
            colors=Pastel1_7.hex_colors, wedgeprops = { 'linewidth' : 7, 'edgecolor' : 'white' })
    p = plt.gcf()
    p.gca().add_artist(my_circle)

    plt.show()

#######################################################################
#### DONUT CHART FOR LOOKING AT RESTAURANTS, CULTURE AND EDUCATION ####
#######################################################################

def composition_chart2(place): 
    names = count_amenities2(place)[(count_amenities2(place)["amenity"] != "total") & (count_amenities2(place)["how many"] != 0)]["amenity"]
    size = count_amenities2(place)[(count_amenities2(place)["amenity"] != "total") & (count_amenities2(place)["how many"] != 0)]["how many"]
    #Remove values equal to 0

 
    # add a circle at the center to transform it in a donut chart
    my_circle=plt.Circle( (0,0), 0.7, color='white')


    # Give color names
    plt.pie(size, labels=names, autopct='%1.1f%%', pctdistance=0.85,
            colors=Pastel1_7.hex_colors, wedgeprops = { 'linewidth' : 7, 'edgecolor' : 'white' })
    p = plt.gcf()
    p.gca().add_artist(my_circle)

    plt.show()