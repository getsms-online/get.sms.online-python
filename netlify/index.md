# Get SMS Online - API Reference

Use the [Get SMS Online](https://getsms.online) API to request temporary US phone numbers, receive SMS messages, and extract OTP verification codes programmatically.

Throughout this reference, **MDN** (mobile device number) refers to a phone number assigned to your request.

> [**Live API reference on GetSMS.Online:**](https://getsms.online/api_command_reference.php)

---

## Endpoint

All requests go to:

```
https://getsms.online/api_command.php
```

Parameters are passed as a **GET query string** or a **POST request**.

---

## Authentication

Every request must include:

| Parameter | Description |
|-----------|-------------|
| `user` | Your username or email address |
| `api_key` | Your API key |

Generate your API key at **Account → Profile** inside the members area. Email confirmation is required.

---

## Response format

All commands return JSON:

```json
{ "status": "ok",    "message": ... }
{ "status": "error", "message": "Error description" }
```

When `status` is `"ok"`, `message` holds the result data.  
When `status` is `"error"`, `message` describes what went wrong.

---

## One-time Numbers

### 1. Request a number

!!! note
    Each one-time number request accepts a single incoming SMS. To receive another message for the same number and service, submit a fresh request and pass the `mdn` parameter to reuse the same phone number.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cmd` | Y | `"request"` |
| `user` | Y | Your username or email |
| `api_key` | Y | Your API key |
| `service` | Y | Service name - from `list_services` or **Billing → Services and Rates** |
| `mdn` | N | Request a specific phone number. Returns an error if the number is in use or no longer available |
| `areacode` | N | Valid 3-digit US area code. Overrides `state`. Ignored when `mdn` is set |
| `state` | N | Valid 2-letter US state abbreviation. Ignored when `mdn` or `areacode` is set |
| `markup` | N | Priority bid, integer 10–2000. See [Priority requests](#priority-requests) |

**`message` array fields on success:**

| Field | Description |
|-------|-------------|
| `id` | Request ID |
| `mdn` | Assigned phone number (empty while status is `Awaiting MDN`) |
| `service` | Service name |
| `status` | `Reserved` or `Awaiting MDN` |
| `state` | State for geo-targeted requests |
| `markup` | Bid value |
| `price` | Price charged |
| `carrier` | Carrier name |
| `till_expiration` | Seconds until the request expires |

**Example:**
```
https://getsms.online/api_command.php?cmd=request&user=test&api_key=0123456789&service=Amazon
```

**Successful response:**
```json
{
  "status": "ok",
  "message": [
    {
      "id": "10000001",
      "mdn": "15302286946",
      "service": "Amazon",
      "status": "Reserved",
      "state": "",
      "markup": 0,
      "price": 0.50,
      "carrier": "TMobile",
      "till_expiration": 900
    }
  ]
}
```

**Error responses:**
```json
{ "status": "error", "message": "Invalid service name Goooooogle" }
{ "status": "error", "message": "No numbers available, retry later" }
```

#### Priority requests

Include the `markup` parameter (10–2000) to bid for a number when none are immediately available.

- The request is created with status `Awaiting MDN`; `mdn` is empty.
- When a number frees up and multiple users have placed bids, it goes to the highest bidder who bid earliest.
- Status changes to `Reserved` once a number is assigned.
- Unfulfilled priority requests are automatically deleted after 15 minutes.
- Track progress with `request_status`, or configure a [webhook URL](#webhook-url) to receive a `priority_request` event when your bid wins.
- **Tip:** query `list_services` with a single service name to get `recommended_markup` as a starting bid.

```json
{
  "status": "ok",
  "message": [
    {
      "id": "10000001",
      "mdn": "",
      "service": "Amazon",
      "status": "Awaiting MDN",
      "state": "CA",
      "markup": 25,
      "price": 0.60,
      "carrier": "",
      "till_expiration": 900
    }
  ]
}
```

#### Reusing a number

To reuse a virtual number previously reserved for the same service, pass the `mdn` parameter. Numbers rotate periodically and may no longer be available.

```
https://getsms.online/api_command.php?cmd=request&user=test&api_key=0123456789&service=Amazon&mdn=12345678901
```

**Error response:**
```json
{ "status": "error", "message": "The MDN is not available" }
```

---

#### Requesting the same temporary number for multiple services simultaneously

Pass up to 5 comma-separated service names in `service` to obtain one phone number that works for all of them at the same time. Priority bids are created automatically and markup is set high enough to win for each service.

!!! note
    Geo targeting can significantly reduce the pool of available numbers.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cmd` | Y | `"request"` |
| `user` | Y | Your username or email |
| `api_key` | Y | Your API key |
| `service` | Y | Up to 5 service names, comma-separated |
| `areacode` | N | Valid 3-digit US area code. Overrides `state` |
| `state` | N | Valid 2-letter US state abbreviation. Ignored when `areacode` is set |

**Example:**
```
https://getsms.online/api_command.php?cmd=request&user=test&api_key=0123456789&service=Yahoo,Google,Amazon
```

**Response:**
```json
{
  "status": "ok",
  "message": [
    {
      "id": "10000001",
      "mdn": "",
      "service": "Amazon",
      "status": "Awaiting MDN",
      "state": "",
      "markup": 10,
      "price": 0.30,
      "carrier": "",
      "till_expiration": 900
    },
    {
      "id": "10000002",
      "mdn": "",
      "service": "Google",
      "status": "Awaiting MDN",
      "state": "",
      "markup": 110,
      "price": 1.30,
      "carrier": "",
      "till_expiration": 900
    },
    {
      "id": "10000003",
      "mdn": "",
      "service": "Yahoo",
      "status": "Awaiting MDN",
      "state": "",
      "markup": 50,
      "price": 0.45,
      "carrier": "",
      "till_expiration": 900
    }
  ]
}
```

---

### 2. Get request status

Look up the current status of a request by its ID.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cmd` | Y | `"request_status"` |
| `user` | Y | Your username or email |
| `api_key` | Y | Your API key |
| `id` | Y | Request ID returned by the `request` command |

**Response** - `message` array entries contain: `id`, `mdn`, `service`, `status`, `state`, `markup`, `carrier`, `till_expiration`.

**Status values:**

| Value | Meaning |
|-------|---------|
| `Awaiting MDN` | Priority bid placed; no number assigned yet. `mdn` is empty |
| `Reserved` | Number assigned, waiting for SMS. `mdn` contains the number |
| `Completed` | SMS received. Retrieve it with `read_sms` |
| `Rejected` | Cancelled via `reject`, or no suitable number was found |
| `Timed Out` | No SMS arrived before expiry; request auto-cancelled |

!!! note
    Allow at least 15 seconds between consecutive `request_status` calls.

**Example:**
```
https://getsms.online/api_command.php?cmd=request_status&user=test&api_key=0123456789&id=10000001
```

**Example responses:**
```json
{
  "status": "ok",
  "message": [
    {
      "id": "10000001",
      "mdn": "",
      "service": "Amazon",
      "status": "Awaiting MDN",
      "state": "CA",
      "markup": 20,
      "carrier": "",
      "till_expiration": 300
    }
  ]
}
```
```json
{
  "status": "ok",
  "message": [
    {
      "id": "10000001",
      "mdn": "12345678901",
      "service": "Amazon",
      "status": "Reserved",
      "state": "CA",
      "markup": 20,
      "carrier": "ATT",
      "till_expiration": 890
    }
  ]
}
```

**Error response:**
```json
{ "status": "error", "message": "Invalid request ID" }
```

---

### 3. Reject a number

Reject a reserved mobile number — it will not be offered to you again.  
Can also cancel a priority bid in `Awaiting MDN` status.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cmd` | Y | `"reject"` |
| `user` | Y | Your username or email |
| `api_key` | Y | Your API key |
| `id` | Y | Request ID returned by the `request` command |

**Example:**
```
https://getsms.online/api_command.php?cmd=reject&user=test&api_key=0123456789&id=10000001
```

**Successful response:**
```json
{ "status": "ok", "message": "MDN has been rejected" }
```

**Error response:**
```json
{ "status": "error", "message": "Invalid request ID" }
```

---

### 4. Read SMS

Retrieve messages received to a phone number. Returns up to 3 of the most recent messages from the past 2 days, newest first.

!!! note
    When filtering by `id`, results appear only after the request reaches `Completed` status. Without `id`, messages from earlier completed requests may also be returned.  
    **Tip:** a [webhook URL](#webhook-url) is more efficient than polling.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cmd` | Y | `"read_sms"` |
| `user` | Y | Your username or email |
| `api_key` | Y | Your API key |
| `id` | N | Filter by request ID. When passed, `mdn` and `service` are ignored |
| `mdn` | N | Filter by phone number |
| `service` | N | Filter by service name |

**`message` array fields on success:**

| Field | Description |
|-------|-------------|
| `timestamp` | UNIX timestamp of receipt |
| `date_time` | Human-readable date/time (America/New_York) |
| `from` | Sender's number |
| `to` | Receiving number |
| `service` | Service name |
| `price` | Price charged |
| `reply` | Full SMS text |
| `pin` | Extracted PIN/OTP code (when recognized) |

**Example:**
```
https://getsms.online/api_command.php?cmd=read_sms&user=test&api_key=0123456789&service=Google
```

**Successful response:**
```json
{
  "status": "ok",
  "message": [
    {
      "timestamp": "1600108956",
      "date_time": "2020-09-14 14:42:36 EDT",
      "from": "22000",
      "to": "18503814729",
      "service": "Google",
      "price": 1.20,
      "reply": "G-804036 is your Google verification code.",
      "pin": "G-804036"
    },
    {
      "timestamp": "1600108852",
      "date_time": "2020-09-14 14:40:52 EDT",
      "from": "18339020112",
      "to": "15182193312",
      "service": "Google",
      "price": 1.20,
      "reply": "G-551858 is your Google verification code.",
      "pin": "G-551858"
    }
  ]
}
```

**Error response:**
```json
{ "status": "error", "message": "No messages" }
```

---

## Balance & Other Info

### 1. List services

Retrieve available services with pricing and availability data.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cmd` | Y | `"list_services"` |
| `user` | Y | Your username or email |
| `api_key` | Y | Your API key |
| `service` | N | One or more service names, comma-separated. Omit to return all services |

**`message` array fields on success:**

| Field | Description |
|-------|-------------|
| `name` | Service name |
| `price` | One-time SMS price |
| `otp_available` | Approximate count of available one-time numbers |
| `recommended_markup` | Suggested priority bid (only returned when querying a single service) |

!!! note
    Availability figures are approximate. Actual availability is confirmed only when you make a `request`.

**Example:**
```
https://getsms.online/api_command.php?cmd=list_services&user=test&api_key=0123456789&service=Google
```

**Successful response:**
```json
{
  "status": "ok",
  "message": [
    {
      "name": "Google",
      "price": "1.00",
      "otp_available": "74",
      "recommended_markup": "10"
    }
  ]
}
```

**Error response:**
```json
{ "status": "error", "message": "Invalid service name DummyService" }
```

---

### 2. View balance

| Parameter | Required | Description |
|-----------|----------|-------------|
| `cmd` | Y | `"balance"` |
| `user` | Y | Your username or email |
| `api_key` | Y | Your API key |

**Example:**
```
https://getsms.online/api_command.php?cmd=balance&user=test&api_key=0123456789
```

**Response:**
```json
{ "status": "ok", "message": "10.00" }
```

---

## Webhook URL

### Setup

Go to **Account → Profile** in the members area and enter your webhook URL.

- Data is delivered as an **HTTP POST** request.
- Your endpoint **must return HTTP 200**. Redirects are not followed.
- On failure the system retries up to 5 more times at 10-minute intervals.

---

### Incoming message

Triggered when an SMS arrives at one of your numbers.

| Field | Value |
|-------|-------|
| `event` | `"incoming_message"` |
| `id` | Request ID from the `request` command |
| `timestamp` | UNIX timestamp |
| `date_time` | Human-readable date/time (America/New_York) |
| `from` | Sender's number |
| `to` | Receiving number |
| `service` | Service name |
| `reply` | SMS text |
| `pin` | Extracted PIN/OTP code (when recognized) |
| `price` | Price charged |

---

### Priority request won

Triggered when your priority bid wins and a number is assigned.

| Field | Value |
|-------|-------|
| `event` | `"priority_request"` |
| `status` | `"ok"` |
| `id` | Request ID |
| `mdn` | Assigned phone number |
| `service` | Service name |
| `price` | Price charged |

---

## Python SDK

A Python client for the Get SMS Online API is [available on GitHub](https://github.com/getsms-online/get.sms.online-python).

Install with pip:

```
pip install get-sms-online
```

---

## Links

- [Get SMS Online](https://getsms.online) - receive SMS online, temporary US phone numbers for SMS verification
- [Live API reference](https://getsms.online/api_command_reference.php)
- [Python SDK on GitHub](https://github.com/getsms-online/get.sms.online-python)
