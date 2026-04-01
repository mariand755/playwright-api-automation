import requests

from utils.timeouts import API_REQUEST_TIMEOUT_SECONDS


class BookingApiClient:
    def __init__(self, base_url: str, timeout: int = API_REQUEST_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_all_bookings(self):
        return requests.get(f"{self.base_url}/booking", timeout=self.timeout)

    def get_booking_by_id(self, booking_id: int):
        return requests.get(f"{self.base_url}/booking/{booking_id}", timeout=self.timeout)

    def create_booking(self, payload: dict):
        return requests.post(f"{self.base_url}/booking", json=payload, timeout=self.timeout)
