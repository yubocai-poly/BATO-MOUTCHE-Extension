import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
import folium
import pandas as pd
import urllib3
from zipfile import ZipFile
import requests
import osmnx as ox
import geopy.distance
import networkx as nx
from selenium import webdriver
import time
import os


def calculate_straight_line_distance(point1, point2):
    """Calculate the straight line distance between two points in kilometers."""
    distance = geopy.distance.distance(point1, point2).m
    return distance


def calculate_network_distance_km(network, orig_node, dest_node):
    """Calculate the distance between two nodes in a network in kilometers."""
    try:
        length_m = nx.shortest_path_length(
            network, orig_node, dest_node, weight='length')
        # Convert to kilometers and round to 3 decimal places
        return round(length_m / 1000, 3)
    except nx.NetworkXNoPath:
        print(f"No path between {orig_node} and {dest_node}")
        return None


def calculate_distance_access_zone(network, zone1_position, zone2_position):
    """
    Calculate the distance between two accessible zones in a network
    Using the formula: 
    d[AZ_i, AZ_j] = 2 * d[AZ_i, station_i] + d[station_i, Station_j] + 2 * d[station_j, AZ_j]
    """
    # Get the nearest nodes (stations) to each zone
    station1 = ox.distance.nearest_nodes(
        network, zone1_position[1], zone1_position[0])
    station2 = ox.distance.nearest_nodes(
        network, zone2_position[1], zone2_position[0])

    # Get the coordinates of the nearest nodes
    station1_coord = (network.nodes[station1]
                      ['y'], network.nodes[station1]['x'])
    station2_coord = (network.nodes[station2]
                      ['y'], network.nodes[station2]['x'])

    # Calculate the distance between the two zones
    distance_railway_walk = (calculate_straight_line_distance(zone1_position, station1_coord) +
                             calculate_straight_line_distance(zone2_position, station2_coord))
    distance_railway_train = 1.2 * \
        calculate_straight_line_distance(station1_coord, station2_coord)
    distance_railway = distance_railway_walk + distance_railway_train
    distance_walk = calculate_straight_line_distance(
        zone1_position, zone2_position)

    return distance_walk, distance_railway, distance_railway_walk, distance_railway_train


def calculate_time_access_zone(network, zone1_position, zone2_position):
    """
    Calculate the time between two accessible zones in a network
    Using the formula: 
    t[AZ_i, AZ_j] = 2 * t[AZ_i, station_i] + t[station_i, Station_j] + 2 * t[station_j, AZ_j]
    speed of walking: 80m/min
    speed of train: 700m/min
    """
    distance_walk, distance_railway, distance_railway_walk, distance_railway_train = calculate_distance_access_zone(
        network, zone1_position, zone2_position)
    time_walk = distance_walk / 80
    time_railway = distance_railway_walk / 80 + distance_railway_train / 700

    return min(time_walk, time_railway)


def calculate_distanceband_weights(gdf,
                                   network,
                                   idCol="IdINSPIRE",
                                   geometryCol="geometry",
                                   threshold=20,
                                   output_file_path="weights_by_id.csv",
                                   column_num='All'):
    """
    Calculate distance band weights for each area in a GeoDataFrame and save to CSV.
    Optimized to compute only upper triangle of the symmetric matrix to reduce computation time.
    """
    if column_num != 'All':
        gdf = gdf.head(column_num)
    if 'level_0' in gdf.columns:
        gdf = gdf.drop(columns=['level_0'])
    gdf.reset_index(inplace=True)
    weights_by_id = pd.DataFrame(index=gdf[idCol])

    for idx, row in gdf.iterrows():
        print(f"Calculating weights for {idx+1} of {len(gdf)}")
        # Start from idx + 1 to compute only upper triangle
        for idx2, row2 in gdf.loc[idx:].iterrows():
            if idx != idx2:
                time_transportation = calculate_time_access_zone(
                    network, (row[geometryCol].x, row[geometryCol].y), (row2[geometryCol].x, row2[geometryCol].y))
                weight = 15 / time_transportation ** 2 if time_transportation <= threshold else 0
            else:
                weight = 10.0  # Higher weight for the same area
            # Assign the weight to both (idx, idx2) and (idx2, idx)
            weights_by_id.at[gdf.at[idx, idCol], gdf.at[idx2, idCol]] = weight
            weights_by_id.at[gdf.at[idx2, idCol], gdf.at[idx, idCol]] = weight

    # Normalize weights and fill diagonal with 1 (self-weight)
    for id in weights_by_id.columns:
        max_weight = max(weights_by_id[id].values)
        weights_by_id[id] = weights_by_id[id] / max_weight
        weights_by_id.at[id, id] = 1.0

    gdf.set_index(idCol, inplace=True)
    weights_by_id.to_csv(output_file_path)

    return weights_by_id


