# Eagle - Data Infrastructure and Security Monitoring

## Introduction
We are in a world of fast-moving data generation and with the ever-growing demand for data infrastructure that can handle the large influx of data being generated. The demand lead to the creation of Eagle.

Eagle is a real-time data platform for banks, enabling seamless data movement, real-time fraud detection, and AI-powered insights with LLMs for secure, efficient decision-making and proactive alerts.

## Project Solution
Eagle gives small organizations and large enterprises the power to control their data movement and monitor all forms of transaction happening in real-time. Also with the integration of the Large Language Model business users can ask questions based on their data in a more interactive format.

### Eagle Architecture
![Architecture](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/1.png)

**Eagle is broken down into 3 major parts and components:**

### Section A: Data Integration
Eagle is a powerful data infrastructure solution designed to handle real-time data ingestion from banking applications and APIs. It integrates with Azure Event Hub’s Transaction Namespace (similar to Apache Kafka), where messages are temporarily queued and stored for up to one hour before being forwarded to their final destination.

The data ingestion process is facilitated by a microservice architecture using Azure Functions with a Timer trigger. This acts as a producer, efficiently sending data at predefined intervals to Azure Event Hub to ensure consistent and reliable data flow.

**Data from Azure Event Hub is consumed through two key pathways:**

- **Azure Stream Analytics:** Aggregates and processes real-time data streams, inserting the results into an Azure SQL Database. This enables AI engineers and business users to access actionable, structured insights.
- **Python Integration:** A Python-based solution consumes data directly from Azure Event Hub and stores it in an Azure Storage Account, providing a flexible alternative for data storage and downstream processing.

### Section B: Security, Monitoring, and Alerts
Eagle incorporates advanced security and monitoring capabilities to safeguard sensitive data and detect suspicious activities. The consumer script intelligently routes data to two storage accounts: one for standard transactions and another dedicated to suspicious transactions.

**Suspicious Transactions are flagged using the following criteria:**

- Transactions involving individuals from countries with international sanctions, such as **"PRK," "IRN," "SYR," and "CUB."**
- Dormant accounts that suddenly initiate large fund transfers:


Flagged transactions are automatically routed to the Suspicious Transactions storage account. An Azure Function with an Event-based Blob Trigger monitors this account and sends immediate alerts to the security and anti-fraud team for further investigation. This ensures prompt action against potential threats.

### Section C: Q&A with LLM and Deployment
Eagle leverages the Azure OpenAI API to build a Retrieval-Augmented Generation (RAG) model on transaction data stored in the Azure SQL Database. This intelligent system allows business users to query their data conversationally and receive insights tailored to their needs.

The solution is deployed using Streamlit and hosted on Azure WebApp, providing an intuitive and accessible interface. With Eagle, business users can effortlessly explore their data, gain deeper insights, and make data-driven decisions in real-time.

## Provision of Resources
Before we get started with this project we need to provision some resources in Azure using the Microsoft PowerShell Template.

### Create Azure Event Hub and Namespace
The Microsoft PowerShell template with the script below will be used in creating Azure EventHub which is needed for receiving real-time data

Azure Event Hubs is a highly scalable data streaming platform and event ingestion service. It can collect and process millions of events per second with low latency.

```PowerShell
# First, ensure you're logged into Azure
Write-Output "Logging in to Azure..."
Connect-AzAccount

# Define variables for the resources
$resourceGroupName = "redpanda-rg"        # Resource Group name
$location = "EastUS"                      # Azure region
$namespaceName = "eagle-namespace"        # Event Hubs Namespace name
$eventHubName = "eaglehub"               # Event Hub name
$skuName = "Standard"                     # Pricing tier (Basic, Standard, or Premium)

try {
    # Check if resource group exists, create if it doesn't
    Write-Output "Checking resource group..."
    $resourceGroup = Get-AzResourceGroup -Name $resourceGroupName -ErrorAction SilentlyContinue
    if (-not $resourceGroup) {
        Write-Output "Creating resource group: $resourceGroupName"
        New-AzResourceGroup -Name $resourceGroupName -Location $location
    }

    # Create Event Hubs Namespace
    Write-Output "Creating Event Hubs Namespace: $namespaceName"
    $namespace = @{
        ResourceGroupName = $resourceGroupName
        Name = $namespaceName
        Location = $location
        SkuName = $skuName
    }
    New-AzEventHubNamespace @namespace

    # Wait for the namespace to be ready
    Write-Output "Waiting for namespace to be ready..."
    Start-Sleep -Seconds 30

    # Create Event Hub within the namespace
    Write-Output "Creating Event Hub: $eventHubName"
    $eventHub = @{
        ResourceGroupName = $resourceGroupName
        Namespace = $namespaceName
        Name = $eventHubName
        RetentionInDays = 1              # Retention period in days (1-7 for Standard tier)
        PartitionCount = 2               # Number of partitions (2-32)
    }
    New-AzEventHub @eventHub

    Write-Output "Event Hub creation completed successfully!"
    Write-Output "Namespace: $namespaceName"
    Write-Output "Event Hub: $eventHubName"

} catch {
    Write-Error "An error occurred:"
    Write-Error $_.Exception.Message
}
```
### Create Azure Storage Account and Stream Analytics
Using the command below to create Azure Data Lake Gen 2 and Stream Analytics for transforming and aggregating the incoming data before sending to Azure SQL Database.

