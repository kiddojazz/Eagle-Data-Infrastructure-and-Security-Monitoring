# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 23:44:58 2024

@author: olanr
"""


import os
from dotenv import load_dotenv
import pyodbc
from pyodbc import OperationalError, DataError, DatabaseError, ProgrammingError, InterfaceError
import pandas as pd
from typing import Union, List


load_dotenv()

server = os.getenv("SERVER")
database = os.getenv("DATABASE")
username = os.getenv("DATABASE_USERNAME")
password = os.getenv("PASSWORD")

connection_string = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=your_server_name;"
    "Database=your_database_name;"
    "Uid=your_username;"
    "Pwd=your_password;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

def create_connection(server, database, username, password):
    
    """
    Creates a connection to a SQL Server database using PYODBC.

    Args:
        server (str): The name or IP address of the SQL Server.
        database (str): The name of the database to connect to.
        username (str): The username for authentication.
        password (str): The password for authentication.

    Returns:
        pyodbc.Connection or None: A connection object if successful, None otherwise.

    This function attempts to create a connection to a SQL Server database using the
    PYODBC library. If the connection fails, it tries an alternative connection string.
    Logs connection status and errors using a logger.
    """
    
    print(f"Creating connection to server: {server},\ndatabase: {database}")
    
    try:
        conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                      f'SERVER={server};'
                      f'DATABASE={database};'
                      f'UID={username};'
                      f'PWD={password};'  # Add semicolon here
                      'Login Timeout=30;')

        print("Connection successful.")
        return conn
    except (OperationalError, DataError, DatabaseError, ProgrammingError, InterfaceError) as e:
        print(f"Error creating connection: {e}")
        print("Trying a different connection string with DRIVER= {SQL Server}")
        try:
            conn = pyodbc.connect('DRIVER={SQL Server};'
                          f'SERVER={server};'
                          f'DATABASE={database};'
                          f'UID={username};'
                          f'PWD={password};'  # Add semicolon here
                          'Login Timeout=30;')

            print("Connection successful on 2nd attempt for PYODBC.")
            return conn
        except (OperationalError, DataError, DatabaseError, ProgrammingError, InterfaceError) as e:
            print(f"Error creating connection on 2nd attempt: {e}")    
            return None


def read_data(table_name, connection):
    
    """
    Reads data from a table in a database into a pandas DataFrame.

    Args:
        table_name (str): The name of the table in the database.
        connection (pyodbc.Connection): The database connection object.

    Returns:
        pd.DataFrame: A DataFrame containing the data from the specified table.

    This function attempts to read data from the specified table in the database
    using the provided connection and returns it as a pandas DataFrame. If an error occurs,
    it returns None and logs the error.
    """
    
    try:
        # Use pandas to read SQL query directly into a DataFrame
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, connection)
        return df
    except Exception as e:
        print("Error reading data:", e)
        return None



def query_db(query: str, conn: pyodbc.Connection)-> Union[List, None]:
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        rows = []
        # Fetch and display results
        for row in cursor.fetchall():
            rows.append(row)
    
        # Close the connection
        cursor.close()
        conn.close()
        return rows
    except pyodbc.Error as e:
        print("Error:", e)



def query_db_pandas(query: str, conn: pyodbc.Connection)-> Union[pd.DataFrame, None]:
    try:
        df = pd.read_sql_query(query, conn)
    
        return df
    except (Exception, pyodbc.Error) as e:
        print("Error:", e)
        return None
        

