import osmnx as ox
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from palettable.colorbrewer.qualitative import Pastel1_7
import plotly.express as px
import seaborn as sns
import folium

tags_transportation = {
    'Bicycle Sharing Docking Station': {"bicycle_rental": "docking_station"},
    'Bus Station': {'public_transport': 'station'},
    'Railway Station': {'railway': ["station", "halt", "tram_stop"]},
}

# tags_information = {
#     'Number of Bicycle Sharing': {'amenity': 'bicycle_rental'},
#     'Bus Station Number': {"highway": "bus_stop"},
#     'railway_station': {'railway': ["station", "halt", "tram_stop"]},
# }

# define the coordinates of the places of interest
coords_places = {
    'Gare du Nord, Paris': (48.881399, 2.357438),
    'Porte de la Chapelle, Paris': (48.8977035, 2.3594563),
    'Opéra Garnier, Paris': (48.87202885000001, 2.331785061251358),
    'Sacré Coeur, Paris': (48.88680575, 2.3430153448835087),
    'Place de la Bastille, Paris': (48.8534157, 2.3696321),
    'Arc de triomphe, Paris': (48.8737791, 2.295037226037673),
    'Olympiades, Paris': (48.8270448, 2.3664175),
    'Quartier de Javel, Paris': (48.8392472, 2.279050277443888),
    'Eglise du Saint-Esprit, Paris': (48.8382111, 2.397625542131148),
    'Place des Vosges, Paris': (48.85559575, 2.3655334556312413)
}

########################################################################################################################
# Compute the basic statistics information of the transportatino in Paris
########################################################################################################################


def count_transport_stations(coords=coords_places, 
                             tags=tags_transportation, 
                             radius=1000):
    # Initialize a dictionary to store the count of each type of station
    data = {key: [] for key in tags.keys()}

    # Iterate through each location
    for place, coordinate in coords.items():
        # Iterate through each tag
        for key, tag in tags.items():
            try:
                # Retrieve Points of Interest (POIs) for specific tags
                gdf = ox.geometries_from_point(
                    coordinate, tags=tag, dist=radius)
                data[key].append(len(gdf))
            except Exception as e:
                # If there is an error, log the error message
                print(f"Error with tag {key} at location {place}: {e}")
                data[key].append('Error')

    # Convert the data to a Pandas DataFrame
    return pd.DataFrame(data, index=coords.keys())


########################################################################################################################
# Visualization functions for the basic statistics information of the transportatino in Paris
########################################################################################################################
def composition_chart_public_transportation(df,
                      place,
                      font_name='sans-serif',
                      font_size=12,
                      fig_size=(8, 8)):
    # Extract the data for the specified place
    data_row = df.loc[place]

    # Prepare the data for the pie chart
    sizes = data_row.values.tolist()
    categories = data_row.index.tolist()

    # Set font properties
    plt.rcParams['font.size'] = font_size
    plt.rcParams['font.family'] = font_name

    # Create a pie chart with the specified figure size
    plt.figure(figsize=fig_size)
    plt.pie(sizes, labels=categories, autopct='%1.1f%%', startangle=90, pctdistance=0.85,
            colors=Pastel1_7.hex_colors, wedgeprops={'linewidth': 7, 'edgecolor': 'white'})

    # Draw a circle at the center to make it a donut chart
    center_circle = plt.Circle((0, 0), 0.70, color='white')
    plt.gcf().gca().add_artist(center_circle)

    # Equal aspect ratio ensures that pie is drawn as a circle
    plt.axis('equal')
    plt.title(f'Distribution of Amenities for {place}')

    return plt


def compare_places_public_transportation(df, font_name='sans-serif', font_size=12, fig_size=(800, 500)):
    list_places = []
    list_var = []
    list_number = []
    for place in df.index:
        for var in df.columns:
            list_places.append(place)
            list_var.append(var)
            list_number.append(df.loc[place, var])
    
    # Create a new dataframe with the lists
    df_new = pd.DataFrame({'Place': list_places, 'Variable': list_var, 'Number': list_number})

    # Create a bar chart with the new dataframe
    fig = px.bar(df_new, x="Place", y="Number", color="Variable", width=fig_size[0], height=fig_size[1])

    # Update layout with font properties
    fig.update_layout(
        showlegend=True,
        font=dict(
            family=font_name,
            size=font_size,
        )
    )
    
    return fig