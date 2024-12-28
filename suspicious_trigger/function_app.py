import azure.functions as func
import logging
import pandas as pd
from datetime import datetime
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from azure.storage.blob import BlobServiceClient
import io
import json

app = func.FunctionApp()
slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
SLACK_CHANNEL_ID = os.environ["SLACK_CHANNEL_ID"]

def get_safe_json_value(value, default='N/A'):
    """Safely parse JSON string or return the value as is."""
    if not value or value == 'N/A':
        return default
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except json.JSONDecodeError:
        return {'name': value} if value else {'name': default}

def format_slack_message(transaction: dict, file_path: str) -> str:
    """Format transaction data into a Slack message with better error handling."""
    try:
        # Safely parse sender and receiver information
        sender = get_safe_json_value(transaction.get('sender'))
        receiver = get_safe_json_value(transaction.get('receiver'))
        
        # Extract just the names from the sender/receiver objects
        sender_name = sender.get('name', 'N/A') if isinstance(sender, dict) else 'N/A'
        receiver_name = receiver.get('name', 'N/A') if isinstance(receiver, dict) else 'N/A'
        
        # Safely convert amount and fee to float with fallback to 0
        try:
            amount = float(transaction.get('amount_usd', 0))
        except (ValueError, TypeError):
            amount = 0
            
        try:
            fee = float(transaction.get('fee_usd', 0))
        except (ValueError, TypeError):
            fee = 0

        # Format additional details for high-value transactions
        additional_sender_details = ""
        additional_receiver_details = ""
        
        if amount > 1000000:  # For transactions over $1M, show more details
            if isinstance(sender, dict):
                additional_sender_details = (
                    f"• *Bank:* {sender.get('bank_name', 'N/A')}\n"
                    f"• *SWIFT:* {sender.get('swift_code', 'N/A')}\n"
                    f"• *Account:* {sender.get('account_number', 'N/A')}\n"
                )
            if isinstance(receiver, dict):
                additional_receiver_details = (
                    f"• *Bank:* {receiver.get('bank_name', 'N/A')}\n"
                    f"• *SWIFT:* {receiver.get('swift_code', 'N/A')}\n"
                    f"• *Account:* {receiver.get('account_number', 'N/A')}\n"
                )

        return (
            ":rotating_light: *NEW SUSPICIOUS TRANSACTION DETECTED* :rotating_light:\n\n"
            f"*File Path:*\n{file_path}\n\n"
            f"*Transaction Details*\n"
            f"• *ID:* {transaction.get('transaction_id', 'N/A')}\n"
            f"• *Amount:* ${amount:,.2f} USD\n"
            f"• *Fee:* ${fee:,.2f} USD\n\n"
            f"*Sender Information*\n"
            f"• *Name:* {sender_name}\n"
            f"{additional_sender_details}"
            f"• *Country:* {transaction.get('sender_country', 'N/A')}\n\n"
            f"*Receiver Information*\n"
            f"• *Name:* {receiver_name}\n"
            f"{additional_receiver_details}"
            f"• *Country:* {transaction.get('receiver_country', 'N/A')}\n\n"
            f"*Additional Information*\n"
            f"• *Transaction Type:* {transaction.get('transaction_type', 'N/A')}\n"
            f"• *Status:* {transaction.get('status', 'N/A')}\n"
            f"• *Timestamp:* {transaction.get('timestamp', 'N/A')}"
        )
    except Exception as e:
        logging.error(f"Error formatting message: {str(e)}")
        return f"Error processing transaction from {file_path}: {str(e)}"

def create_slack_client():
    """Create and validate Slack client with proper error handling."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    
    # Validate token format
    if not token or not token.startswith('xoxb-'):
        logging.error("Invalid Slack bot token format. Token should start with 'xoxb-'")
        raise ValueError("Invalid Slack bot token format")
        
    return WebClient(token=token)

def send_slack_alert(message: str) -> bool:
    """Send alert to Slack with enhanced error handling."""
    try:
        client = create_slack_client()
        channel_id = os.environ.get("SLACK_CHANNEL_ID")
        
        if not channel_id:
            logging.error("Slack channel ID not configured")
            return False

        response = client.chat_postMessage(
            channel=channel_id,
            text=message,
            mrkdwn=True
        )
        
        if not response.get('ok'):
            logging.error(f"Slack API error: {response.get('error', 'Unknown error')}")
            return False
            
        logging.info("Slack alert sent successfully")
        return True
        
    except SlackApiError as e:
        logging.error(f"Failed to send Slack alert: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error sending Slack alert: {str(e)}")
        return False

@app.blob_trigger(
    arg_name="myblob",
    path="suspicious-transactions/{year}/{month}/{day}/{name}.csv",
    connection="airflowdatalakestaging_STORAGE"
)
def monitor_suspicious_transactions(myblob: func.InputStream):
    """Monitor and process suspicious transactions from blob storage."""
    logging.info(f"Processing new file: {myblob.name}")
    
    try:
        # Read CSV with proper encoding and error handling
        df = pd.read_csv(io.BytesIO(myblob.read()), encoding='utf-8')
        
        if df.empty:
            logging.warning(f"Empty file received: {myblob.name}")
            return
            
        processed_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            try:
                transaction = row.to_dict()
                slack_message = format_slack_message(transaction, myblob.name)
                
                if send_slack_alert(slack_message):
                    processed_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                logging.error(f"Error processing transaction: {str(e)}")
                continue
                
        logging.info(f"File processing complete. Processed: {processed_count}, Errors: {error_count}")
                
    except Exception as e:
        error_message = f":x: *ERROR PROCESSING FILE*\nFile: {myblob.name}\nError: {str(e)}"
        logging.error(f"File processing error: {str(e)}")
        send_slack_alert(error_message)