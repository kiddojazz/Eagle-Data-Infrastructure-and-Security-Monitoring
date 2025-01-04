# -*- coding: utf-8 -*-
"""
Created on Thu Jan  2 03:33:50 2025

@author: olanr
"""

import streamlit as st
from typing import Dict
import pandas as pd
from summary_report_plots import (plot_area_chart,
                                  plot_bar_chart,
                                  plot_box_plot,
                                  plot_bubble_chart,
                                  plot_heatmap,
                                  plot_histogram,
                                  plot_kde_plot,
                                  plot_line_chart,
                                  plot_pie_chart,
                                  plot_scatter_chart,
                                  plot_violin_chart,
                                  plot_function_map
                                  )



def create_gpt_chart(df:pd.DataFrame, chart_type: str, chart_title: str, chart_columns: Dict, image_filename: str):
    chart_function = plot_function_map[chart_type]
    chart_metadata = {"image_filename": image_filename, "title": chart_title}
    
    chart_function_columns = {"df": df}
    chart_function_columns.update(chart_columns)
    chart_function_columns.update(chart_metadata)
    
    chart_function(**chart_function_columns)


def create_all_gpt_charts(topic_to_dataframe_map: Dict, topic_to_pdf_map: Dict):
    for topic in topic_to_pdf_map:
        df = topic_to_dataframe_map[topic]
        pdf_content = topic_to_pdf_map[topic]
        
        if len(df) <= 0:
            print(f"DataFrame is empty for topic: '{topic}'")
            
            continue
        
        for chart in pdf_content["chart_info"]:
            if len(chart) <= 0:
                print(f"No chart available for this topic: '{topic}'")
                continue
            current_chart = chart[0]
            chart_columns = current_chart.chart_columns
            chart_title = ""#current_chart.chart_title
            chart_type = current_chart.chart_type
            image_filename = current_chart.chart_image_name
    
            if chart_columns and chart_type:
                try:
                    create_gpt_chart(df, chart_type, chart_title, chart_columns, image_filename)
                except Exception:
                    continue
            
        
        

def extract_pdf_content(subtopic_steps):
    pdf_content = {}
    pdf_content["prompt_overview"] = subtopic_steps.prompt_overview
    for subtopic_step in subtopic_steps.subtopics:
        sub_header = subtopic_step.subtopic
        text = subtopic_step.text
        chart_info = subtopic_step.charts
        pdf_content.setdefault("sub_header", []).extend([sub_header])
        
        pdf_content.setdefault("text", []).extend([text])
        
        pdf_content.setdefault("chart_info", []).extend([chart_info])
        
    return pdf_content
