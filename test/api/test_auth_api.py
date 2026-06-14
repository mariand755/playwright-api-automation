import pytest


# TC-API-010
@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-API-010")
def test_create_token_with_invalid_credentials(booking_api):
    with pytest.raises(ValueError):
        booking_api.create_token("wrong_user", "wrong_pass")
