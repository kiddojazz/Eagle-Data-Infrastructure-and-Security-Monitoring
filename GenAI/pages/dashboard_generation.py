# -*- coding: utf-8 -*-
"""
Created on Fri Jan  3 13:04:57 2025

@author: olanr
"""


import sys
sys.path.append("..")
from pydantic import BaseModel
from enum import Enum
from openai_connection import get_gpt_response, openai_client
from typing import Dict, Union, List, Optional
from db_connection import create_connection, query_db_pandas, server, database, username, password
import pandas as pd
from create_streamlit_chart import create_all_gpt_charts
import streamlit as st


class ReportDescription(BaseModel):
    report_name: str
    description: str
    
class NumReports(BaseModel):
    reports: List[ReportDescription]
    num_reports: int 

class SqlQuery(BaseModel):
    output: str
    
class ChartStep(BaseModel):
    chart_type: str
    chart_description: str
    chart_title: str
    chart_columns: Optional[Dict[str, str]] = None

class GenerateCharts(BaseModel):
    chart_content: List[ChartStep]
    

class ContextTexts(Enum):
    
    TABLE_DESCRIPTION = """I have an SQL Server Table called {table_name}. The table has the following columns:
        {table_columns}
        
        These columns have sample values given below:
            {sample_column_values}
            
        """
        
    GET_SQL_FROM_PROMPT = """Help return an SQL Query that can answer the prompt: {user_prompt}. 
        Use the SQL Server Table Description given below as a guide:
        Table Description:
            {table_description}
        
        """
        
    GET_NUM_REPORTS = """Help return the number of relevant detailed reports (from 1 to 5) that can be used to answer
    the user prompt: '{user_prompt}'. 
    The reports are going to be generated using SQL queries from the SQL Server table described below:
        Table Description:
            {table_description}
    """
    
    GET_SQL_FROM_DESCRIPTION = """Help answer the user query by returning an SQL Query. 
    1. Please keep in mind that the resulting table of the SQL query will be used to create charts and graphs
    2. This SQL Query must answer the report statement and report description provided below.
    3. The SQL Query must be able to query an SQL Server Table whose description is also given below
    4. Make sure the SQL Query is valid SQL Server Query.
    5. You can make use of CTE's or Subqueries, depending on the complexity of the scenario
    
    Report Statement: {report_statement}
    Report Description: {report_description}
    
    SQL Server Table Description:
        {table_description}"""

    
    GET_CHART_SUMMARY = """Help make key decisions on what type of graphs and charts can be used to answer a user's prompt.
        
        1. **Charts and Graphs**: While you are strictly not to generate any charts yourself, include detailed instructions for chart creation. 
        Please take into consideration the number of rows of the Data provided available
            
            - **Chart Type**: Specify the appropriate chart type based on the given options (e.g., bar_chart, line_chart, etc.).
            - **Description**: Provide a brief explanation of what the chart represents, including which columns or data attributes are being plotted.
            - **Chart Title**: Suggest a clear and descriptive title for the chart.
            - **Chart Columns**: Use the data provided to return the columns required to plot the chart. (e.g., "x_col": "petal_length", "y_col": "sepal_length"). The chart columns MUST match the columns of the Data provided.
        
        2. **Inputs:**
            - **User Prompt**: (details the user's specific request) `{user_prompt}`.
            - **Data Provided**: (dictionary mapping of the dataset) `{df_map}` .
            - **Chart Names**: (list of possible chart types such as bar chart, line chart, etc.) `{chart_names}` .
            - **Chart Information**: (additional metadata or context about the chart) `{chart_map}`.
            - **Number of Rows Available**: (the number of rows in the dataset) `{num_rows}` row(s)
            
        **Output**:
            1. Chart type: [Chart Description, Chart title] 
            2. Chart columns
    
            """


