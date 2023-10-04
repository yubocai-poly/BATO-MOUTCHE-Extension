import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
import folium
import pandas as pd
import urllib3
import requests
import osmnx as ox
import networkx as nx
import numpy as np
from tqdm.auto import tqdm 

from pysal.lib import weights
from pysal.lib import cg as geometry
from pysal.model import spreg
from spreg import OLS

import plotly.express as px
from palettable.colorbrewer.qualitative import Pastel1_7

##########################################
##### General variables ##################
##########################################

categories_tags = {'restaurant':["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"],
                   'culture and art':["library", "toy_library", "music_school","arts_centre", "cinema", "conference_centre", "events_venue", "planetarium", "public_bookcase","studio", "theatre", "art", "camera", "collector", "craft", "frame", "games", "model", "musique", "musical_instrument", "photo", "trophy", "video", "video_games", "anime", "books", "ticket", "antiques"],
                   'education':["college",  "kindergarten", "school", "university"],
                   'food_shops' : ["alcohol", "bakery", "butcher", "cheese", "beverages", "brewing_supplies", "chocolate", "coffee", "confectionery", "convenience", "deli", "dairy", "farm", "frozen_food", "greengrocer", "ice_cream", "pasta", "pastry", "seafood", "spices", "tea", "wine", "water", "supermarket"],    
                    'fashion_beauty' : ["bag", "boutique", "clothes", "fabric", "fashion_accessories", "jewelry", "leather", "sewing", "shoes", "tailor", "watches", "wool", "beauty", "cosmetics", "erotic", "hairdresser", "hairdresser_supply", "massage", "perfumery", "tattoo"],
                   'supply_shops' : ["department_store", "general", "kiosk", "mall", "wholesale", "charity", "second_hand", "variety_store", "chemist", "agrarian", "appliance", "bathroom_furnishing", "doityourself", "electrical", "energy", "fireplace", "florist", "garden_centre", "garden_furniture", "gas", "glaziery", "groundskeeping", "hardware", "houseware", "locksmith", "paint", "security", "trade", "antiques", "bed", "candles", "carpet", "curtain", "doors", "flooring", "furniture", "household_linen","interior_decoration", "kitchen", "lighting", "tiles", "window_blind", "computer", "electronics", "hifi", "mobile_phone", "radiotechnics", "telecommunication", "vaccum_cleaner","atv", "bicycle", "boat", "car", "car_repair", "car_parts", "caravan", "fuel", "fishing", "golf", "hunting", "jetski", "military_surplus", "motorcycle", "outdoor", "scuba_diving", "ski", "snowmobile", "sports", "swimming_pool", "trailer", "tyres", "gift", "lottery", "newsagent", "stationery", "bookmaker", "cannabis", "copyshop", "dry_cleaning", "e-cigarette", "funeral_directors", "insurance", "laundry",  "money_lender", "outpost", "party", "pawnbroker", "pest_control", "pet", "pet_grooming", "pyrotechnics", "religion", "storage_rental", "tobacco", "toys", "travel_agency", "weapons", "vacant", "health_food", "baby_goods", "hearing_aids", "herbalist", "medical_supply", "nutrition_supplements", "optician"]}


shops = ["alcohol", "bakery", "butcher", "cheese", "beverages", "brewing_supplies", "chocolate", 
 "coffee", "confectionery", "convenience", "deli", "dairy", "farm", "frozen_food", "greengrocer", 
"health_food", "ice_cream", "pasta", "pastry", "seafood", "spices", "tea", "wine", "water",
"department_store", "general", "kiosk", "mall", "supermarket", "wholesale", 
"baby_goods", "bag", "boutique", "clothes", "fabric", "fashion_accessories", "jewelry", "leather",
"sewing", "shoes", "tailor", "watches", "wool", "charity", "second_hand", "variety_store", 
"beauty", "chemist", "cosmetics", "erotic", "hairdresser", "hairdresser_supply", "hearing_aids", "herbalist", 
"massage", "medical_supply", "nutrition_supplements", "optician", "perfumery", "tattoo",
"agrarian", "appliance", "bathroom_furnishing", "doityourself", "electrical", "energy", "fireplace", "florist", 
"garden_centre", "garden_furniture", "gas", "glaziery", "groundskeeping", "hardware", "houseware", "locksmith", 
"paint", "security", "trade",
"antiques", "bed", "candles", "carpet", "curtain", "doors", "flooring", 'furniture', "household_linen", 
"interior_decoration", "kitchen", "lighting", "tiles", "window_blind", 
"computer", "electronics", "hifi", "mobile_phone", "radiotechnics", "telecommunication", "vaccum_cleaner", 
"atv", "bicycle", "boat", "car", "car_repair", "car_parts", "caravan", "fuel", "fishing", "golf", "hunting", 
"jetski", "military_surplus", "motorcycle", "outdoor", "scuba_diving", "ski", "snowmobile", "sports", 
"swimming_pool", "trailer", "tyres", 
"art", "camera", "collector", "craft", "frame", "games", "model", "musique", "musical_instrument", "photo", 
"trophy", "video", "video_games",
"anime", "books", "gift", "lottery", "newsagent", "stationery", "ticket", 
"bookmaker", "cannabis", "copyshop", "dry_cleaning", "e-cigarette", "funeral_directors", "insurance", "laundry", 
"money_lender", "outpost", "party", "pawnbroker", "pest_control", "pet", "pet_grooming", "pyrotechnics", "religion",
"storage_rental", "tobacco", "toys", "travel_agency", "weapons", "vacant"]

