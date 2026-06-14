import pytest
from jsonschema import validate
from utils.helpers import get_schema


# TC-API-001
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.read_only
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


# TC-API-011
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.api_contract
@pytest.mark.tc_id("TC-API-011")
def test_get_bookings_filtered_by_firstname(booking_api, created_booking):
    expected_firstname = created_booking["booking"]["firstname"]
    booking_id = created_booking["bookingid"]

    response = booking_api.get_all_bookings(params={"firstname": expected_firstname})

    assert response.status_code == 200, (
        f"GET /booking?firstname={expected_firstname} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    results = response.json()
    assert isinstance(results, list), (
        f"Expected a list from filtered GET /booking, got {type(results).__name__}"
    )
    returned_ids = {b["bookingid"] for b in results}
    assert booking_id in returned_ids, (
        f"Created booking ID {booking_id} not found in filtered results "
        f"for firstname={expected_firstname!r}: {returned_ids}"
    )

    detail = booking_api.get_booking_by_id(booking_id)
    assert detail.status_code == 200, (
        f"GET /booking/{booking_id} expected 200: "
        f"status={detail.status_code}, body={detail.text[:200]}"
    )
    assert detail.json()["firstname"] == expected_firstname
