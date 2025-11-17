import pandas as pd
from scipy import stats
import math
import matplotlib.pyplot as plt
import numpy as np

def plot_localisation_boxplot():
    dict_df = pd.read_excel('evaluation.xlsx', sheet_name=None)
    array_localisation = []
    labels = []
    for df_name, df in dict_df.items():
        df = df.drop(index=[15, 16, 17, 18])
        array = []
        for localisation in df['localisation']:
            if math.isnan(localisation):
                continue
            array.append(localisation)
        if len(array) > 0:
            name = df_name
            if(name == "gemma-3-4b"):
                name = "gemma-4b"
            if(name == "gemma-3-12b"):
                name = "gemma-12b"
            if(name == "llama-3.2-11b-vision-instruct"):
                name = "Llama"
            if(name == "qwen2.5-vl-7b"):
                name = "Qwen"
            labels.append(name)
            array_localisation.append(array)

    #print(stats.describe(array_localisation))

    fig, ax = plt.subplots()
    ax.set_ylabel('localisation level')

    bplot = ax.boxplot(array_localisation,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_localisation]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()

def plot_loc_map():
    dict_df = pd.read_excel('evaluation.xlsx', sheet_name=None)
    array_google = []
    array_openstreet = []
    array_ign = []
    array_others = []
    labels = ["Google Maps", "OpenStreetMap", "IGN", "Others"]
    for df_name, df in dict_df.items():
        df = df.drop(index=[15, 16, 17, 18])
        i = 1
        for localisation in df['localisation']:
            if math.isnan(localisation):
                continue
            if i <= 4:
                array_google.append(localisation)
            elif i <= 8:
                array_ign.append(localisation)
            elif i <= 12:
                array_openstreet.append(localisation)
            else:
                array_others.append(localisation)
            i += 1
    

    array_localisation= [array_google, array_openstreet, array_ign, array_others]

    fig, ax = plt.subplots()
    ax.set_ylabel('localisation level')

    bplot = ax.boxplot(array_localisation,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_localisation]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()

def plot_loc_zoom():
    dict_df = pd.read_excel('evaluation.xlsx', sheet_name=None)
    array_18 = []
    array_16 = []
    array_14 = []
    array_12 = []
    labels = ["18", "16", "14", "12"]
    for df_name, df in dict_df.items():
        df = df.drop(index=[15, 16, 17, 18])
        i = 1
        for localisation in df['localisation']:
            if math.isnan(localisation):
                continue
            if i == 1 or i == 5 or i == 9:
                array_18.append(localisation)
            elif i == 2 or i == 6 or i == 10:
                array_16.append(localisation)
            elif i == 3 or i == 7 or i == 11:
                array_14.append(localisation)
            elif i == 4 or i == 8 or i == 12:
                array_12.append(localisation)
            i += 1
    

    array_localisation= [array_18, array_16, array_14, array_12]

    fig, ax = plt.subplots()
    ax.set_ylabel('localisation level')

    bplot = ax.boxplot(array_localisation,
                    tick_labels=labels)  # will be used to label x-ticks

    # Force y-axis to display decimal values instead of rounding to integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=False))

    # Calculate and plot the mean for each distribution
    means = [np.mean(data) for data in array_localisation]
    ax.scatter(range(1, len(means) + 1), means, color='red', marker='D', s=50, zorder=3, label='Mean')
    ax.legend()

    plt.show()

if __name__ == "__main__":
    plot_loc_zoom()