amenities = ["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten", 
"library", "toy_library", "music_school","arts_centre", "cinema", "conference_centre", "events_venue", 
"planetarium", "public_bookcase","studio", "theatre", 
"college", "driving_school", "kindergarten", "language_school", "training", "school", "university"]

"""
We are building several functions on top of OSMnx library which itself build
to interact with Overpass API (a copy of OMS data without the same API limitations)
"""

##########################################
##### OSMNX functions specific implementation ########
##########################################

def get_place_POI_tags(place : str,
    tags = {"amenity":["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"]},
    city : str = "Paris, Ile-de-France, France", consolidate = True,get_network = False,
    network_type = 'walk') : 
    """
    Function to get any city's (Paris' by default) neighborhood's OMS POI.
    place : str, must be name sufficiently known
    city : str, format : "Name, Region, Country" (Example : Paris, Ile-de-France, France)
    tags : dict, keys and values are the same as in OMS. 
    For instance : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#
    and : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#Consommation
    consolidate : use the osmnx consolidate_intersections (tolerance = 15) to merge place with too complicated intersections like a roundabout 
    Returns the street network in a 1km walking distance as a networkx object 
    and the POI in the same area as a geodataframe

    Streets network and POI are projected to WGS-84
    """
    #récupération des données piétons
    place += ", "+city # complete addresse

    #get the network
    if get_network:
        g_place = ox.graph_from_place(place, buffer_dist=1000, network_type=network_type, retain_all=True, truncate_by_edge=True)
        g_place = ox.project_graph(g_place, to_crs="WGS-84")
        if consolidate:
            g_proj = ox.project_graph(g_place)
            g_place = ox.consolidate_intersections(g_proj, rebuild_graph=True, tolerance=15, dead_ends=False)
    
    gdf_pois = ox.geometries_from_place(place, tags, buffer_dist=1000)
    #certains lieux (comme une ville) ont un polygone associée : 
    # on peut donc récupérer les POI sans indiquer de dist
    gdf_pois = ox.project_gdf(gdf= gdf_pois, to_crs="WGS-84")
    gdf_pois = gdf_pois.to_crs("WGS-84")
    gdf_pois = gdf_pois.set_crs("WGS-84")
    gdf_pois["center"]=gdf_pois.to_crs("WGS-84").centroid
    #chaque ligne peut être soit un polygone (par exemple pour le champ de Mars), soit un point comme un restaurant : on calcul le centre pour avoir une référence unique
    if get_network:
        return g_place, gdf_pois    #On récupère directement un networkx et un geodataframe
    else:
        return gdf_pois

def find_cat(df, 
             categories = ["restaurant", "culture and art",
              "education", 'food_shops', 'health',
               'fashion_beauty', 'supply_shops'],
             dummy = False,
             tags_for_cat = categories_tags) :
    if dummy:
        for cat in categories : 
            list_cat_dummy = np.zeros(len(df),dtype = int)
            for i in range(len(df)) :
                if df['amenity'][i] in tags_for_cat[cat]:
                    list_cat_dummy[i] = 1
                if df['shop'][i] in tags_for_cat[cat]:
                    list_cat_dummy[i] = 1
            df[cat] = list_cat_dummy
    else:
        df['category'] = 'Out of interest'
        for i in range(len(df)) :
            for x in categories : 
                if df['amenity'][i] in tags_for_cat[x] : 
                    df['category'][i] = x
                if df['shop'][i] in tags_for_cat[x] : 
                    df['category'][i] = x
    return df

