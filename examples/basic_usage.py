from getsms import GetSMSClient, GetSMSError

client = GetSMSClient(user="your_username", api_key="your_api_key")

# Check balance
print("Balance:", client.balance())

# List available services (optional: filter by name)
services = client.list_services(service="WhatsApp")
for s in services:
    print(f"{s['name']}: ${s['price']}  (available: {s['otp_available']})")

# Request a number for WhatsApp
try:
    requests = client.request_number("WhatsApp")
    req = requests[0]
    print(f"Got number: {req['mdn']}  (request ID: {req['id']})")

    # Wait for an SMS (polls every 15 seconds, up to 15 minutes)
    # If no SMS arrives the request is cancelled automatically by the server
    sms = client.wait_for_sms(req["id"], timeout=900, poll_interval=15)
    if sms:
        print(f"SMS received: {sms['reply']}")
        print(f"PIN: {sms['pin']}")
    else:
        print("No SMS received within the timeout period.")

except GetSMSError as e:
    print(f"Error: {e}")


# Request a number from California for Google
try:
    requests = client.request_number("Google", state="CA")
    print(requests[0])
except GetSMSError as e:
    print(f"Error: {e}")


# Priority request for multiple services at once
try:
    requests = client.request_number(["Yahoo", "Google", "Amazon"])
    for r in requests:
        print(f"  {r['service']}: ID={r['id']}, status={r['status']}")
except GetSMSError as e:
    print(f"Error: {e}")


# Priority request: wait for MDN, then wait for SMS
# Use this when no numbers are immediately available
try:
    entry = client.wait_for_mdn("Google", state="CA")
    if entry:
        print(f"MDN assigned: {entry['mdn']}  (request ID: {entry['id']})")
        sms = client.wait_for_sms(entry["id"], timeout=900, poll_interval=15)
        if sms:
            print(f"SMS received: {sms['reply']}")
            print(f"PIN: {sms['pin']}")
        else:
            print("No SMS received within the timeout period.")
    else:
        print("No MDN was assigned within 30 minutes.")
except GetSMSError as e:
    print(f"Error: {e}")
