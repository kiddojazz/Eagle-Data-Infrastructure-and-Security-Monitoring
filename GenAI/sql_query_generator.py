# -*- coding: utf-8 -*-
"""
Created on Tue Dec 31 00:41:06 2024

@author: olanr
"""


from pydantic import BaseModel
from enum import Enum
from openai_connection import get_gpt_response, openai_client



class SqlQuery(BaseModel):
    output: str



class ContextTexts(Enum):
    
    TABLE_DESCRIPTION = """I have an SQL Table called {table_name}. The table has the following columns:
        {table_columns}
        
        These columns have sample values given below:
            {sample_column_values}
            
        """
        
    GET_SQL_FROM_PROMPT = """Help return an SQL Query that can answer the prompt: {user_prompt}. 
        Use the Table Description given below as a guide:
        Table Description:
            {table_description}
        
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
    


def get_table_description(table_name: str):
    lti = LoadTableInfo(table_name)
    table_cols, sample_table_values = lti.load_info()
    
    table_description = ContextTexts.TABLE_DESCRIPTION.value.format(table_name = table_name, table_columns = table_cols, sample_column_values = sample_table_values)
    
    return table_description


def get_sql_from_prompt(user_prompt: str, table_name:str)->str:
    
    table_description = get_table_description(table_name)
        
    gpt_context = ContextTexts.GET_SQL_FROM_PROMPT.value.format(user_prompt = user_prompt, table_description = table_description)
    
    sql_query = get_gpt_response(text = user_prompt, 
                                 context = gpt_context, 
                                 response_format = SqlQuery, 
                                 openai_client = openai_client
                                 )
    return " ".join(sql_query.output.split("\n"))



if __name__ == "__main__":
    user_prompt = "I want the latest 5 rows of the table"
    table_name = "[eagle_monitor].[eagle_transactions_flat]"
    
    sample_query = get_sql_from_prompt(user_prompt, table_name)