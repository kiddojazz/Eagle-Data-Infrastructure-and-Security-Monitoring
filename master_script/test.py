import asyncio
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

async def test_connection():
    # Your current connection string
    conn_str = "Endpoint=sb://eaglecopilot-namespace.servicebus.windows.net/;SharedAccessKeyName=producer-policy;SharedAccessKey=hQ0redKtLLxWYJjZwMtCDPxUVhyTBAxGS+AEhJ6omIA=;EntityPath=eaglecopilot-hub"
    
    try:
        producer = EventHubProducerClient.from_connection_string(
            conn_str=conn_str,
            eventhub_name="eaglecopilot-hub"
        )
        print("Successfully created producer client")
        
        async with producer:
            print("Successfully entered producer context")
            batch = await producer.create_batch()
            batch.add(EventData("Test message"))
            print("Successfully created batch with test message")
            await producer.send_batch(batch)
            print("Successfully sent batch")
            
    except Exception as e:
        print(f"Connection test failed with error: {type(e).__name__}")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())