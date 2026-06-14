import pytest


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
