import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

from backend.app.validation import ApproveEmailRequest, TripRequest


def _dates(days_out=30, length=6):
    out = dt.date.today() + dt.timedelta(days=days_out)
    ret = out + dt.timedelta(days=length)
    return out, ret


def test_valid_request():
    out, ret = _dates()
    r = TripRequest(origin="Madrid", destination="Paris", outbound_date=out, return_date=ret)
    assert r.adults == 1


def test_bad_date_order_rejected():
    out, ret = _dates()
    with pytest.raises(Exception):
        TripRequest(origin="Madrid", destination="Paris", outbound_date=ret, return_date=out)


def test_bad_location_rejected():
    out, ret = _dates()
    with pytest.raises(Exception):
        TripRequest(origin="https://evil.com/x", destination="Paris", outbound_date=out, return_date=ret)
    with pytest.raises(Exception):
        TripRequest(origin="M", destination="Paris", outbound_date=out, return_date=ret)


def test_passenger_limits():
    out, ret = _dates()
    with pytest.raises(Exception):
        TripRequest(origin="Madrid", destination="Paris", outbound_date=out, return_date=ret, adults=9, children=9)
    with pytest.raises(Exception):
        TripRequest(origin="Madrid", destination="Paris", outbound_date=out, return_date=ret, hotel_class=9)


def test_oversized_prompt_rejected():
    out, ret = _dates()
    with pytest.raises(Exception):
        TripRequest(origin="Madrid", destination="Paris", outbound_date=out, return_date=ret,
                    user_prompt="x" * 5000)


def test_approve_email_validation():
    with pytest.raises(Exception):
        ApproveEmailRequest(itinerary_id="abc", from_email="not-an-email", to_email="a@b.com", subject="hi")