def reduce_tags(tags):
    reduced_tags = {}
    accepted_tags = []
    for cat in categories_tags.keys():
        for t in categories_tags[cat]:
            accepted_tags.append(t)
    for oms_cat in tags.keys():
        tag_to_be_searched = []
        for t in tags[oms_cat]:
            if t in accepted_tags:
                tag_to_be_searched.append(t)
        reduced_tags[oms_cat] = tag_to_be_searched
    return reduced_tags
            

def get_place_POI(place: str, 
    tags : dict = {"shop": shops, "amenity" : amenities},
    categories = categories_tags.keys(),
    city : str = "Paris, Ile-de-France, France", 
    get_dummy_cat = True, tags_for_cat = categories_tags,
    number_var_reduced = True,
    get_network = False,
    consolidate = True,
    network_type = 'walk') :
    """
    Function to get any city's (Paris' by default) neighborhood's OMS POI.
    place : str, must be name sufficiently known
    city : str, format : "Name, Region, Country" (Example : Paris, Ile-de-France, France)
    tags : the dict of tags we select from the categories
    categories : homemade categories on amenities tags. list of str between the following :
    Available categories : 'restaurant', 'culture and art', 'education' 
    list_restaurants = ["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"]
    list_culture = ["library", "toy_library", "music_school","arts_centre", "cinema", "conference_centre", "events_venue", "planetarium", "public_bookcase", "studio", "theatre"]
    list_education = ["college", "driving_school", "kindergarten", "language_school", "training", "school", "university"]
    See : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#
    consolidate : use the osmnx consolidate_intersections (tolerance = 15) to merge place with too complicated intersections like a roundabout 
    Returns the street network in a 1km walking distance as a networkx object 
    and the POI in the same area as a geodataframe
    Streets network and POI are projected to WGS-84"""
    
    #récupération des données piétons
    place += ", "+city # complete addresse

    #get the network
    if  get_network:
        g_place = ox.graph_from_place(place, buffer_dist=1000, network_type=network_type, retain_all=True, truncate_by_edge=True)
        g_place = ox.project_graph(g_place, to_crs="WGS-84")
        if consolidate:
            g_proj = ox.project_graph(g_place)
            g_place = ox.consolidate_intersections(g_proj, rebuild_graph=True, tolerance=15, dead_ends=False)
        
    gdf_pois = ox.geometries_from_place(place, tags, buffer_dist=1000)
    #certains lieux (comme une ville) ont un polygone associé : 
    # on peut donc récupérer les POI sans indiquer de dist
    #gdf_pois = ox.project_gdf(gdf= gdf_pois, to_crs="WGS-84")
    gdf_pois["center"]=gdf_pois.centroid
    #chaque ligne peut être soit un polygone (par exemple pour le champ de Mars), soit un point comme un restaurant : on calcul le centre pour avoir une référence unique
    gdf_pois = find_cat(gdf_pois, categories, dummy = get_dummy_cat, tags_for_cat = tags_for_cat)
    if number_var_reduced:
        gdf_pois = reduce_oms_var(gdf_pois, categories=categories)
    if get_network:
        return g_place, gdf_pois
    else:
        return gdf_pois

def reduce_oms_var(gdf, categories = ["restaurant", "culture and art",
              "education", 'food_shops', 'health',
               'fashion_beauty', 'supply_shops']):
    list_var = ['name','center','geometry'] + list(categories)
    return gdf[list_var]


def get_place_POI_category(place: str, 
    categories : list,
    city : str = "Paris, Ile-de-France, France", consolidate = True,get_network = False,
    network_type = 'walk') :
    """
    Function to get any city's (Paris' by default) neighborhood's OMS POI.
    place : str, must be name sufficiently known
    city : str, format : "Name, Region, Country" (Example : Paris, Ile-de-France, France)
    categories : homemade categories on amenities tags. list of str between the following :
    Available categories : 'restaurant', 'culture and art', 'education' 
    list_restaurants = ["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"]
    list_culture = ["library", "toy_library", "music_school","arts_centre", "cinema", "conference_centre", "events_venue", "planetarium", "public_bookcase", "studio", "theatre"]
    list_education = ["college", "driving_school", "kindergarten", "language_school", "training", "school", "university"]
    See : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#
    consolidate : use the osmnx consolidate_intersections (tolerance = 15) to merge place with too complicated intersections like a roundabout 
    Returns the street network in a 1km walking distance as a networkx object 
    and the POI in the same area as a geodataframe

    Streets network and POI are projected to WGS-84"""
    
    tags = []
    for cat in categories:
        tags += categories_tags[cat]
    tags = {'amenity':tags}
    print(tags)
    return get_place_POI_tags(place = place, tags = tags, city=city, consolidate=consolidate,get_network=get_network,
     network_type=network_type)

