# -*- coding: utf-8 -*-
"""
Created on Tue Dec 31 02:50:12 2024

@author: olanr
"""


import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List
import os
import shutil

ROTATION = 45




def empty_folder(folder_path):
    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Iterate through the contents of the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                # Check if it is a file or directory
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Remove file or symlink
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove directory
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"The folder '{folder_path}' does not exist or is not a directory.")
        

# Function to save plots
def save_plot(fig, filename: str, folderpath: str = "./output_reports_images"):
    # Set the size of the figure
    fig.set_size_inches(5, 3)
    
    # Ensure the folder exists
    os.makedirs(folderpath, exist_ok=True)
    
    # Construct the full file path
    filepath = os.path.join(folderpath, filename)
    
    # Save the figure to the specified folder
    fig.savefig(filepath, bbox_inches="tight", dpi=200)
    
    # Print the saved file location
    if os.path.exists(filepath):
        print(f"The file exists at: {os.path.abspath(filepath)}")
    else:
        print(f"DOES NOT EXIST: {os.path.abspath(filepath)}")

def plot_line_chart(df: pd.DataFrame, x_col, y_col, image_filename: str, title: str = ""):
    fig, ax = plt.subplots()
    sns.lineplot(data=df, x=x_col, y=y_col, ax=ax)
    ax.set_title(title)
    
    plt.setp(ax.get_xticklabels(), rotation=ROTATION, ha="right")
    
    save_plot(fig, image_filename)
    plt.show()


def plot_bar_chart(df: pd.DataFrame, x_col, y_col, image_filename: str, title: str = "" ):
    print(f"Barplot dataframe:\n{df}")
    fig, ax = plt.subplots()
    if df[x_col].nunique() > 20:
        df_top_n = df.nlargest(20, y_col)
        sns.barplot(data=df_top_n, x=x_col, y=y_col, ax=ax, ci=None)
        title = "showing only "
    else:
        sns.barplot(data=df, x=x_col, y=y_col, ax=ax, ci=None)
    ax.set_title(title)
    for bar in ax.patches:
        ax.annotate(f'{bar.get_height():.2f}', 
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                    ha='center', va='bottom', fontsize=10)
    plt.setp(ax.get_xticklabels(), rotation=ROTATION, ha="right")
    save_plot(fig, image_filename)
    plt.show()


def plot_scatter_chart(df: pd.DataFrame, x_col: str, y_col: str, hue_col:str, image_filename: str, title: str = ""):
    fig, ax = plt.subplots()
    sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_col, ax=ax)
    ax.set_title(title)
    plt.setp(ax.get_xticklabels(), rotation=ROTATION, ha="right")
    save_plot(fig, image_filename)
    plt.show()

def plot_histogram(df: pd.DataFrame, x_col: str, image_filename: str, bins: int = 10, title: str = ""):
    fig, ax = plt.subplots()
    hist = sns.histplot(data=df, x="sepal_length", bins=bins, kde=True, ax=ax)
    
    ax.set_title(title)
    # Annotate bar heights
    for bar in hist.patches:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, height, f'{int(height)}', 
                    ha='center', va='bottom', fontsize=10)
    
    plt.setp(ax.get_xticklabels(), rotation=ROTATION, ha="right")
    save_plot(fig, image_filename)
    plt.show()



def plot_pie_chart(df: pd.DataFrame, pie_col: str, image_filename: str, title: str = ""):
    species_counts = df[pie_col].value_counts()
    fig, ax = plt.subplots()
    ax.pie(species_counts, labels=species_counts.index, autopct='%1.1f%%', startangle=90)
    ax.set_title(title)
    save_plot(fig, image_filename)
    plt.show()


def plot_area_chart(df: pd.DataFrame, category_col: str, value_col: str, image_filename: str, title: str = ""):
    cumulative_sum = df.groupby(category_col)[value_col].cumsum()
    df["cumulative_sum"] = cumulative_sum
    fig, ax = plt.subplots()
    sns.lineplot(data=df, x=value_col, y="cumulative_sum", hue=category_col, ax=ax)
    ax.fill_between(df[value_col], cumulative_sum, alpha=0.2)
    ax.set_title(title)
    plt.setp(ax.get_xticklabels(), rotation=ROTATION, ha="right")
    save_plot(fig, image_filename)
    plt.show()


