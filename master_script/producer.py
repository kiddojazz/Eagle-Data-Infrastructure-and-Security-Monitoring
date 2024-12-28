import asyncio
import json
import os
import random
from datetime import datetime
from typing import Dict, List

from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient
from dotenv import load_dotenv
from faker import Faker
import pycountry

# Load environment variables
load_dotenv()

# Configure Azure Event Hub
EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")

# Transaction amount configurations
MIN_AMOUNT = float(os.getenv("MIN_AMOUNT", 10))
MAX_AMOUNT = float(os.getenv("MAX_AMOUNT", 500))
HIGH_RISK_MIN_AMOUNT = float(os.getenv("HIGH_RISK_MIN_AMOUNT", 1000000))
HIGH_RISK_MAX_AMOUNT = float(os.getenv("HIGH_RISK_MAX_AMOUNT", 5000000))
FRAUD_PROBABILITY = float(os.getenv("FRAUD_PROBABILITY", 0.005))

# Initialize Faker
fake = Faker()

# List of sanctioned countries (for demonstration purposes)
SANCTIONED_COUNTRIES = [
    "PRK",  # North Korea
    "IRN",  # Iran
    "SYR",  # Syria
    "CUB",  # Cuba
]

class TransactionGenerator:
    def __init__(self):
        self.country_codes = [country.alpha_3 for country in pycountry.countries]
        
    def generate_person_info(self) -> Dict:
        """Generate person information including name, address, and account details."""
        return {
            "name": fake.name(),
            "address": fake.address(),
            "account_number": fake.bban(),
            "bank_name": fake.company(),
            "swift_code": fake.swift(),
        }

    def calculate_fee(self, amount: float) -> float:
        """Calculate transaction fee based on amount."""
        base_fee = 5.0
        percentage_fee = amount * 0.01  # 1% fee
        return min(base_fee + percentage_fee, 50.0)  # Cap fee at $50

    def generate_transaction(self) -> Dict:
        """Generate a single transaction with random properties."""
        # Determine if this will be a suspicious transaction
        is_suspicious = random.random() < FRAUD_PROBABILITY

        # Set amount range based on transaction type
        if is_suspicious:
            amount = random.uniform(HIGH_RISK_MIN_AMOUNT, HIGH_RISK_MAX_AMOUNT)
            sender_country = random.choice(SANCTIONED_COUNTRIES) if random.random() < 0.3 else random.choice(self.country_codes)
        else:
            amount = random.uniform(MIN_AMOUNT, MAX_AMOUNT)
            sender_country = random.choice([c for c in self.country_codes if c not in SANCTIONED_COUNTRIES])

        receiver_country = random.choice(self.country_codes)
        
        # Generate transaction data
        transaction = {
            "transaction_id": fake.uuid4(),
            "timestamp": datetime.utcnow().isoformat(),
            "sender": self.generate_person_info(),
            "receiver": self.generate_person_info(),
            "amount_usd": round(amount, 2),
            "sender_country": sender_country,
            "receiver_country": receiver_country,
            "transaction_type": "WIRE_TRANSFER",
            "status": "COMPLETED",
            "fee_usd": round(self.calculate_fee(amount), 2),
            "reference": fake.text(max_nb_chars=50),
            "metadata": {
                "ip_address": fake.ipv4() if random.random() < 0.8 else fake.ipv6(),
                "device_id": fake.uuid4(),
                "user_agent": fake.user_agent(),
                "channel": random.choice(["MOBILE_APP", "WEB", "BRANCH", "API"]),
            }
        }
        
        return transaction

class EventHubManager:
    def __init__(self, connection_str: str, eventhub_name: str):
        self.connection_str = connection_str
        self.eventhub_name = eventhub_name

    async def send_to_eventhub(self, data: Dict):
        """Send data to Azure Event Hub."""
        try:
            producer = EventHubProducerClient.from_connection_string(
                conn_str=self.connection_str,
                eventhub_name=self.eventhub_name
            )
            print(f"Attempting to connect to Event Hub: {self.eventhub_name}")
            print(f"Using connection string starting with: {self.connection_str[:50]}...")
            
            async with producer:
                event_data_batch = await producer.create_batch()
                event_data_batch.add(EventData(json.dumps(data)))
                await producer.send_batch(event_data_batch)
        except Exception as e:
            print(f"Detailed error in send_to_eventhub: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            raise

async def main():
    """Main function to run the transaction generator."""
    if not all([EVENT_HUB_CONNECTION_STR, EVENT_HUB_NAME]):
        raise ValueError("Missing required environment variables")

    transaction_generator = TransactionGenerator()
    eventhub_manager = EventHubManager(EVENT_HUB_CONNECTION_STR, EVENT_HUB_NAME)
    
    print("Transaction generator started. Press Ctrl+C to stop.")
    transactions_sent = 0

    try:
        while True:
            try:
                # Generate and send transactions for 2 minutes
                end_time = datetime.now().timestamp() + 120  # 2 minutes
                
                while datetime.now().timestamp() < end_time:
                    # Generate transaction
                    transaction = transaction_generator.generate_transaction()
                    
                    # Send to Event Hub
                    await eventhub_manager.send_to_eventhub(transaction)
                    transactions_sent += 1
                    print(f"Sent transaction {transaction['transaction_id']} (Total: {transactions_sent})")
                    
                    # Wait 15 seconds before next transaction
                    await asyncio.sleep(15)
                
                print("Pausing for 60 seconds...")
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

    except KeyboardInterrupt:
        print(f"\nShutdown requested. Cleaning up...")
    finally:
        print(f"Shutdown complete. Total transactions sent: {transactions_sent}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Handle any top-level keyboard interrupts silently