class LoadTableInfo:
    
    _table_to_col_map = {
        "[eagle_monitor].[eagle_transactions_flat]":[
            (
            'transaction_id', 'transactiondate', 'sender_name', 'sender_address',
            'sender_account_number', 'sender_bank_name', 'sender_swift_code',
            'receiver_name', 'receiver_address', 'receiver_account_number',
            'receiver_bank_name', 'receiver_swift_code', 'amount_usd',
            'sender_country', 'receiver_country', 'transaction_type', 'status',
            'fee_usd', 'reference', 'processing_time', 'ip_address', 'device_id',
            'user_agent', 'channel'
           ), 
            
            ('51B89DDC-7ACB-4C82-87CB-FADF1F8CC05D', 'datetime.datetime(2024, 12, 28, 11, 0, 37, 7000)', 
             'Laura Smith', '954 Bethany Wall Apt. 315\nLaurieville, WY 64325', 'JMKA09839917659480', 
             'Morgan-Garza', 'TBIJGBEZJ86', 'Cristina Henry', '69582 Moore Plains Apt. 125\nMcknightstad, MP 20530', 
             'UQUE94229560919157', 'Preston, Roth and Watson', 'TYMFGBSS9C3', "Decimal('272.56')", 
             'KWT', 'YEM', 'WIRE_TRANSFER', 'COMPLETED', "Decimal('7.73')", 
             'Into inside do probably feeling identify quite.', "datetime.datetime(2024, 12, 28, 11, 0, 37, 697000)", 
             '48.60.29.24', 'a246b28c-a2b7-42ef-92ec-762894d3a9aa', 
             'Mozilla/5.0 (compatible; MSIE 6.0; Windows NT 5.1; Trident/3.0)', 'WEB')
            
            ]
                        }
    
    def __init__(self, table_name):
        self.table_name = table_name
        
    
    def get_table_col_map(self):
        return self._table_to_col_map
    
    def load_info(self):
        table_col_map = self.get_table_col_map()
        return table_col_map[self.table_name]
    

