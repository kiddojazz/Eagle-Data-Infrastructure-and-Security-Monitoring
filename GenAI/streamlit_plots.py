# -*- coding: utf-8 -*-
"""
Created on Tue Dec 31 00:50:27 2024

@author: olanr
"""

import streamlit as st
import plotly.express as px

import pandas as pd
import numpy as np
from typing import Union, List
import plotly.figure_factory as ff
from wordcloud import WordCloud
import matplotlib.pyplot as plt




def plot_line_chart(df, x_col, y_col, title):
  """
  Plots a line chart using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    x_col: Name of the column to use for the x-axis.
    y_col: Name of the column to use for the y-axis.
    title: Title of the chart.
  """
  fig = px.line(df, x=x_col, y=y_col, title=title)
  st.plotly_chart(fig)


def plot_bar_chart(df, x_col, y_col, title):
  """
  Plots a bar chart using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    x_col: Name of the column to use for the x-axis.
    y_col: Name of the column to use for the y-axis.
    title: Title of the chart.
  """
 
  try:
      fig = px.bar(df, x=x_col, y=y_col, title=title)
      st.plotly_chart(fig)
  except ValueError:
      pass

def plot_scatter_chart(df, x_col, y_col, title):
  """
  Plots a scatter chart using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    x_col: Name of the column to use for the x-axis.
    y_col: Name of the column to use for the y-axis.
    title: Title of the chart.
  """
  fig = px.scatter(df, x=x_col, y=y_col, title=title)
  st.plotly_chart(fig)

def plot_histogram(df, col, title):
  """
  Plots a histogram using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    col: Name of the column to use for the histogram.
    title: Title of the chart.
  """
  fig = px.histogram(df, x=col, title=title)
  st.plotly_chart(fig)


def plot_hbar_chart(df, values, names, title, num_bars: int = 10):
    
    df_top_n = df.nlargest(num_bars, values)
    
    fig = px.bar(df_top_n, x = values, y = names, title = title, orientation= "h")
    st.plotly_chart(fig)
    

def plot_pie_chart(df, values, names, title, max_categories: int = 10):
    """
    Plots a pie chart using Plotly Express.

      Args:
        df: Pandas DataFrame containing the data.
        values: Name of the column containing the values for the pie slices.
        names: Name of the column containing the labels for the pie slices.
        title: Title of the chart.
    """
    if len(df[names].unique()) < max_categories:
        fig = px.pie(df, values=values, names=names, title=title)
        st.plotly_chart(fig)
        
    else:
        if df[values].dtype in ["int64", "int32", "int16", "int8", "float64", "float32", "float16"]:
            plot_hbar_chart(df, values, names, title)
        
      
      


def plot_area_chart(df, x_col, y_col, title):
  """
  Plots an area chart using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    x_col: Name of the column to use for the x-axis.
    y_col: Name of the column to use for the y-axis.
    title: Title of the chart.
  """
  fig = px.area(df, x=x_col, y=y_col, title=title)
  st.plotly_chart(fig)


def plot_box_plot(df, x_col, y_col, title):
  """
  Plots a box plot using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    x_col: Name of the column to use for the x-axis (categorical).
    y_col: Name of the column to use for the y-axis (numerical).
    title: Title of the chart.
  """
  fig = px.box(df, x=x_col, y=y_col, title=title)
  st.plotly_chart(fig)


def plot_heatmap(df, x_col, y_col, values, title, num_vals: int = 10):
  """
  Plots a heatmap using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    x_col: Name of the column to use for the x-axis.
    y_col: Name of the column to use for the y-axis.
    values: Name of the column containing the values for the heatmap.
    title: Title of the chart.
  """
  # df_numeric = df.select_dtypes(include = ["int64", "int32", "int16", "int8", "float64", "float32", "float16"])
  # fig = px.imshow(df_numeric.corr(), color_continuous_scale = "BuPu", title=title, text_auto='.2f')
  
  try:
      df_top_n = df.nlargest(num_vals, values)
      
      heatmap_data = df_top_n.pivot_table(
          index= x_col,
          columns = y_col,
          values = values,
          fill_value= 0
          )
      
      fig = px.imshow(heatmap_data, title = title, text_auto= True)
      st.plotly_chart(fig)
  except Exception:
      return


