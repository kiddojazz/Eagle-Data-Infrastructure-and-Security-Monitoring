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