def calculate_distance_node_index(gdf,
                                  network,
                                  idCol="IdINSPIRE",
                                  geometryCol="geometry",
                                  threshold=20,
                                  output_file_path="distance_by_id.csv",
                                  column_num='All'):
    """
    Calculate distance band weights for each area in a GeoDataFrame and save to CSV.
    Optimized to compute only upper triangle of the symmetric matrix to reduce computation time.
    """
    if column_num != 'All':
        gdf = gdf.head(column_num)
    if 'level_0' in gdf.columns:
        gdf = gdf.drop(columns=['level_0'])
    gdf.reset_index(inplace=True)
    distance_by_id = pd.DataFrame(index=gdf[idCol])

    for idx, row in gdf.iterrows():
        print(f"Calculating weights for {idx+1} of {len(gdf)}")
        # Start from idx + 1 to compute only upper triangle
        for idx2, row2 in gdf.loc[idx:].iterrows():
            if idx != idx2:
                distance_ = calculate_distance_access_zone(
                    network, (row[geometryCol].x, row[geometryCol].y), (row2[geometryCol].x, row2[geometryCol].y))
                distance = str(distance_[0]) + ',' + str(distance_[1]) + \
                    ',' + str(distance_[2]) + ',' + str(distance_[3])
            else:
                distance = 0.0  # Higher weight for the same area
            # Assign the weight to both (idx, idx2) and (idx2, idx)
            distance_by_id.at[gdf.at[idx, idCol],
                              gdf.at[idx2, idCol]] = distance
            distance_by_id.at[gdf.at[idx2, idCol],
                              gdf.at[idx, idCol]] = distance

    gdf.set_index(idCol, inplace=True)
    distance_by_id.to_csv(output_file_path)

    return distance_by_id


def read_distance_csv(file_path):
    """
    读取存储的 CSV 文件并返回一个 DataFrame。

    :param file_path: CSV 文件的路径
    :return: 从 CSV 文件中读取的 DataFrame
    """
    return pd.read_csv(file_path)


def compute_time(data: str):
    """
    Compute the weight of the data.
    """
    data = data.split(',')
    distance_walk, distance_railway, distance_railway_walk, distance_railway_train = float(
        data[0]), float(data[1]), float(data[2]), float(data[3])
    time_walk = distance_walk / 80
    time_railway = distance_railway_walk / 80 + distance_railway_train / 700

    return min(time_walk, time_railway)


def transfer_distance_to_weight(dataframe,
                                threshold=20
                                ):
    """
    Transfer the distance to weight.
    """
    max_weight = 10.0
    normolizer = threshold**2
    dataframe_copy = dataframe.copy()
    for i in range(dataframe_copy.shape[0]):
        for j in range(dataframe_copy.shape[1]):
            if i != j:
                time_transportation = compute_time(dataframe_copy.iloc[i, j])
                weight = normolizer / time_transportation ** 2 if time_transportation <= threshold else 0
            else:
                weight = 10.0  # Higher weight for the same area
            dataframe_copy.iloc[i, j] = weight

     # Normalize weights and fill diagonal with 1 (self-weight)
    for id in dataframe_copy.columns:
        max_weight = max(dataframe_copy[id].values)
        dataframe_copy[id] = dataframe_copy[id] / max_weight
        dataframe_copy.at[id, id] = 1.0

    dataframe_copy.iloc[0, 0] = 1.0

    return dataframe_copy

def fig_save_folium(map, file_path, file_name, width=1000, height=800, dpi=600):
    """
    Save the folium map as a PNG file.
    """
    # Save the map to an HTML file
    html_path = os.path.join(file_path, file_name + '.html')
    map.save(html_path)
    
    # Open a browser window with specified width and height
    browser = webdriver.Chrome()
    browser.set_window_size(width, height)  # Set the browser window to the desired image size
    browser.get('file:///' + os.path.realpath(html_path))
    time.sleep(3)  # Wait for map to load
    
    # Save the screenshot to a PNG file
    png_path = os.path.join(file_path, file_name + '.png')
    browser.save_screenshot(png_path)
    browser.quit()
    
    # No need to resize image as we set the browser window size already
    # No need to specify DPI as it's only relevant for printing purposes and has no effect on screen display
    
    # Remove the temporary HTML file
    os.remove(html_path)
    
    return png_path  # Return the path to the saved PNG file



###################################################################################################################
# Node Index Computations
###################################################################################################################
def compute_distance_sum(df):
    df_copy = df.copy()
    for i in range(df_copy.shape[0]):
        for j in range(df_copy.shape[1]):
            if i != j:
                data = df_copy.iloc[i,j].split(",")
                time_walk = float(data[0]) / 80
                time_railway = float(data[2]) / 80 + float(data[3]) / 700
                df_copy.iloc[i,j] = min(time_walk, time_railway)
            else:
                df_copy.iloc[i,j] = 0
    df_copy.iloc[0,0] = 0

    # compute the sum of distance for each column
    distance_sum = df_copy.sum(axis=0)
    distance_sum = pd.DataFrame(distance_sum.values, index=df_copy.columns, columns=["sum"])
    return distance_sum

def compute_distance_node_index(df):
    df_copy = df.copy()
    N = df_copy.shape[0]
    for i in range(df_copy.shape[0]):
        df_copy.iloc[i,0] = N / df_copy.iloc[i,0]

    # min-max normalization
    df_copy = (df_copy - df_copy.min()) / (df_copy.max() - df_copy.min())
    df_copy = df_copy.rename(columns={"sum": "node_index"})
    return df_copy
