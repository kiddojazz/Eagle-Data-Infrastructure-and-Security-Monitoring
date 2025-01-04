# -*- coding: utf-8 -*-
"""
Created on Fri Jan  3 20:25:01 2025

@author: olanr
"""


from typing import Dict
import pandas as pd
from streamlit_plots import(plot_3D_scatter_plot,
                            plot_area_chart,
                            plot_bar_chart,
                            plot_box_plot,
                            plot_bubble_chart,
                            plot_choropleth_map,
                            plot_density_heatmap,
                            plot_funnel_chart,
                            plot_heatmap,
                            plot_histogram,
                            plot_kde_plot,
                            plot_line_chart,
                            plot_parallel_coordinates,
                            plot_pie_chart,
                            plot_radar_chart,
                            plot_scatter_chart,
                            plot_sunburst_chart,
                            plot_timeline_chart,
                            plot_treemap_chart,
                            plot_violin_chart,
                            streamlit_chart_map
                            )



def create_gpt_chart(df:pd.DataFrame, chart_type: str, chart_title: str, chart_columns: Dict):
    chart_function = streamlit_chart_map[chart_type]
    chart_metadata = {"title": chart_title}
    
    chart_function_columns = {"df": df}
    chart_function_columns.update(chart_columns)
    chart_function_columns.update(chart_metadata)
    
    chart_function(**chart_function_columns)


def extract_chart_info(chart_info_content):
    chart_info = {}
    
    if len(chart_info_content.chart_content) <= 0:
        print("No chart available")
        return
        
    for chart_content in chart_info_content.chart_content:
        chart_type = chart_content.chart_type
        chart_description = chart_content.chart_description
        chart_title = chart_content.chart_title
        chart_columns = chart_content.chart_columns
        
        chart_info.setdefault("chart_type", []).extend([chart_type])
        chart_info.setdefault("chart_description", []).extend([chart_description])
        chart_info.setdefault("chart_title", []).extend([chart_title])
        chart_info.setdefault("chart_columns", []).extend([chart_columns])
    return chart_info


def create_all_gpt_charts(topic_to_dataframe_map: Dict, topic_to_chart_info: Dict):
    
    for topic in topic_to_chart_info:
        df = topic_to_dataframe_map[topic]
        chart_info_content = topic_to_chart_info[topic]
        
        if len(df) <= 0:
            print(f"DataFrame is empty for topic: '{topic}'")
            continue
        
        chart_info = extract_chart_info(chart_info_content)
        
        if not chart_info:
            print(f"No chart available for topic '{topic}'")
            continue
        
        for idx, chart_type in enumerate(chart_info["chart_type"]):
            chart_title = chart_info["chart_title"][idx]
            chart_columns = chart_info["chart_columns"][idx]
            
            print(f"Passing the information: \ndf:{df}\nchart: {chart_type}\ntitle: {chart_title}\ncols: {chart_columns}\n\n")
            
            if chart_columns and chart_title and chart_type:
                create_gpt_chart(df, chart_type, chart_title, chart_columns)
            
        