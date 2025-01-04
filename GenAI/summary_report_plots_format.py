# -*- coding: utf-8 -*-
"""
Created on Tue Dec 31 05:39:11 2024

@author: olanr
"""


from pydantic import BaseModel
from typing import List


class LineChartFormat(BaseModel):
    x_col: str
    y_col: str
    image_filename: str 
    plot_title: str 
    
class BarChartFormat(BaseModel):
    x_col: str 
    y_col: str 
    image_filename: str 
    plot_title: str 
    
class ScatterChartFormat(BaseModel):
    x_col: str 
    y_col: str 
    hue_col: str 
    image_filename: str 
    plot_title: str 
    
class HistogramFormat(BaseModel):
    x_col: str 
    image_filename: str 
    bins: int 
    plot_title: str 

class PieChartFormat(BaseModel):
    pie_col: str 
    image_filename: str 
    plot_title: str 

class AreaChartFormat(BaseModel):
    category_col: str 
    value_col: str 
    image_filename: str 
    plot_title: str 
    
class BoxPlotFormat(BaseModel):
    x_col: str 
    y_col: str 
    image_filename: str 
    plot_title: str 
    
class HeatmapFormat(BaseModel):
    non_numeric_cols: List 
    image_filename: str 
    plot_title: str 

class BubbleChartFormat(BaseModel):
    x_col: str 
    y_col: str 
    size_col: str 
    hue_col: str 
    image_filename: str 
    plot_title: str 
    
class KdePlotFormat(BaseModel):
    x_col: str 
    hue_col: str 
    image_filename: str 
    plot_title: str 
    
class ViolinChartFormat(BaseModel):
    x_col: str 
    y_col: str 
    image_filename: str 
    plot_title: str 
    