def plot_bubble_chart(df, x_col, y_col, size_col, title):
  """
  Plots a bubble chart using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    x_col: Name of the column to use for the x-axis.
    y_col: Name of the column to use for the y-axis.
    size_col: Name of the column to use for the size of the bubbles.
    title: Title of the chart.
  """
  fig = px.scatter(df, x=x_col, y=y_col, size=size_col, title=title)
  st.plotly_chart(fig)

def plot_sunburst_chart(df, path, values, title):
  """
  Plots a sunburst chart using Plotly Express.

  Args:
    df: Pandas DataFrame containing the data.
    path: A list of columns representing the hierarchical path.
    values: Name of the column containing the values for the sunburst chart.
    title: Title of the chart.
  """
  fig = px.sunburst(df, path=path, values=values, title=title)
  st.plotly_chart(fig)


def plot_choropleth_map(df, hover_column, location_column, color_column, title):
    fig = px.choropleth(
        df,
        locations=location_column,
        color=color_column,
        hover_name=hover_column,
        title=title,
        projection="orthographic"
        )
    st.plotly_chart(fig)
                        

def plot_kde_plot(df: Union[pd.Series, pd.DataFrame], 
                  group_labels: Union[List, None] = None, 
                  curve_type: str = "kde", 
                  show_hist:bool = True
                  ):
    
    if isinstance(df, pd.Series):
        fig = ff.create_distplot([list(df)],
                                 group_labels= group_labels if group_labels else [df.name],#group_labels,
                                 curve_type=curve_type,
                                 show_hist=show_hist,
                                 )
    else:
        lol_df = [list(df[column]) for column in df.columns]
        fig = ff.create_distplot(lol_df,
                                 group_labels= df.columns,
                                 curve_type=curve_type,
                                 show_hist=show_hist,
                                 )
        
    st.plotly_chart(fig)


def plot_violin_chart(df, x_col, y_col, color_col, box = True, points = "all", title = "Violin Plot"):
    fig = px.violin(
    df,
    y=y_col,
    x=x_col,
    color=color_col,
    box=box,
    points=points,
    title=title
    )

    st.plotly_chart(fig)



def plot_funnel_chart(df, x_col, y_col, title = "Sales Funnel"):
    fig = px.funnel(df, x=x_col, y=y_col, title=title)
    st.plotly_chart(fig)    



def plot_treemap_chart(df, path: List, values_col, color_col, title = "Treemap Example"):
    fig = px.treemap(
        df,
        path=path,
        values=values_col,
        color= color_col,
        title=title
        )

    st.plotly_chart(fig)

def plot_density_heatmap(df, x_col, y_col, title = "Density Heatmap Example"):
    fig = px.density_heatmap(
        df,
        x=x_col,
        y=y_col,
        marginal_x="histogram",
        marginal_y="histogram",
        title= title
        )
    st.plotly_chart(fig)


def plot_parallel_coordinates(df, dimensions: List[str], color_col, title = "Parallel Coordinates Example"):
    fig = px.parallel_coordinates(
        df,
        dimensions=dimensions,
        color=color_col,
        title=title
        )
    st.plotly_chart(fig)


def plot_timeline_chart(df, x_start, x_end, y_col, color_col, title = "Timeline Example"):
    fig = px.timeline(
        df,
        x_start=x_start,
        x_end=x_end,
        y=y_col,
        color=color_col,
        title=title
    )
    st.plotly_chart(fig)



def plot_3D_scatter_plot(df, x_col, y_col, z_col, color_col, title = "3D Scatter Plot Example"):
    
    fig = px.scatter_3d(
        df,
        x=x_col,
        y=y_col,
        z=z_col,
        color=color_col,
        title=title
        )
    st.plotly_chart(fig)


