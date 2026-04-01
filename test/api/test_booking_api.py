import pytest
from jsonschema import validate
from utils.helpers import get_schema


@pytest.mark.api
def test_get_all_bookings(booking_api):
    response = booking_api.get_all_bookings()

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.api
def test_get_booking_by_id(booking_api):
    payload = {
        "firstname": "Deterministic",
        "lastname": "User",
        "totalprice": 125,
        "depositpaid": False,
        "bookingdates": {
            "checkin": "2024-05-01",
            "checkout": "2024-05-03",
        },
        "additionalneeds": "Late Checkout",
    }

    create_response = booking_api.create_booking(payload)
    assert create_response.status_code == 200
    booking_id = create_response.json()["bookingid"]

    response = booking_api.get_booking_by_id(booking_id)

    assert response.status_code == 200
    schema = get_schema("booking_details_schema.json")

    validate(instance=response.json(), schema=schema)


@pytest.mark.api
def test_invalid_booking(booking_api):
    all_bookings = booking_api.get_all_bookings().json()
    existing_ids = [item["bookingid"] for item in all_bookings]
    invalid_id = max(existing_ids) + 999999

    response = booking_api.get_booking_by_id(invalid_id)

    assert response.status_code in [404, 400]


@pytest.mark.api
def test_create_booking(booking_api):

    payload = {
        "firstname": "John",
        "lastname": "Doe",
        "totalprice": 100,
        "depositpaid": True,
        "bookingdates": {
            "checkin": "2024-01-01",
            "checkout": "2024-01-05"
        }, 
        "additionalneeds": "Breakfast",
    }

    response = booking_api.create_booking(payload)

    assert response.status_code == 200
    schema = get_schema("booking_schema.json")
    response_json = response.json()

    validate(instance=response_json, schema=schema)
    assert response_json["booking"]["firstname"] == payload["firstname"]