class ChartReference:
    
    chart_map = {"line_chart": ["df: pd.DataFrame", "x_col: str", "y_col: str", "title: str", """Plots a line chart using the specified columns from the dataframe. 'title' gives the name header on the chart"""],
                 "bar_chart": ["df: pd.DataFrame", "x_col: str", "y_col: str", "title: str", """Plots a bar chart using the specified columns from the dataframe. 'title' gives the name header on the chart"""],
                 "scatter_chart": ["df: pd.DataFrame", "x_col: str", "y_col: str", "title: str", """Plots a scatter chart using the specified columns from the dataframe, and 'title' gives the name header on the chart"""],
                 "histogram": ["df: pd.DataFrame", "col: str", "title: str", """Plots a histogram for the specified column of the dataframe. 'title' gives the name header on the chart"""],
                 "pie_chart": ["df: pd.DataFrame", "values: str", "names: str", "title: str", """Plots a pie chart for the distribution of values in a specified column. 'title' gives the name header on the chart"""],
                 "area_chart": ["df: pd.DataFrame", "x_col: str", "y_col: str", "title: str", """Plots an area chart based on cumulative values from the dataframe.   and 'title' gives the name header on the chart"""],
                 "box_plot": ["df: pd.DataFrame", "x_col: str", "y_col: str", "title: str", """Plots a box plot to show the distribution of values in one column grouped by another column.   and 'title' gives the name header on the chart"""],
                 "heatmap": ["df: pd.DataFrame", "x_col: str", "y_col: str", "values: str", "title: str", """Plots a heatmap of the correlation matrix of numerical columns in the dataframe.   and 'title' gives the name header on the chart"""],
                 "bubble_chart": ["df: pd.DataFrame", "x_col: str", "y_col: str", "size_col: str", "image_filename:str", "title: str", """Plots a bubble chart, where the size of the bubbles is determined by a specified column.   and 'title' gives the name header on the chart"""],
                 "sunburst_chart": ["df: pd.DataFrame", "path: List", "values: str", "title: str", """Plots a sunburst chart, with path being a list of columns within the dataset and 'title' gives the name header on the chart"""],
                 "choropleth_map": ["df: pd.DataFrame", "hover_column: str", "location_column: str", "color_column: str", "title: str", """Plots a choropleth map, where the size of the bubbles is determined by a specified column.'title' gives the name header on the chart"""],
                 "kde_plot": ["df: Union[pd.DataFrame, pd.Series]", "x_col: str", "group_labels: List", """Plots a Kernel Density Estimate (KDE) plot to estimate the probability density of a continuous variable. group_labels argument gives the name of the kde plot for a pandas series. If a pandas dataframe is passed, """],
                 "violin_chart": ["df: pd.DataFrame", "x_col: str", "y_col: str", "color_col: str", "title: str", """Plots a violin chart to show the distribution of data for different categories.   and 'title' gives the name header on the chart"""],
                 "funnel_chart": ["df: pd.DataFrame", "x_col: str", "y_col: str", "title: str", """Plots a funnel chart using the provided data. 'title' gives the name header on the chart"""],
                 "treemap_chart": ["df: pd.DataFrame", "path: List", "value_col: str", "color_col: str", "title: str", """Plots a treemap chart using the provided data. The 'path' argument is a list of categorical columns, 'title' gives the name header on the chart"""],
                 "density_heatmap": ["df: pd.DataFrame", "x_col: str", "y_col: str", "title: str", """Plots a density heatmap using the provided data. 'title' gives the name header on the chart"""],
                 "parallel_coordinates": ["df: pd.DataFrame", "dimensions: List", "color_col: str", "title: str", """Plots a parallel coordinates using the provided data. 'title' gives the name header on the chart"""],
                 "timeline_chart": ["df: pd.DataFrame", "x_start: str", "x_end: str", "y_col: str", "color_col: str", "title: str", """Plots a parallel coordinates using the provided data. The 'dimension' argument is a list of numeric columns, 'title' gives the name header on the chart"""],
                 "3D_scatter_plot": ["df: pd.DataFrame", "x_col: str", "y_col: str", "z_col: str", "color_col: str", "title: str", """Plots a 3D scatter plot using the provided data. 'title' gives the name header on the chart"""],
                 "radar_chart": ["df: pd.DataFrame", "unique_col: str", "aggregated_column: str", "chart_name: str", "color_col: str", "title: str", """Plots a radar chart using the provided data. 'title' gives the name header on the chart"""],
                 #"wordcloud": ["text: str", "title: str", """Plots a word cloud using the provided data. 'title' gives the name header on the chart"""]
                 
                 }
    
    chart_description_map = {"bar_chart": """Plots a bar chart using the specified columns from the dataframe. Parameters: df (pd.DataFrame): The dataframe containing the data. x_col (str): The name of the column to be plotted on the x-axis. y_col (str): The name of the column to be plotted on the y-axis. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the bar chart with annotated values on top of bars.""",
                 "line_chart": """Plots a line chart using the specified columns from the dataframe. Parameters: df (pd.DataFrame): The dataframe containing the data. x_col (str): The name of the column to be plotted on the x-axis. y_col (str): The name of the column to be plotted on the y-axis. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the line chart.""",
                 "scatter_chart": """Plots a scatter chart using the specified columns from the dataframe, with optional hue coloring. Parameters: df (pd.DataFrame): The dataframe containing the data. x_col (str): The name of the column to be plotted on the x-axis. y_col (str): The name of the column to be plotted on the y-axis. hue_col (str): The column used for coloring the points based on categories. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the scatter plot.""",
                 "histogram": """Plots a histogram for the specified column of the dataframe. Parameters: df (pd.DataFrame): The dataframe containing the data. x_col (str): The name of the column to be plotted in the histogram. image_filename (str): The filename to save the plot as an image. bins (int, optional): The number of bins to be used in the histogram. Default is 10. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the histogram with annotated bar heights.""",
                 "pie_chart": """Plots a pie chart for the distribution of values in a specified column. Parameters: df (pd.DataFrame): The dataframe containing the data. pie_col (str): The column for which the pie chart is to be plotted. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the pie chart.""",
                 "area_chart": """Plots an area chart based on cumulative values from the dataframe. Parameters: df (pd.DataFrame): The dataframe containing the data. category_col (str): The column used for grouping data in the area chart. value_col (str): The column for the values to be plotted. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the area chart.""",
                 "box_plot": """Plots a box plot to show the distribution of values in one column grouped by another column. Parameters: df (pd.DataFrame): The dataframe containing the data. x_col (str): The name of the column for categorical grouping. y_col (str): The name of the column to be plotted on the y-axis. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the box plot with calculated statistics annotated.""",
                 "heatmap": """Plots a heatmap of the correlation matrix of numerical columns in the dataframe. Parameters: df (pd.DataFrame): The dataframe containing the data. non_numeric_cols (List): List of non-numeric column names to exclude from the correlation matrix. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the heatmap.""",
                 "bubble_chart": """Plots a bubble chart, where the size of the bubbles is determined by a specified column. Parameters: df (pd.DataFrame): The dataframe containing the data. x_col (str): The name of the column to be plotted on the x-axis. y_col (str): The name of the column to be plotted on the y-axis. size_col (str): The name of the column used to determine the size of the bubbles. hue_col (str): The column used for coloring the bubbles based on categories. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the bubble chart.""",
                 "kde_plot": """Plots a Kernel Density Estimate (KDE) plot to estimate the probability density of a continuous variable. Parameters: df (pd.DataFrame): The dataframe containing the data. x_col (str): The name of the column to be plotted on the x-axis. hue_col (str): The column used for differentiating groups in the KDE plot. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the KDE plot.""",
                 "violin_chart": """Plots a violin chart to show the distribution of data for different categories. Parameters: df (pd.DataFrame): The dataframe containing the data. x_col (str): The column to be plotted on the x-axis. y_col (str): The column to be plotted on the y-axis. image_filename (str): The filename to save the plot as an image. title (str, optional): The title of the plot. Default is an empty string. Returns: None: Displays and saves the violin plot."""
                 }
    
    
    def __init__(self, chart_name: Union[str, None] = None):
        self._chart_name = chart_name if chart_name else None
        
    
    def load_map(self):
        return self.chart_map
    
    def load_description(self):
        return self.chart_description_map
    
    def select_map(self):
        if self._chart_name:
            return self.chart_map[self._chart_name]
        raise ValueError("Chart Name not specified")
        
    def load_chart_names(self):
        return list(self.chart_map.keys())
        


