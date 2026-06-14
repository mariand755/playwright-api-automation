import pytest
from jsonschema import validate
from utils.helpers import get_schema


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