def get_polygon_POI_tags(
    polygon,
    tags = {"amenity":["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"]},
    consolidate = True,
    network_type = 'walk') : 
    """
    Function to get OMS POI within a polygon.
    polygon : shapely.geometry.MultiPolygon or shapely.geometry.Polygon
    tags : dict, keys and values are the same as in OMS. 
    For instance : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#
    and : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#Consommation
    consolidate : use the osmnx consolidate_intersections (tolerance = 15) to merge place with too complicated intersections like a roundabout 
    Returns the POI in the polygon as a geodataframe
    POI are projected to WGS-84
    """
    """# récupération des données piétons
    #get the network
    g_poly = ox.graph_from_polygon(polygon, network_type=network_type, retain_all=True, truncate_by_edge=True)
    g_poly = ox.project_graph(g_poly, to_crs="WGS-84")
    if consolidate:
        g_proj = ox.project_graph(g_poly)
        g_poly = ox.consolidate_intersections(g_proj, rebuild_graph=True, tolerance=15, dead_ends=False)"""
    
    gdf_pois = ox.geometries.geometries_from_polygon(polygon, tags)
    #certains lieux (comme une ville) ont un polygone associée : 
    # on peut donc récupérer les POI sans indiquer de dist
    if len(gdf_pois) > 0:
        gdf_pois = ox.project_gdf(gdf= gdf_pois, to_crs="WGS-84")
        #gdf_pois["center"]=gdf_pois.centroid
    #chaque ligne peut être soit un polygone (par exemple pour le champ de Mars), soit un point comme un restaurant : on calcul le centre pour avoir une référence unique
    return gdf_pois #return g_poly, gdf_pois    #On récupère directement un networkx et un geodataframe

def get_polygon_POI_category(polygon, 
    categories : list,
    consolidate = True,
    network_type = 'walk') :
    """
    Function to get OMS POI within a polygon.
    polygon : shapely.geometry.MultiPolygon or shapely.geometry.Polygon
    categories : homemade categories on amenities tags. list of str between the following :
    Available categories : 'restaurant', 'culture and art', 'education' 
    list_restaurants = ["restaurant", "cafe","bar","ice_cream","fast_food","pub","food_court","biergarten"]
    list_culture = ["library", "toy_library", "music_school","arts_centre", "cinema", "conference_centre", "events_venue", "planetarium", "public_bookcase", "studio", "theatre"]
    list_education = ["college", "driving_school", "kindergarten", "language_school", "training", "school", "university"]
    See : https://wiki.openstreetmap.org/wiki/FR:%C3%89l%C3%A9ments_cartographiques#
    consolidate : use the osmnx consolidate_intersections (tolerance = 15) to merge place with too complicated intersections like a roundabout 
    Returns the POI in the polygon as a geodataframe
    POI are projected to WGS-84"""
    
    tags = []
    for cat in categories:
        tags += categories_tags[cat]
    tags = {'amenity':tags}
    return get_polygon_POI_tags(polygon = polygon, tags = tags, consolidate=consolidate, network_type=network_type)

##########################################
##### Map function ########
########################################## 

def plot_POI_folium(place_latlong : np.array,
    gdf_poi: gpd.GeoDataFrame, tiles = "OpenStreetMap", zoom_start = 14) :
    """
    place_latlong : the central place for which to center the map on, tuple (lat, long)
    gdf_poi : GeoPandas.GeoDataFrame with POI
    It is the classical folium method : you create a list with geometry point values (here gdf_poi.center) and for each 
    coordinates, you add a marker. 
    Returns a Folium map
    """
    #on représente en lat, long (et donc y,x)!!!
    # y = lat
    # x = long
    map = folium.Map(location=place_latlong, tiles=tiles, zoom_start=zoom_start)

    for poi in gdf_poi.iterrows():
        # Place the markers with the popup labels and data
        x , y = (poi[1]['center'].x, poi[1]['center'].y)
        map.add_child(
            folium.Marker(
                location=[y,x],
                popup=
                    "Name: " + str(poi[1]['name']) + "<br>" #here to add name 
                    #+ "Leisure: " + str(poi[1]['leisure']) + "<br>" #type 
                   # + "Amenity: " + str(poi[1]['amenity']) + "<br>" #type 
                    + "Coordinates: " + str(y)+', '+str(x)
                ,
            
                icon=folium.Icon(color="blue"),
            )
        )
    return map