def get_chart_names():
    cr = ChartReference()
    chart_names = cr.load_chart_names()
    return chart_names

def get_chart_map():
    cr = ChartReference()
    chart_map = cr.load_map()
    return chart_map


def get_table_description(table_name: str):
    lti = LoadTableInfo(table_name)
    table_cols, sample_table_values = lti.load_info()
    
    table_description = ContextTexts.TABLE_DESCRIPTION.value.format(table_name = table_name, table_columns = table_cols, sample_column_values = sample_table_values)
    
    return table_description


def get_num_reports(user_prompt: str, table_name:str)->str:
    
    table_description = get_table_description(table_name)
        
    gpt_context = ContextTexts.GET_NUM_REPORTS.value.format(user_prompt = user_prompt, table_description = table_description)
    
    num_reports = get_gpt_response(text = user_prompt, 
                                   context = gpt_context, 
                                   response_format = NumReports, 
                                   openai_client = openai_client
                                   )
    return num_reports


def get_report_to_description_map(num_reports: NumReports)-> Dict:
    report_to_description_map = {}
    for report_collection in num_reports.reports:
        report_name = report_collection.report_name
        description = report_collection.description
        report_to_description_map[report_name] = description
    
    return report_to_description_map


def get_sql_from_description(user_prompt: str, report_statement: str, report_description: str):
    
    table_description = get_table_description(table_name)
    
    gpt_context = ContextTexts.GET_SQL_FROM_DESCRIPTION.value.format(report_statement = report_statement,
                                                                     report_description = report_description,
                                                                     table_description = table_description
                                                                     )
    
    sql_query = get_gpt_response(text = user_prompt, 
                                 context = gpt_context, 
                                 response_format = SqlQuery, 
                                 openai_client = openai_client
                                 )
    
    return " ".join(sql_query.output.split("\n"))
    