def plot_radar_chart(df, unique_col, aggregated_column, chart_name='Performance', title="Radar Chart Example"):
    # Group and aggregate data
    new_df = df.groupby(unique_col)[aggregated_column].sum().reset_index()
    
    # Create the radar chart
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=new_df[aggregated_column],  # Radial values
        theta=new_df[unique_col],    # Categories/angles
        fill='toself',               # Fill the area
        name=chart_name,             # Legend name
        text=new_df[aggregated_column],  # Text for the values
        textposition='top center'    # Position of the text labels
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        polar=dict(radialaxis=dict(visible=True)),
    )
    
    # Display the chart
    st.plotly_chart(fig)


def plot_wordcloud(text, title = "Word Cloud Example"):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

    # Plot the Word Cloud
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")  # Remove axes

    # Display in Streamlit
    st.title(title)
    st.pyplot(fig)
    
    

streamlit_chart_map = {"area_chart": plot_area_chart, 
                     "bar_chart": plot_bar_chart, 
                     "box_plot": plot_box_plot,
                     "bubble_chart": plot_bubble_chart,
                     "heatmap": plot_heatmap,
                     "histogram": plot_histogram,
                     "kde_plot": plot_kde_plot,
                     "line_chart": plot_line_chart,
                     "pie_chart": plot_pie_chart,
                     "scatter_chart": plot_scatter_chart,
                     "violin_chart": plot_violin_chart,
                     "radar_chart": plot_radar_chart,
                     "3D_scatter_plot": plot_3D_scatter_plot,
                     "timeline_chart": plot_timeline_chart,
                     "parallel_coordinates": plot_parallel_coordinates,
                     "density_heatmap": plot_density_heatmap,
                     "treemap_chart": plot_treemap_chart,
                     "funnel_chart": plot_funnel_chart,
                     "choropleth_map": plot_choropleth_map,
                     "sunburst_chart": plot_sunburst_chart
                     }