##########################################
##### Route functions ########
##########################################

def route_between_coordinates(streets : nx.classes.MultiDiGraph,
    coord1: tuple, coord2 : tuple, weight = "lenght"):
    """
    Using the street network closest point to each coordinate, 
    calculate the shortest path on the networks
    coord : format (long, lat)
    return a list of osmid for the nodes of the route on the streets network
    /!\\ if there is no path return a NoneType /!\\ 
    """
    orig = ox.distance.nearest_nodes(streets,X=coord1[0],Y = coord1[1])
    dest = ox.distance.nearest_nodes(streets,X=coord2[0],Y = coord2[1])
    route = ox.shortest_path(streets, orig, dest, weight=weight) # on peut aussi mettre travel_time
    if route == None:
        print(f"/!\\ Warning /!\\ No route between {coord1} and {coord2}")

    return route

def distance_route(route, streets : nx.classes.MultiDiGraph, limit=1000):
    n = len(route)-1
    dist_metric = 0
    for i in range(n):
        adj = streets.adj[route[i]]
        dist_metric += adj[route[i+1]][0]['length']
        if dist_metric > limit:
            return dist_metric
    return dist_metric

def distance_between_coordinates(streets : nx.classes.MultiDiGraph,
    coord1: tuple, coord2 : tuple, weight = "lenght", limit = 1000):
    route = route_between_coordinates(streets,
    coord1, coord2, weight)
    if route == None:
        return np.inf
    else:
        return distance_route(route,streets)/limit

def route_between_POI(streets : nx.classes.MultiDiGraph, poi : gpd.GeoDataFrame,
    name1: str, name2 : str, weight = "lenght"):
    """
    Calculate the distance between the POI named name1 and name2
    using their centroid coordinates
    """
    coord1 = get_POI_coordinates(poi = poi, name = name1)
    coord2 = get_POI_coordinates(poi = poi, name = name2)

    route = route_between_coordinates(streets= streets, coord1= coord1,
    coord2= coord2, weight = weight)
    print(route)
    if route == None:
        print(f"/!\\ Warning /!\\ No route between {name1} and {name2}")
    return route

def get_POI_coordinates(poi: gpd.GeoDataFrame, name : str):
    coord = poi[poi['name']==name]['center'][0]
    coord = np.array(coord)
    return (coord[0], coord[1])

##########################################
##### Cuisine data exploration function ##
##########################################

def get_type_cuisine(amenities : gpd.GeoDataFrame, unique= True):
    type_restaurants = amenities['cuisine'].value_counts()
    if not unique:
        type_restaurants = {"type_cuisine":type_restaurants.keys(), "nb_cuisine":type_restaurants.values}
        df = pd.DataFrame.from_dict(type_restaurants)
        return df

    unique_keys = []
    double_keys = []
    unique_number = []
    for k in type_restaurants.keys():
        split = k.split(';')
        if k== 'chinese;japanese':
            print(split, len(split))
        if len(split) > 1:
            #sometimes the cuisine type are on the format 'italian;pizza', we will count it as 1 pizza and 1 italian
            double_keys.append(k)
        else :
            unique_keys.append(k)
    for k in double_keys: #not very optimal
        #update of the values
        for l in k.split(';'):
            if l in unique_keys:
                type_restaurants[l] += 1
            else:
                type_restaurants[l] = 1
                unique_keys.append(l)
    unique_type = {k:type_restaurants[k] for k in unique_keys}
    double_type = {k:type_restaurants[k] for k in double_keys}
    print(sum(double_type.values()), " type de cuisine en doublon ont été incorporé dans",
    sum(unique_type.values()), "style de cuisine")

    unique_type = {"type_cuisine":unique_type.keys(), "nb_cuisine":unique_type.values()}
    return pd.DataFrame(unique_type)