```PowerShell
# Login to Azure
Write-Output "Logging in to Azure..."
Connect-AzAccount

# Variables
$resourceGroupName = "docker_rg"          # Use your existing resource group
$location = "EastUS"                      # Replace with your desired Azure region (if needed)
$storageAccountName = "eagleadls"  # Replace with your desired storage account name
$containerNames = @("checkpoints", "normal-transactions")
$streamAnalyticsJobName = "eagle-stream-analytics-job" # Replace with your desired job name

# Check if the Resource Group Exists
Write-Output "Verifying Resource Group: $resourceGroupName..."
if (-not (Get-AzResourceGroup -Name $resourceGroupName -ErrorAction SilentlyContinue)) {
    Write-Error "Resource Group $resourceGroupName does not exist. Please create it manually or specify a valid Resource Group."
    exit
} else {
    Write-Output "Resource Group $resourceGroupName exists. Proceeding with setup..."
}

# Create Storage Account (Data Lake Gen 2)
Write-Output "Creating Storage Account: $storageAccountName..."
$storageAccount = New-AzStorageAccount -ResourceGroupName $resourceGroupName `
                                        -Name $storageAccountName `
                                        -Location $location `
                                        -SkuName Standard_LRS `
                                        -Kind StorageV2 `
                                        -EnableHierarchicalNamespace $true
Write-Output "Storage Account $storageAccountName created successfully."


# Create Containers in the Storage Account
Write-Output "Creating containers in Storage Account: $storageAccountName..."
$storageContext = $storageAccount.Context
foreach ($containerName in $containerNames) {
    Write-Output "Creating container: $containerName..."
    New-AzStorageContainer -Name $containerName -Context $storageContext
    Write-Output "Container $containerName created successfully."
}

# Create Azure Stream Analytics Job
Write-Output "Creating Azure Stream Analytics Job: $streamAnalyticsJobName..."
New-AzStreamAnalyticsJob -ResourceGroupName $resourceGroupName `
                         -Name $streamAnalyticsJobName `
                         -Location $location `
                         -Sku Standard `
                         -OutputErrorPolicy Stop
Write-Output "Azure Stream Analytics Job $streamAnalyticsJobName created successfully."

Write-Output "Setup completed: Storage Account with containers and Stream Analytics Job."
```

### Producer Script
Eagle is aimed at being a data infrastructure solution, helping organization (Financial Institution) move data from one source to another with in realtime or batch process. With Eagle aimed at working in the financial institution and processing data in realtime. The producer are our transaction being made where fund is transferred between one country and the other.

![Producer](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/2.png)

👉🏾 [Producer Code](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/tree/master/eaglecopilotproducer_app)

### Deploy Producer Script to Azure Function

After successfully creating the Producer script we need to run the script in a managed service using the Azure functions with a Timer trigger. This will ensure for continued process of our script.
![Deployment](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/3.png)


In your Azure Function, you will notice the data are being sent to Azure EventHub as the transaction happens.
![Azure Function Producer](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/4.png)


### Consumer Script
The consumer script consumes data from Azure EventHub and sends the data to Azure Storage Account as a CSV file. Note, there is a logic to identify suspicious transactions based off sanctions countries and transferred amount. 

 👉🏾[Consumer Script](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/tree/master/eaglecopilotconsumer_app)

![Consumer Timer](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/5.png)



Head to your Azure Storage account to verify the consumer script is loading data as CSV to Azure Data Lake Gen 2 **normal-transaction container.**

![Conatiner Normal Transaction](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/6.png)


You can also view the ADLS data to confirm the CSV files' records.

![Adls Record](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/7.png)


The consumer script also generated a CSV file for suspicious transactions based on the logic we started earlier.

![Suspicious](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/8.png)


If you study the image below the first shows it was flagged off due to the amount being transferred and haven't made transactions for a particular period. While the second shows it was flagged off due to being part of the sanctioned countries.

![Suspicious Record 1](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/9.png)

![Record 2](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/10.png)



## Alert & Monitoring Script
For the script we will be using the Blob Trigger in Azure Function, when data drops in the suspicious container a message containing the information about the data is sent to the CyberSecurity and Compliance for further investigation about the transaction carried out.

👉🏾 [Suspicious Script](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/tree/master/suspicious_trigger)

From the image below you will notice the Azure Function capture data from Azure Storage Account and send the necessary information to Slack Channel where the security team can take the necessary action.

![Alert Trigger](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/11.png)

Sample of the image sent to Slack, this gives all the necessary information about the Data in the suspicious container.

![Slack Notification](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/12.png)

### Process & Aggregate Data
The process and aggregating of the data is done using Azure Stream Analytics then sent to Azure SQL Database

```SQL
/*
Here are links to help you get started with Stream Analytics Query Language:
Common query patterns - https://go.microsoft.com/fwLink/?LinkID=619153
Query language - https://docs.microsoft.com/stream-analytics-query/query-language-elements-azure-stream-analytics
*/


