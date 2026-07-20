# Get SMS Online - Python SDK

Python client for the [Get SMS Online](https://getsms.online) API. Receive SMS online and get one-time verification codes programmatically for WhatsApp, Telegram, Google, and 700+ other services.

Use this library to automate phone number verification with temporary phone numbers - no SIM card required.  
Ideal for receiving OTP codes, bypassing SMS verification, and managing virtual phone numbers at scale.

> **Compatible with both [getsms.online](https://getsms.online) and [tellabot.com](https://www.tellabot.com) - the API is identical.**  

[![PyPI version](https://img.shields.io/pypi/v/get-sms-online.svg)](https://pypi.org/project/get-sms-online/)
[![Downloads](https://pepy.tech/badge/get-sms-online)](https://pepy.tech/project/get-sms-online)

## Installation

```bash
pip install get-sms-online
```

```bash
pip install git+https://github.com/getsms-online/get.sms.online-python.git
```

## Quick start

```python
from getsms import GetSMSClient, GetSMSError

client = GetSMSClient(user="your_username", api_key="your_api_key")

# Check balance
print(client.balance())   # e.g. 10.0

# Request a number and wait for the SMS
requests = client.request_number("WhatsApp")
req = requests[0]
print(f"Your number: {req['mdn']}")

sms = client.wait_for_sms(req["id"], timeout=900)
if sms:
    print(f"Code: {sms['pin']}")
```

## API key

Generate your API key at **Account → Profile** inside the members area at [getsms.online](https://getsms.online).

## Reference

### `GetSMSClient(user, api_key)`

All methods raise `GetSMSError` on API errors.

---

#### `request_number(service, mdn=None, areacode=None, state=None, markup=None)`

Request a phone number for one or more services.

| Parameter | Type | Description |
|-----------|------|-------------|
| `service` | str or list | Service name(s), e.g. `"WhatsApp"` or `["Google", "Yahoo"]` |
| `mdn` | str | Request a specific number (optional) |
| `areacode` | str | 3-digit US area code (optional) |
| `state` | str | 2-letter US state, e.g. `"CA"` (optional) |
| `markup` | int | Priority bid 10–2000 (optional) |

Returns a list of request dicts: `id`, `mdn`, `service`, `status`, `state`, `markup`, `price`, `carrier`, `till_expiration`.

```python
# Single service
result = client.request_number("WhatsApp")

# Specific area code
result = client.request_number("Google", areacode="415")

# Multiple services at once (priority request)
result = client.request_number(["Google", "Amazon", "Yahoo"])
```

---

#### `request_status(request_id)`

Get the current status of a request.

Possible status values: `Reserved`, `Awaiting MDN`, `Completed`, `Rejected`, `Timed Out`.

```python
info = client.request_status("10000001")
print(info[0]["status"])   # "Reserved"
print(info[0]["mdn"])      # "15302286946"
```

---

#### `reject(request_id)`

Reject a reserved number or cancel a priority bid.

```python
client.reject("10000001")
```

---

#### `read_sms(request_id=None, mdn=None, service=None)`

Read the latest SMS messages (up to 3, from the past 2 days).  
**Tip:** use a [webhook](#webhook) instead of polling.

```python
messages = client.read_sms(request_id="10000001")
for msg in messages:
    print(msg["reply"], msg["pin"])
```

---

#### `list_services(service=None)`

List available services and prices.

```python
# All services
all_services = client.list_services()

# One or more specific services
info = client.list_services("Google")
info = client.list_services(["Google", "WhatsApp"])
```

Returns: `name`, `price`, `ltr_price`, `ltr_short_price`, `otp_available`, `ltr_available`, `recommended_markup`.

---

#### `balance()`

Returns your current balance as a `float`.

```python
print(client.balance())   # 10.0
```

---

#### `wait_for_mdn(service, areacode=None, state=None, timeout=1800, poll_interval=15)`

Convenience helper for priority requests - use when no numbers are immediately available.

1. Fetches `recommended_markup` for the service via `list_services`
2. Adds 2% and submits a priority request with that markup
3. Polls `request_status` every 15 seconds until a number is assigned (`Reserved`) or the request expires

After it returns, pass `entry["id"]` to `wait_for_sms` to wait for the SMS.

```python
entry = client.wait_for_mdn("Google", state="CA")
if entry:
    print(f"Number assigned: {entry['mdn']}")
    sms = client.wait_for_sms(entry["id"])
    if sms:
        print(sms["pin"])
```

Returns a request dict with the assigned MDN, or `None` if timed out / rejected.

---

#### `wait_for_sms(request_id, timeout=900, poll_interval=15)`

Convenience helper - polls `request_status` until an SMS arrives or the request expires.  
The number is cancelled automatically by the server on timeout - no manual rejection needed.  
`poll_interval` is enforced to a minimum of 15 seconds.

```python
sms = client.wait_for_sms("10000001", timeout=900, poll_interval=15)
if sms:
    print(sms["pin"])
```

Returns the first SMS message dict, or `None` if the request timed out or was rejected.

---

## Webhook

Instead of polling `read_sms`, configure a webhook URL at **Account → Profile**.  
Your endpoint will receive POST requests with the following fields:

**Incoming message:**

| Field | Value |
|-------|-------|
| `event` | `"incoming_message"` |
| `id` | Request ID |
| `timestamp` | UNIX timestamp |
| `date_time` | Human-readable (America/New_York) |
| `from` | Sending number |
| `to` | Receiving number |
| `service` | Service name |
| `reply` | SMS text |
| `pin` | Extracted PIN code |
| `price` | Price |

**Priority request won:**

| Field | Value |
|-------|-------|
| `event` | `"priority_request"` |
| `status` | `"ok"` |
| `id` | Request ID |
| `mdn` | Assigned number |
| `service` | Service name |
| `price` | Price |

Your webhook endpoint must return **HTTP 200**. On failure the system retries 5 times at 10-minute intervals.

---

## Error handling

```python
from getsms import GetSMSClient, GetSMSError

client = GetSMSClient("user", "key")

try:
    result = client.request_number("WhatsApp")
except GetSMSError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Network error: {e}")
```

## Links

- [Get SMS Online](https://getsms.online) - receive SMS online, temporary phone numbers for SMS verification
- [API Command Reference](https://getsms.online/api_command_reference.php) - full API documentation
- [Tell A Bot](https://www.tellabot.com) - also compatible with Tell A Bot

## License

MIT