def get_sqls_from_descriptions(user_prompt: str, report_to_description_map: Dict)-> Dict:
    topic_to_sql_map = {}
    
    for report_statement in report_to_description_map:
        report_description = report_to_description_map[report_statement]
        sql_query = get_sql_from_description(user_prompt, report_statement, report_description)
        topic_to_sql_map[report_statement] = sql_query
        
    return topic_to_sql_map


def get_topic_to_dataframe_map(topic_to_sql_map: Dict)-> Dict:
    topic_to_df_map = {}
    for topic in topic_to_sql_map:
        sql_query = topic_to_sql_map[topic]
        query_df = query_db_pandas(sql_query, conn)
        topic_to_df_map[topic] = query_df
    
    return topic_to_df_map


def generate_chart_info_from_df(user_prompt: str, df: pd.DataFrame, max_rows: int = 100):
    
    chart_names = get_chart_names()
    chart_map = get_chart_map()
    
    gpt_context = ContextTexts.GET_CHART_SUMMARY.value.format(user_prompt = user_prompt,
                                                               df_map = df.head(max_rows).to_dict(orient= "list"), 
                                                               chart_names = chart_names, 
                                                               chart_map = chart_map,
                                                               num_rows = len(df)
                                                               )
    
    charts_object = get_gpt_response(text = user_prompt, 
                                     context = gpt_context, 
                                     response_format = GenerateCharts, 
                                     openai_client = openai_client
                                     )
    
    return charts_object

def generate_all_charts_info(user_prompt: str, topic_to_dataframe_map: Dict)-> Dict:
    topic_to_chart_info = {}
    
    for topic in topic_to_dataframe_map:
        df = topic_to_dataframe_map[topic]
        
        if isinstance(df, pd.DataFrame):
            charts_object = generate_chart_info_from_df(user_prompt, df)
            
            topic_to_chart_info[topic] = charts_object
        
    return topic_to_chart_info
        


    

if __name__ == "__main__":
    st.markdown(
        """
        # Interactive Dashboard Generator

Welcome to the **Interactive Dashboard Generator**! 🎉

This tool allows you to **generate dynamic dashboards** based on your specific data queries. Simply enter your query below, and the system will process your request to build the desired dashboard in real-time.

## How it Works:
1. **Enter Your Query**: Provide the type of visualization or data analysis you would like to see.
2. **Generate Dashboard**: Once the query is submitted, the system will automatically generate a corresponding dashboard with the appropriate charts and widgets.
3. **Interactive Exploration**: Use the interactive controls (like sliders, dropdowns, and buttons) to explore and adjust the dashboard to your preferences. (*Feature Coming Soon*)


### Example Queries:
- "Generate a line chart showing sales over time."
- "Create a bar chart comparing revenue across different regions."
- "Show a pie chart of customer segmentation by age group."

💡 **Tip**: Be as specific as possible with your query to get the most accurate dashboard.

---


### Enter Your Query:
Below is a field where you can type your query. Once entered, hit the button to generate your dashboard!


        """
        )
    user_prompt = st.chat_input("Type your query to generate the dashboard")
    
    if user_prompt:
        table_name = "[eagle_monitor].[eagle_transactions_flat]"
        
        num_reports = get_num_reports(user_prompt, table_name)
        
        report_to_description_map = get_report_to_description_map(num_reports)
        
        topic_to_sql_map = get_sqls_from_descriptions(user_prompt, report_to_description_map)
        
        conn = create_connection(server, database, username, password)
        
        topic_to_dataframe_map = get_topic_to_dataframe_map(topic_to_sql_map)
    
        topic_to_chart_info = generate_all_charts_info(user_prompt, topic_to_dataframe_map)
        st.markdown("### Generated Dashboard:")
        create_all_gpt_charts(topic_to_dataframe_map, topic_to_chart_info)