def counting_unique_subvalues(df : pd.DataFrame, var, relative= False):
    """
        Counting values of a categorical var in a dataframe where thoses values can have multiple subvalues.
        returns a dictionnary with for every entry the number of values counted
        the code is probably suboptimal
    """
    counts = df[var].value_counts()
    # for now we only separate list variables, could be extended to str with a split(separator)
    list_counts = counts.tolist()
    unique_values = [] #unique values are str
    multiple_values = [] #multiple are list
    for i,k in enumerate(counts.keys()):
        if type(k)==str:
            unique_values.append((i,k))
        elif type(k)==list:
            multiple_values.append((i,k))
    counts = {k:list_counts[i] for (i,k) in unique_values}
    #we transform it in dataframe because of unhashable type and we keep only the unique values, and we transform it into a dictionnary because
    for i,k in multiple_values:
        for subk in k:
            if subk in counts.keys():
                counts[subk] += list_counts[i]
            else :
                unique_values.append((i,subk))
                counts[subk] = list_counts[i]
    if relative:
        total = sum(counts.values())
        for (i,k) in counts.keys():
            counts[k]= counts[k]/total
    return counts

##########################################
##### Aggregation function ########
##########################################

def count_POI_within_polygon(gdf : gpd.GeoDataFrame,  categories = categories_tags.keys()):
    """
    count for each polygons in the polygons list how many POI correspond to each category
    take as arguments a geodataframe with polygon as index, a list of categories_tags's keys"""
    number_poi_by_cat = {}
    for cat in categories:
        number_poi_by_cat[cat] = []
        for poly, row in tqdm(gdf.iterrows()):
            n = len(get_polygon_POI_category(polygon= poly, categories=[cat]))
            number_poi_by_cat[cat].append(n)
    for cat in categories:
        gdf[cat] = number_poi_by_cat[cat] 
    return gdf

def aggregating_from_dummies_on_grid(grid, osmgdf,
                                     geometry = "geometry",
                                     categories = categories_tags.keys()
):
    agg_nb_grid = {}
    for cat in categories:
        agg_nb_grid[cat] = []
    for i in range(len(grid)):
        isin = osmgdf.within(grid[geometry][i])
        nb = osmgdf[categories][isin].sum()
        for cat in categories:
            agg_nb_grid[cat].append(nb[cat])
    for cat in categories:
        grid[cat] = agg_nb_grid[cat]
    return grid 


def get_POI_cat_on_INSPIRE_grid(url :str, city : str = "Paris", reduced_cat = True):
    pgdf = gpd.read_file(url)
    pgdf = pgdf.to_crs("EPSG:4326")
    if reduced_cat:
        osmgdf = get_place_POI(city)
        # je comprend pas le warning  : j'ai projeté en WGS-84.
        return aggregating_from_dummies_on_grid(pgdf,osmgdf)
    else:
        categories = dict()
        for s in shops:
            categories[s]=[s]
        for a in amenities:
            categories[a]=[a]
        
        osmgdf = get_place_POI("Paris", categories=categories.keys(), tags_for_cat = categories)
        return aggregating_from_dummies_on_grid(pgdf,osmgdf,categories = categories.keys())



##########################################
##### 2SFCA function ########
##########################################

def calculate_2SFCA_demand(gdf,weights_by_id,
    weight_age = {
        'Ind_0_3':1,
        "Ind_4_5" : 1,
        "Ind_6_10" : 1,
        "Ind_11_17" : 1,
        "Ind_18_24" : 1,
        "Ind_25_39" : 1,
        "Ind_40_54" : 1,
        "Ind_55_64" : 1,
        "Ind_65_79" : 1,
        "Ind_80p" : 1,
        "Ind_inc" : 1
    }
):
    """
    gdf and weights_by_id must use the same id.
    """
    f = lambda row: calcule_individual_demand(row = row, weight_age= weight_age)
    demand = gdf.apply(f, axis = 'columns',raw = False)
    weighted_demand = weights_by_id.multiply(other = demand,axis=0) 
    # we have for each column i the series of individual demande j * weight ij
    return weighted_demand.sum() # donne pour chaque carré sa zone de patientèle cad le nombre de personnes
    # qui veulent recevoir le service, sommé par les poids décroissants avec la distance


def calcule_individual_demand(row,
    weight_age = {
        'Ind_0_3':1,
        "Ind_4_5" : 1,
        "Ind_6_10" : 1,
        "Ind_11_17" : 1,
        "Ind_18_24" : 1,
        "Ind_25_39" : 1,
        "Ind_40_54" : 1,
        "Ind_55_64" : 1,
        "Ind_65_79" : 1,
        "Ind_80p" : 1,
        "Ind_inc" : 1
    }):
    demand = 0
    for k in weight_age.keys():
        demand += row[k]*weight_age[k]
    return demand

