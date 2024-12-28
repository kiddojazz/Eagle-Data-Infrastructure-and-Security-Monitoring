import logging
import asyncio
import json
import os
import random
from datetime import datetime
from typing import Dict
import azure.functions as func
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient
from faker import Faker
import pycountry

app = func.FunctionApp()

# Initialize configurations
fake = Faker()
MIN_AMOUNT = float(os.getenv("MIN_AMOUNT", 10))
MAX_AMOUNT = float(os.getenv("MAX_AMOUNT", 500))
HIGH_RISK_MIN_AMOUNT = float(os.getenv("HIGH_RISK_MIN_AMOUNT", 1000000))
HIGH_RISK_MAX_AMOUNT = float(os.getenv("HIGH_RISK_MAX_AMOUNT", 5000000))
FRAUD_PROBABILITY = float(os.getenv("FRAUD_PROBABILITY", 0.005))
SANCTIONED_COUNTRIES = ["PRK", "IRN", "SYR", "CUB"]

class TransactionGenerator:
    def __init__(self):
        self.country_codes = [country.alpha_3 for country in pycountry.countries]
        
    def generate_person_info(self) -> Dict:
        return {
            "name": fake.name(),
            "address": fake.address(),
            "account_number": fake.bban(),
            "bank_name": fake.company(),
            "swift_code": fake.swift(),
        }

    def calculate_fee(self, amount: float) -> float:
        base_fee = 5.0
        percentage_fee = amount * 0.01
        return min(base_fee + percentage_fee, 50.0)

    def generate_transaction(self) -> Dict:
        is_suspicious = random.random() < FRAUD_PROBABILITY
        
        if is_suspicious:
            amount = random.uniform(HIGH_RISK_MIN_AMOUNT, HIGH_RISK_MAX_AMOUNT)
            sender_country = random.choice(SANCTIONED_COUNTRIES) if random.random() < 0.3 else random.choice(self.country_codes)
        else:
            amount = random.uniform(MIN_AMOUNT, MAX_AMOUNT)
            sender_country = random.choice([c for c in self.country_codes if c not in SANCTIONED_COUNTRIES])

        return {
            "transaction_id": fake.uuid4(),
            "timestamp": datetime.utcnow().isoformat(),
            "sender": self.generate_person_info(),
            "receiver": self.generate_person_info(),
            "amount_usd": round(amount, 2),
            "sender_country": sender_country,
            "receiver_country": random.choice(self.country_codes),
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

async def send_to_eventhub(transaction: Dict):
    connection_str = os.getenv("EVENT_HUB_CONNECTION_STR")
    eventhub_name = os.getenv("EVENT_HUB_NAME")
    
    if not all([connection_str, eventhub_name]):
        raise ValueError("Missing Event Hub connection settings")
        
    producer = EventHubProducerClient.from_connection_string(
        conn_str=connection_str,
        eventhub_name=eventhub_name
    )
    
    async with producer:
        event_data_batch = await producer.create_batch()
        event_data_batch.add(EventData(json.dumps(transaction)))
        await producer.send_batch(event_data_batch)

@app.timer_trigger(schedule="* */3 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
async def eaglebankproducer(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    try:
        transaction_generator = TransactionGenerator()
        transaction = transaction_generator.generate_transaction()
        await send_to_eventhub(transaction)
        logging.info(f'Successfully sent transaction {transaction["transaction_id"]}')
    except Exception as e:
        logging.error(f'Error generating/sending transaction: {str(e)}')