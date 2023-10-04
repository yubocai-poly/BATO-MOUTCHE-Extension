import folium
import pandas as pd
import geopandas as gpd
from matplotlib import colormaps
from matplotlib.colors import ListedColormap


def folium_grid_cat_plot(gdf, var : str, cmap = 'Set1', 
coordinates =(48.8534100,2.3488000),zoom_start=12.1, discrete = False, op = 0.6):
    if discrete:
        colors = colormaps[cmap](range(len(gdf[var].unique())))
        colors = ListedColormap(colors)
        m = folium.Map(coordinates, zoom_start = zoom_start)
        m = gdf.explore(
            m = m,
            column = var,
            tooltip = var,
            tiles = 'OpenStreetMap',
            popup = True,
            cmap = colors,
            categorical = True,
            style_kwds = dict(color = "black", opacity = op,
            fillOpacity = 0.4)
        )
    else:
        m = folium.Map(coordinates, zoom_start = zoom_start)
        m = gdf.explore(
            m = m,
            column = var,
            tooltip = var,
            tiles = 'OpenStreetMap',
            popup = True,
            cmap = cmap,
            style_kwds = dict(color = "black", opacity = op,
            fillOpacity = 0.4)
        )


    return m

from matplotlib.colors import ListedColormap
from matplotlib import colormaps, rc
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statannot import add_stat_annotation
from itertools import combinations

def violin_plots(df, var_distinguante,nb_cluster,dico_var,
                  cluster_column = 'label',log_scale_required =[],cmap ='Set1',ttest= True):
    font = {'size'   : 33}

    rc('font', **font)
    #plt.rcParams.update({'font.size': 44})    
    colors = colormaps[cmap](range(nb_cluster))
    colors = sns.color_palette(colors)
    df = df.astype({cluster_column:"str"})
    order = np.sort(df[cluster_column].unique())
    fig,axs = plt.subplots(ncols = 2, nrows = len(var_distinguante)//2+(len(var_distinguante)%2),
        figsize=(30,45))
    i = 0
    for i,var in enumerate(var_distinguante):
        to_do_stat_on = []
        for j in order:
            if len(df[df[cluster_column]==j][var].dropna())>1:
                to_do_stat_on.append(j)
        pairs = list(combinations(to_do_stat_on, r=2))
        ax = axs[(i-(i%2))//2][i%2]
        x = cluster_column
        y = var
        ax = sns.violinplot(data=df, x=x, y=y, ax = ax, order = order, palette = colors, box_visible = True)
        if var in log_scale_required:
            ax.set_yscale('symlog')
        if ttest:
            ax, test_results = add_stat_annotation(ax, data=df, x=x, y=y, order=order,box_pairs=pairs,
            test='t-test_ind',
            text_format='star', loc='inside', verbose=0)
        ax.set_ylabel(dico_var[var])

    fig.tight_layout()
    plt.show()

def boxplots(df, var_distinguante,nb_cluster,dico_var,
                  cluster_column = 'label',log_scale_required =[],cmap ='Set1',ttest= True):
    colors = colormaps[cmap](range(nb_cluster))
    colors = sns.color_palette(colors)
    df = df.astype({cluster_column:"str"})
    order = np.sort(df[cluster_column].unique())
    fig,axs = plt.subplots(ncols = 2, nrows = len(var_distinguante)//2+(len(var_distinguante)%2),
        figsize=(30,45))
    i = 0

    font = {'size'   : 33}

    rc('font', **font) 

    for i,var in enumerate(var_distinguante):
        to_do_stat_on = []
        for j in order:
            if len(df[df[cluster_column]==j][var].dropna())>1:
                to_do_stat_on.append(j)
        pairs = list(combinations(to_do_stat_on, r=2))
        ax = axs[(i-(i%2))//2][i%2]
        x = cluster_column
        y = var
        ax = sns.boxplot(data=df, x=x, y=y, ax = ax, order = order, palette = colors)
        if var in log_scale_required:
            ax.set_yscale('symlog')
        if ttest:
            ax, test_results = add_stat_annotation(ax, data=df, x=x, y=y, order=order,box_pairs=pairs,
            test='t-test_ind',
            text_format='star', loc='inside', verbose=0)
        ax.set_ylabel(dico_var[var])

    fig.tight_layout()
    plt.show()