if __name__ == "__main__":
    
    # Sample data for line chart
    df_line = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', end='2023-12-31', freq='ME'),
        'sales': np.random.randint(1000, 5000, size=12)
    })
    
    # Sample data for bar chart
    df_bar = pd.DataFrame({
        'category': ['A', 'B', 'C', 'D'],
        'values': np.random.randint(10, 50, size=4)
    })
    
    # Sample data for scatter chart
    df_scatter = pd.DataFrame({
        'feature1': np.random.randn(50),
        'feature2': np.random.randn(50)
    })
    
    # Sample data for histogram
    df_hist = pd.DataFrame({'age': np.random.randint(18, 65, size=100)})
    
    # Sample data for pie chart
    df_pie = pd.DataFrame({
        'category': ['A', 'B', 'C'],
        'count': np.random.randint(10, 30, size=3)
    })
    
    # Sample data for area chart
    df_area = df_line.copy()
    
    # Sample data for box plot
    df_box = pd.DataFrame({
        'group': np.random.choice(['A', 'B', 'C'], size=100),
        'values': np.random.randn(100)
    })
    
    # Sample data for heatmap
    df_heatmap = pd.DataFrame({
        'a_values': np.random.randint(0, 100, size=20),
        'b_values': np.random.randint(0, 100, size=20),
        'c_values': np.random.randint(0, 100, size=20),
        'x_values': np.random.randint(0, 100, size=20),
        'y_values': np.random.randint(0, 100, size=20),
        'z_values': np.random.randint(0, 100, size=20)
    })
    
    
    # Sample data for bubble chart
    df_bubble = pd.DataFrame({
        'x_col': np.random.randn(20),
        'y_col': np.random.randn(20),
        'size_col': np.random.randint(10, 50, size=20)
    })
    
    # Sample data for sunburst chart
    df_sunburst = pd.DataFrame({
        "categories": ["Earth", "Earth", "Earth", "Mars", "Mars", "Mars"],
        "regions": ["North America", "South America", "Europe", "North Pole", "South Pole", "Crater"],
        "populations": [500, 300, 200, 50, 25, 75],
    })
    
    
    # Sample data for kde plot
    df_kde = pd.Series(np.random.normal(loc=5, scale=2, size=1000))
    # df_kde = pd.DataFrame({
    #     "salary1": np.random.normal(loc=5, scale=2, size=1000),
    #     "salary2": np.random.normal(loc=5, scale=2, size=1000)
    #     }
    #     )
    
    # Sample data for map chart
    df_map = px.data.gapminder().query("year == 2007")
    
    # Sample data for violin plot
    df_violin = px.data.tips()
    
    # Sample data for Funnel chart
    df_funnel = pd.DataFrame({
        "Stage": ["Lead", "Qualified", "Proposal", "Negotiation", "Closed"],
        "Value": [1000, 800, 600, 400, 200]
    })
    
    # Sample data for treemap chart
    df_treemap = px.data.tips()
    
    
    # Sample data for Density Heatmap
    df_density = px.data.iris()
    
    
    # Sample data for parallel
    df_parallel = px.data.iris()
    
    
    # Sample data for timeline
    df_timeline = pd.DataFrame([
        dict(Task="Task 1", Start='2023-12-01', Finish='2023-12-05', Resource='Team A'),
        dict(Task="Task 2", Start='2023-12-03', Finish='2023-12-08', Resource='Team B'),
        dict(Task="Task 3", Start='2023-12-06', Finish='2023-12-10', Resource='Team A')
    ])
    
    
    # Sample data for 3D Scatter plot
    df_3d_scatter = px.data.iris()
    
    
    import plotly.graph_objects as go
    
    categories = ['Speed', 'Reliability', 'Comfort', 'Safety', 'Efficiency']
    
    values = [90, 80, 70, 85, 95]
    # Sample data for Radar chart
    df_radar = pd.DataFrame({"metrics": ['Speed', 'Reliability', 'Comfort', 'Safety', 'Efficiency'],
                  "values": [90, 80, 70, 85, 95]})
    
    
    
    # Sample data for word cloud
    word_cloud_text = """
    Data Science Machine Learning Artificial Intelligence Streamlit Python Cloud Computing 
    Visualization Automation Analysis Engineering Deep Learning Neural Networks NLP Computer Vision
    """
    
    
    
    
    # Example usage:
    # Assuming you have a DataFrame named 'data'
    plot_line_chart(df_line, 'date', 'sales', 'Sales Over Time')
    plot_bar_chart(df_bar, 'category', 'values', "Inventory Stock")
    plot_scatter_chart(df_scatter, 'feature1', 'feature2', 'Feature Correlation')
    plot_histogram(df_hist, 'age', 'Age Distribution')
    plot_pie_chart(df_pie, 'count', 'category', 'Category Distribution')
    plot_area_chart(df_area, 'date', 'sales', 'Sales Volume Over Time')
    plot_box_plot(df_box, 'group', 'values', 'Group Distribution')
    plot_heatmap(df_heatmap, 'x_col', 'y_col', 'values', 'Correlation Heat Map')
    plot_bubble_chart(df_bubble, 'x_col', 'y_col', 'size_col', 'Size Bubble Chart')
    plot_sunburst_chart(df_sunburst, path = ["categories", "regions"], values = "populations", title = "Sunbursting Chart")
    plot_choropleth_map(df_map, "country", "iso_alpha", "gdpPercap", "GDP Per Capita")
    plot_kde_plot(df_kde, ["Data"], "kde", True)
    plot_violin_chart(df_violin, "day", "total_bill", "sex")
    plot_funnel_chart(df_funnel, "Value", "Stage")
    plot_treemap_chart(df_treemap, ["day", "time"], "total_bill", "total_bill")
    plot_density_heatmap(df_density, "sepal_width", "sepal_length")
    plot_parallel_coordinates(df_parallel,
                              ["sepal_width", "sepal_length", "petal_width", "petal_length"],
                              "species_id")
    plot_timeline_chart(df_timeline, "Start", "Finish", "Task", "Resource")
    plot_3D_scatter_plot(df_3d_scatter, "sepal_length", "sepal_width","petal_width", "species")
    plot_radar_chart(df_radar, "metrics", "values")
    plot_wordcloud(word_cloud_text)