def calculate_2SFCA_accessibility_var(supply,demand,weights_by_id):
    ratio = supply/demand
    weighted_ratio = weights_by_id.multiply(other = ratio,axis=0) 
    return weighted_ratio.sum()

def calculate_distanceband_weights(gdf, idCol = "IdINSPIRE",geometryCol="geometry",threshold = 1):
    # donner directement par la fonction de pysal
    # for each i in ids, we attribute the list (dataframe with  id in index) of the weight of j from i
    radius = geometry.sphere.RADIUS_EARTH_KM
    gdf.reset_index(inplace=True)
    w_db = weights.distance.DistanceBand.from_dataframe(gdf,threshold=threshold,binary = False,radius = radius,geom_col = geometryCol, ids = idCol)
    # poids calculé en faisant la fonction inverse de la distance euclidienne entre les polygons (entre leurs centroids ?)
    # thresold de 1km <=> 15mn de marche à 4km/h
    for id in gdf["IdINSPIRE"]:
        w_db[id][id]=10.0
    full_matrix,ids = w_db.full()
    max_weight = 10.0 * threshold
    weights_by_id = pd.DataFrame(index = ids)
    for i,id in enumerate(ids):
        weights_by_id = weights_by_id.join(pd.Series(index = ids,data=full_matrix[i],name=id))
        weights_by_id[id][id] = max_weight
    gdf.set_index(idCol,inplace= True)
    weights_by_id= weights_by_id/max_weight
    return weights_by_id

def calculate_2SFCA_accessibility(gdf, interestsVar, weights_by_id,weight_age={
        'Ind_0_3':1,
        "Ind_4_5" : 1,
        "Ind_6_10" : 1,
        "Ind_11_17" : 1,
        "Ind_18_24" : 1,
        "Ind_25_39" : 1,
        "Ind_40_54" : 1,
        "Ind_55_64" : 1,
        "Ind_65_79" : 1,
        "Ind_80p" : 1,
        "Ind_inc" : 1
    }
):
    """
    gdf : gpd.GeoDataFrame
    interestsVar : list of gdf's var we want to calculate the accessibility. Needs to be summable.
    Les tranches d'âge suivantes :
    Ind_0_3 : Nombre d’individus de 0 à 3 ans
    Ind_4_5 : Nombre d’individus de 4 à 5 ans
    Ind_6_10 : Nombre d’individus de 6 à 10 ans
    Ind_11_17 : Nombre d’individus de 11 à 17 ans
    Ind_18_24 : Nombre d’individus de 18 à 24 ans
    Ind_25_39 : Nombre d’individus de 25 à 39 ans
    Ind_40_54 : Nombre d’individus de 40 à 54 ans
    Ind_55_64 : Nombre d’individus de 55 à 64 ans
    Ind_65_79 : Nombre d’individus de 65 à 79 ans
    Ind_80p : Nombre d’individus de 80 ans ou plus
    Ind_inc : Nombre d’individus dont l’âge est inconnu 
    weight = decaying distance function matrix
    represented as a dataframe : col name = IdINSPIRE of the corresponding square, give a pd.Series of the weight.
    weight_age = dict with previous keys as entries, weights_by_id for each age as values
    weight_age can be for instance how relatively old people consumate health services compare to younger ones. 
    for now weight_age is unique. In the future we will implement the possibility to add one series of weights 
    for each variable.
    """
    demand = calculate_2SFCA_demand(gdf=gdf,weights_by_id=weights_by_id, weight_age=weight_age)
    # we use a unique demand function for now
    # but we can create a dict var:weight_age to take consideration that different age doesnt consume
    # the same type of services. And from that dict we create var:demand and we use that dict in
    # the following lambda function
    f = lambda s: calculate_2SFCA_accessibility_var(supply=s,demand=demand,weights_by_id=weights_by_id)
    return gdf[interestsVar].apply(f,axis = 0)