SELECT
    transaction_id,
         timestamp as transactiondate,
         sender,
         receiver,
         amount_usd,
         sender_country,
         receiver_country,
         transaction_type,
         status,
         fee_usd,
         reference,
         metadata,
         EventprocessedUtcTime as Processingtime
INTO
    [transactionoutput]
FROM
    [transactioninput]

```

In your Azure Stream Analytics, you can aggregate the data to how you want your output to look like.
![Stream Analytics](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/13.png)


Check your Azure SQL Database to know the amount of data currently loaded to the Azure SQL Database.

![Check Records](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/14.png)

First count check to know the total number of records.

![Count Records](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/15.png)

Check Count Check over a while, we can assume data are being loaded into the Azure SQL Database.

![Reconfirm Records](https://github.com/kiddojazz/Eagle-Data-Infrastructure-and-Security-Monitoring/blob/master/Images/16.png)


## RAG Model
Eagle leverages the Azure OpenAI API to build a Retrieval-Augmented Generation (RAG) model on transaction data stored in the Azure SQL Database. This intelligent system allows business users to query their data conversationally and receive insights tailored to their needs. You can also generate report and dashboard based of the question asked.

The solution is deployed using Streamlit and hosted on Azure WebApp, providing an intuitive and accessible interface. With Eagle, business users can effortlessly explore their data, gain deeper insights, and make data-driven decisions in real time.

```Python
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
```

## Code Breakdown
**Imports and Setup**
●	Imports various libraries including streamlit, pandas, and custom modules for database connections and OpenAI API interactions.
●	Sets up Streamlit's page configuration with a title and layout.
Classes and Enums
●	SqlQuery & DataExplanation: These classes define models using Pydantic for structured output from queries and explanations.
●	ContextTexts (Enum): Contains predefined text templates for SQL queries and explanations based on user prompts.

**LoadTableInfo Class**
This class manages information about database tables:
●	_table_to_col_map: A mapping of table names to their column definitions and sample values.
●	Methods:
○	get_table_col_map(): Returns column mappings.
○	load_info(): Loads column information based on a given table name.

**Functions**
1.	get_table_description(table_name): Generates a description of a specified table using its columns and sample values.
2.	get_sql_from_prompt(user_prompt): Uses OpenAI's API to generate an SQL query based on user input.
3.	get_explanation_from_df(user_prompt, df): Provides explanations of data using OpenAI's API.

**Database Interaction**
●	fetch_data(query): Queries the database using provided SQL commands and caches results for performance.

**Streamlit Application Logic**
●	Initializes session state variables for chat features and current/new datasets.
●	Displays a welcome message with instructions.
●	Handles user input through chat prompts to generate SQL queries.
●	Fetches new datasets based on generated queries.
●	Displays new/current datasets in an interactive format.

**User Interaction Features**
●	Users can activate chat features to ask questions about transaction types or other queries related to displayed datasets.
●	The application provides toggles to show new or current datasets dynamically.


## Conclusion
Eagle is a continuous process and would further require more update and improvement as during its development stage. With Eagle we have been able to create a full streaming data solution providing both security and business usecase.



