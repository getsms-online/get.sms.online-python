import time
import requests


class GetSMSError(Exception):
    pass


class GetSMSClient:
    """
    Python client for the Get SMS Online API (https://getsms.online).
    Also compatible with Tell A Bot (https://www.tellabot.com) — the API is identical.
    Full API reference: https://getsms.online/api_command_reference.php
    """

    BASE_URL = "https://getsms.online/api_command.php"

    def __init__(self, user, api_key):
        """
        :param user:    Your username or email
        :param api_key: Your API key (generate at Account -> Profile)
        """
        self.user = user
        self.api_key = api_key

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _call(self, params):
        params["user"] = self.user
        params["api_key"] = self.api_key
        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "error":
            raise GetSMSError(data.get("message", "Unknown error"))
        return data["message"]

    # ------------------------------------------------------------------ #
    #  One-time MDNs                                                       #
    # ------------------------------------------------------------------ #

    def request_number(self, service, mdn=None, areacode=None, state=None, markup=None):
        """
        Request one or more phone numbers.

        :param service:  Service name(s) — string or list of up to 5 names.
                         Example: "WhatsApp"  or  ["Yahoo", "Google", "Amazon"]
        :param mdn:      Request a specific MDN (optional).
        :param areacode: 3-digit US area code (optional).
        :param state:    2-letter US state abbreviation (optional).
        :param markup:   Priority bid value 10-2000 (optional).
        :return: List of request dicts with keys:
                 id, mdn, service, status, state, markup, price, carrier, till_expiration
        """
        if isinstance(service, (list, tuple)):
            service = ",".join(service)
        params = {"cmd": "request", "service": service}
        if mdn is not None:
            params["mdn"] = mdn
        if areacode is not None:
            params["areacode"] = areacode
        if state is not None:
            params["state"] = state
        if markup is not None:
            params["markup"] = markup
        return self._call(params)

    def request_status(self, request_id):
        """
        Get the current status of a request.

        :param request_id: ID returned by request_number()
        :return: List with one request dict.
                 status values: "Reserved", "Awaiting MDN", "Completed", "Rejected", "Timed Out"
        """
        return self._call({"cmd": "request_status", "id": request_id})

    def reject(self, request_id):
        """
        Reject a reserved MDN or cancel a priority bid.

        :param request_id: ID returned by request_number()
        :return: Confirmation message string
        """
        return self._call({"cmd": "reject", "id": request_id})

    def read_sms(self, request_id=None, mdn=None, service=None):
        """
        Read SMS messages (up to 3 latest from the past 2 days).
        Consider using a webhook instead of polling.

        :param request_id: Filter by request ID (optional)
        :param mdn:        Filter by phone number (optional)
        :param service:    Filter by service name (optional)
        :return: List of message dicts with keys:
                 timestamp, date_time, from, to, service, price, reply, pin
        """
        params = {"cmd": "read_sms"}
        if request_id is not None:
            params["id"] = request_id
        if mdn is not None:
            params["mdn"] = mdn
        if service is not None:
            params["service"] = service
        return self._call(params)

    # ------------------------------------------------------------------ #
    #  Balance & Info                                                      #
    # ------------------------------------------------------------------ #

    def list_services(self, service=None):
        """
        List available services and their prices.

        :param service: One or more service names to filter (string or list). Optional.
        :return: List of service dicts with keys:
                 name, price, ltr_price, ltr_short_price, otp_available,
                 ltr_available, recommended_markup
        """
        params = {"cmd": "list_services"}
        if service is not None:
            if isinstance(service, (list, tuple)):
                service = ",".join(service)
            params["service"] = service
        return self._call(params)

    def balance(self):
        """
        Get your current account balance.

        :return: Balance as a float
        """
        return float(self._call({"cmd": "balance"}))

    # ------------------------------------------------------------------ #
    #  Convenience helpers                                                 #
    # ------------------------------------------------------------------ #

    def wait_for_mdn(self, service, areacode=None, state=None, timeout=1800, poll_interval=15):
        """
        Place a priority request and wait until a phone number (MDN) is assigned.

        Fetches recommended_markup for the service, adds 2%, and submits a priority
        request. Then polls request_status every poll_interval seconds until the status
        changes to "Reserved" (MDN assigned) or a terminal state is reached.

        After this returns successfully, call wait_for_sms(entry["id"]) to wait for the SMS.

        :param service:       Service name (single string)
        :param areacode:      3-digit US area code (optional)
        :param state:         2-letter US state abbreviation (optional)
        :param timeout:       Maximum seconds to wait (default: 1800 = 30 minutes)
        :param poll_interval: Seconds between status checks (default: 15)
        :return: Request dict with MDN assigned (keys: id, mdn, service, status, ...),
                 or None if timed out / rejected
        :raises GetSMSError: On API errors
        """
        poll_interval = max(15, poll_interval)

        # Get recommended_markup for the service and add 2%
        services = self.list_services(service)
        if not services:
            raise GetSMSError(f"Service '{service}' not found")
        recommended = int(services[0].get("recommended_markup", 10))
        markup = min(recommended + 2, 2000)

        # Place priority request
        result = self.request_number(service, areacode=areacode, state=state, markup=markup)
        if not result:
            return None
        request_id = result[0]["id"]

        # Poll until MDN is assigned or terminal state
        deadline = time.time() + timeout
        while time.time() < deadline:
            info = self.request_status(request_id)
            if not info:
                return None
            entry = info[0]
            status = entry.get("status")
            if status in ("Timed Out", "Rejected"):
                return None
            if status == "Reserved" and entry.get("mdn"):
                return entry
            # "Awaiting MDN" — keep waiting
            time.sleep(poll_interval)
        return None

    def wait_for_sms(self, request_id, timeout=900, poll_interval=15):
        """
        Poll request_status until an SMS arrives or the request expires.
        The number is cancelled automatically by the server on timeout — no need to reject it manually.

        :param request_id:    ID returned by request_number()
        :param timeout:       Maximum seconds to wait (default: 900 = 15 minutes)
        :param poll_interval: Seconds between status checks (default: 15, minimum recommended)
        :return: First SMS message dict, or None if timed out / rejected
        :raises GetSMSError: On API errors
        """
        poll_interval = max(15, poll_interval)
        deadline = time.time() + timeout
        while time.time() < deadline:
            info = self.request_status(request_id)
            if not info:
                return None
            entry = info[0]
            status = entry.get("status")
            if status in ("Timed Out", "Rejected"):
                # Terminal states — server already cancelled the request
                return None
            if status == "Completed":
                # SMS has arrived — read_sms is only meaningful at this point
                messages = self.read_sms(request_id=request_id)
                return messages[0] if messages else None
            # "Awaiting MDN" (no number yet) or "Reserved" (number assigned, waiting for SMS)
            time.sleep(poll_interval)
        return None