def plot_box_plot(df: pd.DataFrame, x_col: str, y_col: str, image_filename: str, title: str = ""):
    fig, ax = plt.subplots()
    sns.boxplot(data=df, x=x_col, y=y_col, ax=ax)

    # Calculate metrics
    for species in df[x_col].unique():
        subset = df[df[x_col] == species][y_col]
        median = subset.median()
        q1 = subset.quantile(0.25)
        q3 = subset.quantile(0.75)
        iqr = q3 - q1
        min_val = subset.min()
        max_val = subset.max()

        # Position the text above the plot
        x = df[x_col].unique().tolist().index(species)
        ax.text(x, median, f'Median: {median:.2f}\nIQR: {iqr:.2f}\nMin: {min_val:.2f}\nMax: {max_val:.2f}', 
                ha='center', va='bottom', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
    
    ax.set_title(title)
    save_plot(fig, image_filename)
    plt.show()


def plot_heatmap(df: pd.DataFrame, non_numeric_cols: List, image_filename: str, title: str = ""):
    try:
        corr = df.drop(non_numeric_cols, axis = 1).corr()  # Compute correlation matrix
    except KeyError:
        return
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
    ax.set_title(title)
    save_plot(fig, image_filename)
    plt.show()


def plot_bubble_chart(df: pd.DataFrame, x_col: str, y_col: str, size_col: str, hue_col: str, image_filename:str, title: str = ""):
    fig, ax = plt.subplots()
    scatter = sns.scatterplot(data=df, x=x_col, y=y_col, size=size_col, 
                               hue=hue_col, sizes=(20, 200), ax=ax)

    # Move legend outside
    scatter.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    ax.set_title(title)
    plt.setp(ax.get_xticklabels(), rotation=ROTATION, ha="right")
    save_plot(fig, image_filename)
    plt.show()


def plot_kde_plot(df: pd.DataFrame, x_col: str, hue_col: str, image_filename: str, title: str = ""):
    fig, ax = plt.subplots()
    sns.kdeplot(data=df, x=x_col, hue=hue_col, fill=True, ax=ax)
    ax.set_title(title)
    save_plot(fig, image_filename)
    plt.show()



def plot_violin_chart(df: pd.DataFrame, x_col: str, y_col: str, image_filename: str, title: str = ""):
    fig, ax = plt.subplots()
    sns.violinplot(data=df, x=x_col, y=y_col, ax=ax)

    for unique_val in df[x_col].unique():
        subset = df[df[x_col] == unique_val][y_col]
        mean = subset.mean()
        median = subset.median()
        q1 = subset.quantile(0.25)
        q3 = subset.quantile(0.75)

        # Position the text above the plot
        x = df[x_col].unique().tolist().index(unique_val)
        ax.text(x, mean, f'Mean: {mean:.2f}\nMedian: {median:.2f}\nQ1: {q1:.2f}\nQ3: {q3:.2f}', 
                ha='center', va='bottom', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
    
    ax.set_title(title)
    save_plot(fig, image_filename)
    plt.show()


plot_function_map = {"area_chart": plot_area_chart, 
                     "bar_chart": plot_bar_chart, 
                     "box_plot": plot_box_plot,
                     "bubble_chart": plot_bubble_chart,
                     "heatmap": plot_heatmap,
                     "histogram": plot_histogram,
                     "kde_plot": plot_kde_plot,
                     "line_chart": plot_line_chart,
                     "pie_chart": plot_pie_chart,
                     "scatter_chart": plot_scatter_chart,
                     "violin_chart": plot_violin_chart}

if __name__ == "__main__":
    # Example DataFrame
    df = sns.load_dataset("iris")  # Replace with your own dataset
    
    plot_line_chart(df=df, x_col="sepal_length", y_col="sepal_width", image_filename= "line_chart.png", title = "Test Bar Chart")
    
    plot_bar_chart(df=df, x_col="species", y_col="sepal_length", image_filename="bar_chart_with_values.png")
    
    plot_scatter_chart(df=df, x_col="sepal_length", y_col="sepal_width", hue_col="species", image_filename ="scatter_chart.png")
    
    plot_histogram(df = df, x_col = "sepal_length", image_filename="histogram_with_values.png")
    
    plot_pie_chart(df = df, pie_col = "species", image_filename = "pie_chart.png")
    
    plot_area_chart(df = df, category_col= "species", value_col = "sepal_length", image_filename = "area_chart.png")
    
    plot_box_plot(df = df, x_col = "species", y_col = "sepal_length", image_filename= "box_plot_with_metrics.png")
    
    plot_heatmap(df = df, non_numeric_cols= ["species"], image_filename="heatmap.png")
    
    plot_bubble_chart(df = df, x_col = "sepal_length", y_col = "sepal_width", size_col="petal_length", hue_col= "species", image_filename = "bubble_chart_with_legend_outside.png")
    
    plot_kde_plot(df = df, x_col = "sepal_length", hue_col = "species", image_filename="kde_plot.png")
    
    plot_violin_chart(df = df, x_col = "species", y_col = "sepal_length", image_filename= "violin_chart_with_metrics.png")
    


# def plot_bar_chart():
#     fig, ax = plt.subplots()
#     sns.barplot(data=df, x="species", y="sepal_length", ax=ax, ci=None)
#     save_plot(fig, "bar_chart.png")
#     plt.show()

# plot_bar_chart()

# def plot_histogram():
#     fig, ax = plt.subplots()
#     sns.histplot(data=df, x="sepal_length", bins=10, kde=True, ax=ax)
#     save_plot(fig, "histogram.png")
#     plt.show()

# plot_histogram()


# def plot_box_plot():
#     fig, ax = plt.subplots()
#     sns.boxplot(data=df, x="species", y="sepal_length", ax=ax)
#     save_plot(fig, "box_plot.png")
#     plt.show()

# plot_box_plot()


# def plot_bubble_chart():
#     fig, ax = plt.subplots()
#     sns.scatterplot(data=df, x="sepal_length", y="sepal_width", size="petal_length", hue="species", sizes=(20, 200), ax=ax)
#     save_plot(fig, "bubble_chart.png")
#     plt.show()

# plot_bubble_chart()

# def plot_violin_chart():
#     fig, ax = plt.subplots()
#     sns.violinplot(data=df, x="species", y="sepal_length", ax=ax)
#     save_plot(fig, "violin_chart.png")
#     plt.show()

# plot_violin_chart()