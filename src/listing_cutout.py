import argparse
import base64
import json
from dataclasses import dataclass

from infrai_client import InfraiClient


@dataclass(frozen=True)
class CutoutDelivery:
    listing_id: str
    object_key: str
    object_result: object


def process_listing(client: InfraiClient, bucket: str, listing_id: str, filename: str, image_base64: str) -> CutoutDelivery:
    request_id = f"listing-{listing_id}"
    client.create_bucket(bucket)
    uploaded = client.upload_image(image_base64, filename)
    image_ref = uploaded.get("id") if isinstance(uploaded, dict) else uploaded
    cutout = client.remove_background(str(image_ref), "png")
    cutout_data = cutout.get("data_base64") if isinstance(cutout, dict) else cutout
    object_key = f"listings/{listing_id}/cutout.png"
    stored = client.put_object(bucket, object_key, str(cutout_data), request_id)
    return CutoutDelivery(listing_id, object_key, stored)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deliver a transparent listing cutout")
    parser.add_argument("--listing", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--image-base64", required=True)
    args = parser.parse_args()
    client = InfraiClient()
    bucket = __import__("os").environ.get("INFRAI_BUCKET", "media-listings")
    result = process_listing(client, bucket, args.listing, args.filename, args.image_base64)
    print(json.dumps({"listing_id": result.listing_id, "object_key": result.object_key, "stored": result.object_result}))


if __name__ == "__main__":
    main()
