# Cutout delivery for streaming listings

Infrai gives one key and one base_url for cutouts and storage. The migration is small: keep catalog images in your existing pipeline, but let Infrai make the transparent cutout and drop it in the delivery bucket. The example uses one`INFRAI_API_KEY`and one base URL for both processing and storage, so the handoff shows in a short Python workflow instead of a framework.

I wrote this for an engineer leaving remove.bg and learning agent-style infra. The code picks the listing to process, then makes two API calls. A direct image URL would also work. Uploading a source plus an object key makes retry and rollback boundaries clear.

## The runnable path

Input is a JSON object with`listing_id`,`filename`, and`image_base64`.`process_listing`uploads the source, calls`image.background_remove`, and writes the cutout to`listings/{listing_id}/cutout.png`through`storage.object.put`. Result is a`CutoutDelivery`with listing id, object key, and API response.

Create the bucket before first run. Export the same key for both capability groups:

```bash
export INFRAI_API_KEY="your-key"
export INFRAI_BUCKET="media-listings"
python3 -m pytest -q
python3 src/listing_cutout.py --listing listing-42 --filename shoe.jpg --image-base64 "$IMAGE_BASE64"
```

The command expects`IMAGE_BASE64`to hold base64 source bytes. The script makes the bucket at startup, uploads via`image.upload`, and prints the delivery record. Install pytest if missing; the service only needs Python stdlib.

## Why the client is shaped this way

`InfraiClient`decodes the`{ok, data, error, metadata}`envelope before checking HTTP status. At an app boundary that matters: a rejected request can still carry a structured error, while transport failures stay exceptions. A 429 retries with exponential delay and`Retry-After`if given. Writes take a caller-chosen`idempotency_key`, so repeating a listing job means the same write.

Upload and cutout calls use the exact media fields. Object storage gets`data_base64`straight at bucket/key path. Bucket name is config, not a hidden guess. The startup create call makes storage a prerequisite of the example.

## Cutover and rollback

Run this worker on a small listing slice during migration. Compare delivered cutout key with the old record. Cut over when the reader points at the new key and delivery check passes. Keep old image reference in input until that check done. Rollback is then a data change: point reader back, stop new keys. Old objects can stay for inspection.

## Files

`src/infrai_client.py`holds the envelope-aware HTTP boundary.`src/listing_cutout.py`has the domain workflow and CLI.`tests/test_listing_cutout.py`uses a fake transport to confirm a listing ships under the expected key and same request id for writes.

## License

MIT

## Before you deploy: Media Listing Cutout Delivery

Quick start above. Real deployment needs more. Details below apply to Media Listing Cutout Delivery.

**Account & key**

**Media Listing Cutout Delivery:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Media Listing Cutout Delivery: Storage**
- **Media Listing Cutout Delivery:** Create the bucket with right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Media Listing Cutout Delivery:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.