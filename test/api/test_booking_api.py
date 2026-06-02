import pytest
from jsonschema import validate
from utils.helpers import get_schema


# TC-API-001
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.api_contract
@pytest.mark.tc_id("TC-API-001")
def test_get_all_bookings(booking_api):
    response = booking_api.get_all_bookings()

    assert response.status_code == 200, (
        f"GET {response.url} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    bookings = response.json()
    assert isinstance(bookings, list), (
        f"Expected a list of bookings, got {type(bookings).__name__}"
    )
    if bookings:
        schema = get_schema("booking_list_item_schema.json")
        validate(instance=bookings[0], schema=schema)


# TC-API-002
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.api_contract
@pytest.mark.tc_id("TC-API-002")
def test_get_booking_by_id(booking_api, created_booking):
    booking_id = created_booking["bookingid"]
    response = booking_api.get_booking_by_id(booking_id)

    assert response.status_code == 200, (
        f"GET {response.url} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    schema = get_schema("booking_details_schema.json")
    response_json = response.json()

    validate(instance=response_json, schema=schema)
    assert response_json["firstname"] == created_booking["booking"]["firstname"], (
        f"Round-trip check failed: expected firstname={created_booking['booking']['firstname']!r}, "
        f"got {response_json.get('firstname')!r}"
    )


# TC-API-003
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-API-003")
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
@pytest.mark.smoke
@pytest.mark.api_contract
@pytest.mark.tc_id("TC-API-004")
def test_create_booking(booking_api, auth_token, booking_payload_factory, request):
    payload = booking_payload_factory(
        firstname="John",
        lastname="Doe",
        totalprice=100,
        depositpaid=True,
        checkin="2024-01-01",
        checkout="2024-01-05",
        additionalneeds="Breakfast",
    )

    response = booking_api.create_booking(payload)

    assert response.status_code == 200, (
        f"POST {response.url} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    booking_id = response.json()["bookingid"]

    def _cleanup():
        delete_response = booking_api.delete_booking(booking_id, auth_token)
        if delete_response.status_code not in (201, 404):
            raise RuntimeError(
                f"Test teardown failed: delete booking {booking_id} "
                f"returned status={delete_response.status_code}, body={delete_response.text[:200]}"
            )

    request.addfinalizer(_cleanup)

    schema = get_schema("booking_schema.json")
    response_json = response.json()

    validate(instance=response_json, schema=schema)
    assert response_json["booking"]["firstname"] == payload["firstname"], (
        f"Round-trip check failed: expected firstname={payload['firstname']!r}, "
        f"got {response_json['booking'].get('firstname')!r}"
    )


# TC-API-005
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.tc_id("TC-API-005")
def test_delete_booking(booking_api, auth_token, booking_payload_factory):
    payload = booking_payload_factory(
        firstname="ToDelete",
        lastname="User",
        totalprice=50,
        checkin="2024-06-01",
        checkout="2024-06-02",
    )

    create_response = booking_api.create_booking(payload)
    assert create_response.status_code == 200, (
        f"POST {create_response.url} failed: "
        f"status={create_response.status_code}, body={create_response.text[:200]}"
    )
    booking_id = create_response.json()["bookingid"]

    delete_response = booking_api.delete_booking(booking_id, auth_token)
    # Restful Booker returns 201 for a successful DELETE — non-standard but documented API behaviour.
    assert delete_response.status_code == 201, (
        f"DELETE /booking/{booking_id} expected 201: "
        f"status={delete_response.status_code}, body={delete_response.text[:200]}"
    )

    verify_response = booking_api.get_booking_by_id(booking_id)
    assert verify_response.status_code == 404, (
        f"GET /booking/{booking_id} after delete expected 404: "
        f"status={verify_response.status_code}, body={verify_response.text[:200]}"
    )
