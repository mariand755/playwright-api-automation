import requests

from utils.timeouts import API_REQUEST_TIMEOUT_SECONDS


class BookingApiClient:
    def __init__(self, base_url: str, timeout: int = API_REQUEST_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_all_bookings(self):
        return requests.get(f"{self.base_url}/booking", timeout=self.timeout)

    def get_booking_by_id(self, booking_id: int):
        return requests.get(
            f"{self.base_url}/booking/{booking_id}", timeout=self.timeout
        )

    def create_booking(self, payload: dict):
        return requests.post(
            f"{self.base_url}/booking", json=payload, timeout=self.timeout
        )

    def create_token(self, username: str, password: str) -> str:
        response = requests.post(
            f"{self.base_url}/auth",
            json={"username": username, "password": password},
            timeout=self.timeout,
        )
        token = response.json().get("token")
        if not token:
            raise ValueError(
                f"POST /auth did not return a token: "
                f"status={response.status_code}, body={response.text[:200]}"
            )
        return token

    def delete_booking(self, booking_id: int, token: str):
        return requests.delete(
            f"{self.base_url}/booking/{booking_id}",
            headers={"Cookie": f"token={token}"},
            timeout=self.timeout,
        )
