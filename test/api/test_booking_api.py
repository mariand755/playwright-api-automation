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


# TC-API-006
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.api_contract
@pytest.mark.tc_id("TC-API-006")
def test_update_booking(
    booking_api, created_booking, auth_token, booking_payload_factory
):
    booking_id = created_booking["bookingid"]
    update_payload = booking_payload_factory(
        firstname="Updated",
        lastname="User",
        totalprice=200,
        depositpaid=True,
        checkin="2025-03-01",
        checkout="2025-03-07",
    )

    response = booking_api.update_booking(booking_id, update_payload, auth_token)

    assert response.status_code == 200, (
        f"PUT /booking/{booking_id} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    schema = get_schema("booking_details_schema.json")
    response_json = response.json()

    validate(instance=response_json, schema=schema)
    assert response_json["firstname"] == update_payload["firstname"]
    assert response_json["lastname"] == update_payload["lastname"]
    assert response_json["totalprice"] == update_payload["totalprice"]
    assert response_json["depositpaid"] == update_payload["depositpaid"]
    assert (
        response_json["bookingdates"]["checkin"]
        == update_payload["bookingdates"]["checkin"]
    )
    assert (
        response_json["bookingdates"]["checkout"]
        == update_payload["bookingdates"]["checkout"]
    )


# TC-API-007
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-API-007")
def test_update_booking_without_auth(
    booking_api, created_booking, booking_payload_factory
):
    booking_id = created_booking["bookingid"]
    update_payload = booking_payload_factory(
        firstname="ShouldNotUpdate",
        lastname="User",
        totalprice=999,
    )

    response = booking_api.update_booking(booking_id, update_payload, "invalid_token")

    assert response.status_code in {401, 403}, (
        f"PUT /booking/{booking_id} with invalid token expected 401 or 403: "
        f"status={response.status_code}, body={response.text[:200]}"
    )

    get_response = booking_api.get_booking_by_id(booking_id)
    assert get_response.status_code == 200, (
        f"GET /booking/{booking_id} after rejected PUT failed: "
        f"status={get_response.status_code}, body={get_response.text[:200]}"
    )
    body = get_response.json()
    assert body["firstname"] == created_booking["booking"]["firstname"], (
        f"Booking was modified by unauthorized PUT: "
        f"expected firstname={created_booking['booking']['firstname']!r}, "
        f"got {body.get('firstname')!r}"
    )
    assert body["lastname"] == created_booking["booking"]["lastname"]
    assert body["totalprice"] == created_booking["booking"]["totalprice"]


# TC-API-008
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-API-008")
def test_create_booking_missing_required_field(booking_api):
    payload = {
        # firstname intentionally omitted — required field
        "lastname": "MissingFirst",
        "totalprice": 100,
        "depositpaid": False,
        "bookingdates": {"checkin": "2024-01-01", "checkout": "2024-01-02"},
    }

    response = booking_api.create_booking(payload)

    # Restful Booker returns 400 or 500 for malformed payloads; both indicate rejection.
    assert response.status_code in {400, 500}, (
        f"POST {response.url} with missing 'firstname' expected 400 or 500: "
        f"status={response.status_code}, body={response.text[:200]}"
    )


# TC-API-009
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-API-009")
def test_delete_booking_without_auth(booking_api, created_booking):
    booking_id = created_booking["bookingid"]

    response = booking_api.delete_booking(booking_id, "invalid_token")

    assert response.status_code in {401, 403}, (
        f"DELETE /booking/{booking_id} with invalid token expected 401 or 403: "
        f"status={response.status_code}, body={response.text[:200]}"
    )

    get_response = booking_api.get_booking_by_id(booking_id)
    assert get_response.status_code == 200, (
        f"GET /booking/{booking_id} after rejected DELETE expected 200: "
        f"status={get_response.status_code}, body={get_response.text[:200]}"
    )
    body = get_response.json()
    assert body["firstname"] == created_booking["booking"]["firstname"], (
        f"Booking was modified by unauthorized DELETE: "
        f"expected firstname={created_booking['booking']['firstname']!r}, "
        f"got {body.get('firstname')!r}"
    )


# TC-API-010
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-API-010")
def test_create_token_with_invalid_credentials(booking_api):
    with pytest.raises(ValueError):
        booking_api.create_token("wrong_user", "wrong_pass")


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


# TC-API-012
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.tc_id("TC-API-012")
def test_patch_booking_updates_single_field(booking_api, created_booking, auth_token):
    booking_id = created_booking["bookingid"]
    original = created_booking["booking"]

    response = booking_api.patch_booking(
        booking_id, {"firstname": "Patched"}, auth_token
    )

    assert response.status_code == 200, (
        f"PATCH /booking/{booking_id} failed: "
        f"status={response.status_code}, body={response.text[:200]}"
    )
    body = response.json()
    assert body["firstname"] == "Patched", (
        f"Expected firstname='Patched', got {body.get('firstname')!r}"
    )
    assert body["lastname"] == original["lastname"]
    assert body["totalprice"] == original["totalprice"]
    assert body["depositpaid"] == original["depositpaid"]

    detail = booking_api.get_booking_by_id(booking_id)
    assert detail.status_code == 200, (
        f"GET /booking/{booking_id} after PATCH expected 200: "
        f"status={detail.status_code}, body={detail.text[:200]}"
    )
    assert detail.json()["firstname"] == "Patched"


# TC-API-013
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-API-013")
def test_patch_booking_without_auth(booking_api, created_booking):
    booking_id = created_booking["bookingid"]
    original_firstname = created_booking["booking"]["firstname"]

    response = booking_api.patch_booking(
        booking_id, {"firstname": "ShouldNotPatch"}, "invalid_token"
    )

    assert response.status_code in {401, 403}, (
        f"PATCH /booking/{booking_id} with invalid token expected 401 or 403: "
        f"status={response.status_code}, body={response.text[:200]}"
    )

    get_response = booking_api.get_booking_by_id(booking_id)
    assert get_response.status_code == 200
    assert get_response.json()["firstname"] == original_firstname, (
        f"Booking was modified by unauthorized PATCH: "
        f"expected firstname={original_firstname!r}, "
        f"got {get_response.json().get('firstname')!r}"
    )
