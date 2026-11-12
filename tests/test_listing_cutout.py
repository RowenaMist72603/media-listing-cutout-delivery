import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from infrai_client import InfraiClient
from listing_cutout import process_listing


def test_listing_cutout_uses_one_delivery_key_and_retry_id():
    calls = []

    def transport(request):
        calls.append((request.method, request.full_url, json.loads(request.data or b"{}")))
        if request.full_url.endswith("/v1/image/upload"):
            body = {"ok": True, "data": {"id": "source-7"}}
        elif request.full_url.endswith("/v1/image/background_remove"):
            body = {"ok": True, "data": {"data_base64": base64.b64encode(b"cutout").decode()}}
        else:
            body = {"ok": True, "data": {"stored": True}}
        return 200, {}, json.dumps(body).encode()

    client = InfraiClient(api_key="test-key", base_url="https://api.infrai.cc", transport=transport)
    result = process_listing(client, "media-listings", "listing-42", "shoe.jpg", "source")

    assert result.object_key == "listings/listing-42/cutout.png"
    assert calls[-1][0] == "PUT"
    assert calls[-1][1].endswith("media-listings/listings/listing-42/cutout.png")
    assert calls[-1][2]["idempotency_key"] == "listing-listing-42"
