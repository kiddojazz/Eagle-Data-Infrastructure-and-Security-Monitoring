CREATE PROCEDURE InsertFlattenedTransactions
AS
BEGIN
    INSERT INTO eagle_monitor.eagle_transactions_flat (
	transaction_id,
    transactiondate,
    sender_name,
    sender_address,
    sender_account_number,
    sender_bank_name,
    sender_swift_code,
    receiver_name,
    receiver_address,
    receiver_account_number,
    receiver_bank_name,
    receiver_swift_code,
    amount_usd,
    sender_country,
    receiver_country,
	transaction_type,
	"status",
	fee_usd,
	reference,
	processing_time,
	ip_address,
	device_id,
	user_agent,
	channel
    )

	SELECT 
    transaction_id,
    transactiondate,
    JSON_VALUE(sender, '$.name') AS sender_name,
    JSON_VALUE(sender, '$.address') AS sender_address,
    JSON_VALUE(sender, '$.account_number') AS sender_account_number,
    JSON_VALUE(sender, '$.bank_name') AS sender_bank_name,
    JSON_VALUE(sender, '$.swift_code') AS sender_swift_code,
    JSON_VALUE(receiver, '$.name') AS receiver_name,
    JSON_VALUE(receiver, '$.address') AS receiver_address,
    JSON_VALUE(receiver, '$.account_number') AS receiver_account_number,
    JSON_VALUE(receiver, '$.bank_name') AS receiver_bank_name,
    JSON_VALUE(receiver, '$.swift_code') AS receiver_swift_code,
    amount_usd,
    sender_country,
    receiver_country,
	transaction_type,
	status,
	fee_usd,
	reference,
	Processingtime as processing_time,
	JSON_VALUE(metadata, '$.ip_address') AS ip_address,
	JSON_VALUE(metadata, '$.device_id') AS device_id,
	JSON_VALUE(metadata, '$.user_agent') AS user_agent,
	JSON_VALUE(metadata, '$.channel') AS channel
FROM 
    [eagle_monitor].[eagle_transaction_table];

END;