def aggregate_2SFCA(gdf, 
                    categories  = ['restaurant','culture and art', 'education', 'food_shops', 'fashion_beauty','supply_shops'],
                    weight = True):
    
    """
    gdf : gpd.GeoDataFrame
    categories : list
    weight : boolean (whether you want to weight each service by its importance in every day life)
    
    Returns an aggregated accessibility index based on each service accessibility indexes
    """
    
    #we weight each service by its importance : 
    for i in categories :
        gdf[str("weight_" + i)] = gdf[i].sum()/(gdf[categories].sum(axis = 1).sum())
    
    if weight : 
        for i in categories : 
            gdf[str(i + "_access" + "_norm*weight")] = (gdf[str(i + "_access")].apply(lambda x : (x - gdf[str(i + "_access")].min())/(gdf[str(i + "_access")].max() - gdf[str(i + "_access")].min())))*(1 - gdf[str("weight_" + i)])
        gdf["CS_aggregated"] = gdf[[i + "_access_norm*weight" for i in categories]].sum(axis = 1) 
        
    else : 
        for i in categories : 
            gdf[str(i + "_access" + "without_norm*weight")] = gdf[str(i + "_access")].apply(lambda x : (x - gdf[str(i + "_access")].min())/(gdf[str(i + "_access")].max() - gdf[str(i + "_access")].min()))
        gdf["CS_aggregated_without_weight"] = gdf[[i + "_accesswithout_norm*weight" for i in categories]].sum(axis = 1) 
        
    return gdf



#########################
###### Regression #######
#########################


def LM_test(df,dep_var, indep_var, w) : 
    
    """ Lagrange Multiplier tests to choose regression 
    df : DataFrame
    dep_var : str (the variable we are interested in)
    indep_var : list of str (the explanatory variables)
    w : type of weight 
    """
    ols = OLS(df[[dep_var]].values, df[indep_var].values)
    lms = spreg.LMtests(ols, w)
    print("LM error test p_value for " + str(dep_var) + " : " + str(round(lms.lme[1],4)))
    print("LM lag test p_value for " + str(dep_var) + " : " + str(round(lms.lml[1],4)))
    print("Robust LM error test p_value for " + str(dep_var) + " : " + str(round(lms.rlme[1],4)))
    print("Robust LM lag test p_value for " + str(dep_var) + " : " + str(round(lms.rlml[1],4)))
    print("LM SARMA test p_value for " + str(dep_var) + " : " + str(round(lms.sarma[1],4)))

    
def reg_spatial(gdf, dep_var, indep_var, weight): 
    """df : DataFrame
    dep_var : str (the variable we are interested in)
    indep_var : list of str (the explanatory variables)
    weight : type of weight 
    
    Runs a SARMA regression taking into account heteroskedasticity
    """
    
    m2 = spreg.GM_Combo_Het(
    # Dependent variable
    gdf[[dep_var]].values,
    gdf[indep_var].values,
    w=weight,
    name_y=dep_var,
    name_x= indep_var,) #SARMA Model

    return m2


    #########################
######## Charts #########
#########################

def composition_chart(place : str, 
                      var = 'category', 
                      tags = {"amenity": amenities, "shop" : shops},
                      categories = categories_tags.keys(),
                      city = "Paris, Ile-de-France, France"): 
    
    pois = get_place_POI(place, tags, categories, city)
    dic = {}
    for i in categories : 
        dic[i] = pois[i].sum()
    names = [x for x in list(dic.keys()) if dic[x] != 0]
    size = [x for x in list(dic.values()) if x != 0]
    #Remove values equal to 0

    # add a circle at the center to transform it in a donut chart
    my_circle=plt.Circle( (0,0), 0.7, color='white')


    # Give color names
    plt.pie(size, labels=names, autopct='%1.1f%%', pctdistance=0.85,
            colors=Pastel1_7.hex_colors, wedgeprops = { 'linewidth' : 7, 'edgecolor' : 'white' })
    p = plt.gcf()
    p.gca().add_artist(my_circle)
    
    plt.title(place)
    plt.show()


def compare_places(places : list, 
                   var = 'category', 
                   tags = {"amenity": amenities, "shop" : shops},
                   categories = categories_tags.keys(),
                   city = "Paris, Ile-de-France, France") : 
    
    list_places = []
    list_var = []
    list_number = []
    for i in tqdm(range(len(places))):
        pois = get_place_POI(places[i], tags, categories, city)
        dic = {}
        for j in categories : 
            dic[j] = pois[j].sum()
        for x in dic : 
            list_places.append(places[i])
            list_var.append(x)
            list_number.append(dic[x])
    df = pd.DataFrame({'Place' : list_places, 'Var' : list_var, 'Number' : list_number})
    fig = px.bar(df, x="Place", y = "Number", color = "Var", width=800, height=500)
    fig.update_layout(showlegend=True)
    
    return fig