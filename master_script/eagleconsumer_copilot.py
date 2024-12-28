import logging
import asyncio
import json
import os
from datetime import datetime
import pandas as pd
from typing import Dict, List
import azure.functions as func
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
from azure.storage.filedatalake.aio import DataLakeServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Event Hub Configuration
EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")

# Azure Storage Configuration
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
STORAGE_SAS_TOKEN = os.getenv("AZURE_SAS_TOKEN")
CHECKPOINT_CONTAINER = os.getenv("CHECKPOINT_CONTAINER", "checkpoints")
NORMAL_CONTAINER = os.getenv("NORMAL_CONTAINER", "normal-transactions")
SUSPICIOUS_CONTAINER = os.getenv("SUSPICIOUS_CONTAINER", "suspicious-transactions")

# Construct the storage account URL
STORAGE_URL = f"https://{STORAGE_ACCOUNT_NAME}.dfs.core.windows.net"

# Transaction monitoring thresholds
HIGH_AMOUNT_THRESHOLD = float(os.getenv("HIGH_AMOUNT_THRESHOLD", 1000000))  # $1M USD
SANCTIONED_COUNTRIES = ["PRK", "IRN", "SYR", "CUB"]  # Sanctioned countries list

class TransactionProcessor:
    def __init__(self):
        self.normal_transactions = []
        self.suspicious_transactions = []
        
        # Initialize DataLake client with SAS token
        self.datalake_service_client = DataLakeServiceClient(
            account_url=STORAGE_URL,
            credential=STORAGE_SAS_TOKEN
        )
        
    def is_suspicious(self, transaction: Dict) -> bool:
        """
        Determine if a transaction is suspicious based on defined criteria.
        """
        # Check for high amount
        amount_suspicious = transaction.get('amount_usd', 0) >= HIGH_AMOUNT_THRESHOLD
        
        # Check for sanctioned countries
        sender_country = transaction.get('sender_country')
        receiver_country = transaction.get('receiver_country')
        country_suspicious = (sender_country in SANCTIONED_COUNTRIES or 
                            receiver_country in SANCTIONED_COUNTRIES)
        
        return amount_suspicious or country_suspicious

    async def save_to_datalake(self, transactions: List[Dict], container_name: str, batch_id: str):
        """
        Save transactions to Azure Data Lake Storage as CSV file.
        """
        if not transactions:
            return

        # Convert transactions to DataFrame
        df = pd.DataFrame(transactions)
        
        # Create CSV content
        csv_content = df.to_csv(index=False).encode('utf-8')
        
        # Generate file path with year/month/day folder structure
        now = datetime.now()
        file_path = f"{now.year}/{now.month:02d}/{now.day:02d}/transactions_{batch_id}.csv"
        
        try:
            # Get container client
            container_client = self.datalake_service_client.get_file_system_client(container_name)
            
            # Create directory structure if it doesn't exist
            directory_path = f"{now.year}/{now.month:02d}/{now.day:02d}"
            directory_client = container_client.get_directory_client(directory_path)
            await directory_client.create_directory()
            
            # Create file client and upload data
            file_client = container_client.get_file_client(file_path)
            await file_client.upload_data(csv_content, overwrite=True)
            
            logging.info(f"Saved {len(transactions)} transactions to {container_name}/{file_path}")
        
        except Exception as e:
            logging.error(f"Error saving to Data Lake: {str(e)}")
            raise

    async def process_batch(self):
        """
        Process accumulated transactions and save to appropriate containers.
        """
        if self.normal_transactions or self.suspicious_transactions:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save normal transactions
            if self.normal_transactions:
                await self.save_to_datalake(
                    self.normal_transactions,
                    NORMAL_CONTAINER,
                    batch_id
                )
                self.normal_transactions = []
            
            # Save suspicious transactions
            if self.suspicious_transactions:
                await self.save_to_datalake(
                    self.suspicious_transactions,
                    SUSPICIOUS_CONTAINER,
                    batch_id
                )
                self.suspicious_transactions = []

    async def process_events(self, max_wait_time: int = 60):
        """
        Process events from Event Hub with a maximum wait time.
        """
        checkpoint_store = BlobCheckpointStore(
            blob_account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
            container_name=CHECKPOINT_CONTAINER,
            credential=STORAGE_SAS_TOKEN
        )
        
        client = EventHubConsumerClient.from_connection_string(
            conn_str=EVENT_HUB_CONNECTION_STR,
            consumer_group="$Default",
            eventhub_name=EVENT_HUB_NAME,
            checkpoint_store=checkpoint_store,
        )

        async def process_event(partition_context, event):
            try:
                # Parse event data
                event_data = json.loads(event.body_as_str(encoding='UTF-8'))
                
                # Classify transaction
                if self.is_suspicious(event_data):
                    self.suspicious_transactions.append(event_data)
                    logging.info(f"Suspicious transaction detected: {event_data['transaction_id']}")
                else:
                    self.normal_transactions.append(event_data)
                    logging.info(f"Normal transaction processed: {event_data['transaction_id']}")
                
                # Process batch if we have accumulated enough transactions
                if len(self.normal_transactions) >= 10 or len(self.suspicious_transactions) >= 1:
                    await self.process_batch()
                
                # Update checkpoint
                await partition_context.update_checkpoint(event)
                
            except Exception as e:
                logging.error(f"Error processing event: {str(e)}")
                raise

        async with client:
            try:
                # Process events for max_wait_time seconds
                await client.receive(
                    on_event=process_event,
                    starting_position="-1",  # Start from beginning
                    max_wait_time=max_wait_time
                )
            finally:
                # Process any remaining transactions
                await self.process_batch()

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
async def consumereagle_timer(myTimer: func.TimerRequest) -> None:
    """
    Azure Function timer trigger that runs every 5 minutes to process transactions.
    """
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Starting transaction processing cycle')
    
    try:
        # Initialize processor
        processor = TransactionProcessor()
        
        # Process events for 4 minutes (240 seconds)
        # This gives 1-minute buffer before the next trigger
        await processor.process_events(max_wait_time=240)
        
        logging.info('Transaction processing cycle completed successfully')
        
    except Exception as e:
        logging.error(f'Error in transaction processing cycle: {str(e)}')
        raise