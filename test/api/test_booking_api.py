import pytest
from jsonschema import validate
from utils.helpers import get_schema


# TC-API-001
@pytest.mark.api
def test_get_all_bookings(booking_api):
    response = booking_api.get_all_bookings()

    assert response.status_code == 200, (
        f"GET {response.url} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    # Validate that the response is a list of bookings, which should be the expected format for this endpoint.
    assert isinstance(response.json(), list)


# TC-API-002
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
    assert create_response.status_code == 200, (
        f"POST {create_response.url} failed: "
        f"status={create_response.status_code}, body={create_response.text[:200]}"
    )

    # Extract the booking ID from the create response to use in the get request.
    booking_id = create_response.json()["bookingid"]
    response = booking_api.get_booking_by_id(booking_id)

    assert response.status_code == 200, (
        f"GET {response.url} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    schema = get_schema("booking_details_schema.json")
    response_json = response.json()

    # Validate the response against the schema to ensure it has the expected structure and data types.
    validate(instance=response_json, schema=schema)
    assert response_json["firstname"] == payload["firstname"], (
        f"Round-trip check failed: expected firstname={payload['firstname']!r}, "
        f"got {response_json.get('firstname')!r}"
    )


# TC-API-003
@pytest.mark.api
@pytest.mark.negative
def test_invalid_booking(booking_api):
    invalid_id = 999999999

    # Attempt to retrieve a booking with an ID that does not exist, expecting a 404 Not Found or 400 Bad Request response.
    response = booking_api.get_booking_by_id(invalid_id)

    assert response.status_code in [404, 400], (
        f"GET {response.url} expected 404 or 400 for invalid booking ID: "
        f"status={response.status_code}, body={response.text[:200]}"
    )


# TC-API-004
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

    assert response.status_code == 200, (
        f"POST {response.url} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    schema = get_schema("booking_schema.json")
    response_json = response.json()

    validate(instance=response_json, schema=schema)
    # Verify that the created booking's firstname matches the payload.
    assert response_json["booking"]["firstname"] == payload["firstname"]
