import pytest
from jsonschema import validate
from utils.helpers import get_schema


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
    assert get_response.status_code == 200, (
        f"GET /booking/{booking_id} after rejected PATCH expected 200: "
        f"status={get_response.status_code}, body={get_response.text[:200]}"
    )
    body = get_response.json()
    assert body["firstname"] == original_firstname, (
        f"Booking was modified by unauthorized PATCH: "
        f"expected firstname={original_firstname!r}, "
        f"got {body.get('firstname')!r}"
    )
