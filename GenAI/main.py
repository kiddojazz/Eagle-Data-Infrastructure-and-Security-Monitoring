# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 14:18:20 2024

@author: olanr
"""

from db_connection import (server,
                           database,
                           username,
                           password
                           )

from db_connection import create_connection, query_db_pandas
from enum import Enum
import streamlit as st
from openai_connection import get_gpt_response, openai_client
from pydantic import BaseModel
import pandas as pd

st.set_page_config(
    page_title="My Streamlit App",
    page_icon="🏠",
    layout="wide",
)

st.title("Database Data Viewer")
st.sidebar.success("Select a page above.")


table_name = "[eagle_monitor].[eagle_transactions_flat]"



class SqlQuery(BaseModel):
    output: str
    
class DataExplanation(BaseModel):
    explanation: str

class ContextTexts(Enum):
    
    TABLE_DESCRIPTION = """I have an SQL Server Table called {table_name}. The table has the following columns:
        {table_columns}
        
        These columns have sample values given below:
            {sample_column_values}
            
        """
        
    GET_SQL_FROM_PROMPT = """Help return an SQL Query that can answer the prompt: {user_prompt}.
        The SQL Query can use CTE's or subqueries as necessary.
        Give me only the SQL Query. Do NOT add any extra word, space, or character. Do NOT add "sql" to the query
        Use the SQL Server Table Description given below as a guide:
        Table Description:
            {table_description}
        
        """
        
    GET_DATA_EXPLANATION = """Help interprete and answer the user's questions based on the dataset provided below.
    The dataset will not be more than 50 rows at a time.
    Please always remind the user that the data interpretation is always based on just 50 rows of the actual dataset if the data given is 40 rows and above.
        User's Prompt: {user_prompt}
        
        Data Given: {data_given}"""


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
    


def get_table_description(table_name: str):
    lti = LoadTableInfo(table_name)
    table_cols, sample_table_values = lti.load_info()
    
    table_description = ContextTexts.TABLE_DESCRIPTION.value.format(table_name = table_name, table_columns = table_cols, sample_column_values = sample_table_values)
    
    return table_description

def get_sql_from_prompt(user_prompt: str):
    
    table_description = get_table_description(table_name)
    
    gpt_context = ContextTexts.GET_SQL_FROM_PROMPT.value.format(user_prompt = user_prompt,
                                                                table_description = table_description
                                                                )
    
    sql_query = get_gpt_response(text = user_prompt, 
                                 context = gpt_context, 
                                 response_format = SqlQuery, 
                                 openai_client = openai_client
                                 )
    
    return " ".join(sql_query.output.split("\n"))


def get_explanation_from_df(user_prompt: str, df: pd.DataFrame):
    
    
    gpt_context = ContextTexts.GET_DATA_EXPLANATION.value.format(user_prompt = user_prompt,
                                                                data_given = df.head(50)
                                                                )
    
    explanation = get_gpt_response(text = user_prompt, 
                                 context = gpt_context, 
                                 response_format = DataExplanation, 
                                 openai_client = openai_client
                                 )
    
    return explanation.explanation


# Cache the database query function to improve performance
@st.cache_data
def fetch_data(query: str):
    """
    Fetch data from the database and cache the result for faster retrieval.
    """
    conn = create_connection(server, database, username, password)
    data = query_db_pandas(query, conn)
    conn.close()
    return data


user_prompt = "Give me a summary on the transaction types"
table_name = "[eagle_monitor].[eagle_transactions_flat]"


st.markdown("""
## Welcome to the Database Viewer and Interaction Platform! 👋

We’re glad to have you here. Here's what you can do:

1. **View the Dataset**: Use the **chat feature** on the left to explore the dataset in detail.
2. **Chat with the Data**: Click the **Activate Chat** button toggle below to start interacting with the data directly.

---

Feel free to explore and ask questions about the data. We’re here to make your data exploration experience seamless and engaging! 🚀
""")



# Initialize session state for variables
if "chat_on" not in st.session_state:
    st.session_state["chat_on"] = False
if "new_query" not in st.session_state:
    st.session_state["new_query"] = ""
if "new_df" not in st.session_state:
    st.session_state["new_df"] = None
if "current_df" not in st.session_state:
    st.session_state["current_df"] = None

# Sidebar with toggle and flash message
with st.sidebar:
    st.session_state["chat_on"] = st.toggle("Activate chat", value=st.session_state["chat_on"])
    flash_placeholder = st.empty()
    messages = st.container()

    # Input prompt for query
    if prompt := st.chat_input("Ask a question or generate a query"):
        messages.chat_message("user").write(prompt)

        # Generate SQL query
        st.session_state["new_query"] = get_sql_from_prompt(prompt)

        try:
            # Fetch data for the new query
            st.session_state["new_df"] = fetch_data(st.session_state["new_query"])
        except Exception as e:
            st.error(f"Error fetching data: {e}")

        if st.session_state["chat_on"]:
            st.write("Chat activated!")
            # Generate explanation from the currently displayed data
            if st.session_state["current_df"] is not None:
                explanation = get_explanation_from_df(prompt, st.session_state["current_df"])
                messages.chat_message("assistant").write(f"{explanation}")
            else:
                st.warning("No data is currently displayed for chat.")
            flash_placeholder.empty()
        else:
            with flash_placeholder:
                st.warning("Click the **Activate Chat** button to start interacting with the data.")

# Main area
st.write("### Data Display")
# Toggles for showing/hiding data
show_new_data = st.checkbox("Show New Data Preview", value=True)
show_current_data = st.checkbox("Show Currently Displayed Data", value=True)

# Preview new data
if show_new_data and st.session_state.get("new_df") is not None:
    st.write("**New Data Preview**:")
    st.dataframe(st.session_state["new_df"])
    if st.button("Update Display Data"):
        st.session_state["current_df"] = st.session_state["new_df"]
        st.success("Display data updated!")

# Display the current data
if show_current_data and st.session_state.get("current_df") is not None:
    st.write("**Currently Displayed Data**:")
    st.dataframe(st.session_state["current_df"])

