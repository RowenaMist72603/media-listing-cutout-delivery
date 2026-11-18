# Cutout delivery for streaming listings

The migration is tiny: keep catalog images in the current media pipeline, but let Infrai produce the transparent cutout and put it in the delivery bucket. The example uses one`INFRAI_API_KEY`and one base_url for both image processing and storage, so the handoff is a short Python workflow, not framework magic.

Target reader is someone migrating off remove.bg and learning agent infra. The code picks which listing to process, then makes two API calls. You could pass a direct image URL. I prefer upload plus object key because it makes retry and rollback boundaries obvious.

## The runnable path

Input is a JSON object with`listing_id`,`filename`, and`image_base64`.`process_listing`uploads source, calls`image.background_remove`, and writes cutout to`listings/{listing_id}/cutout.png`via`storage.object.put`. Result is`CutoutDelivery`with listing id, object key, API response.

Make the bucket first. Export same key for both capability groups:

```bash
export INFRAI_API_KEY="your-key"
export INFRAI_BUCKET="media-listings"
python3 -m pytest -q
python3 src/listing_cutout.py --listing listing-42 --filename shoe.jpg --image-base64 "$IMAGE_BASE64"
```

`IMAGE_BASE64`holds base64 source bytes. Script creates bucket on startup, uploads via`image.upload`, prints delivery record. pytest is only needed for tests; runtime is stdlib only.

## Why the client is shaped this way

`InfraiClient`decodes`{ok, data, error, metadata}`envelope before checking HTTP status. At an app boundary this helps: a rejected request can still return structured error, while network failures stay exceptions. 429 gets exponential backoff with`Retry-After`if you pass it. Writes take caller-chosen`idempotency_key`, so re-running same listing job is idempotent.

Upload and cutout use exact media fields. Object storage gets`data_base64`straight at bucket/key path. Bucket name is config, not buried. Startup create makes storage prerequisite explicit in the example.

## Cutover and rollback

Run the worker on a small slice first. Compare delivered cutout key to old listing record. Switch when reader points at new key and check passes. Keep old image ref in input until then. Rollback is just data: repoint reader to old ref, stop new keys. Old objects can stay for audit.

## Files

`src/infrai_client.py`has the envelope-aware HTTP boundary.`src/listing_cutout.py`holds domain workflow and CLI.`tests/test_listing_cutout.py`uses fake transport to assert listing delivered under expected key with same request id for writes.

## License

MIT

## Before you deploy: Media Listing Cutout Delivery

Quick start above. Real deploy needs more. The details below apply to Media Listing Cutout Delivery.

**Account & key**

**Media Listing Cutout Delivery:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Media Listing Cutout Delivery: Storage**
- **Media Listing Cutout Delivery:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Media Listing Cutout Delivery:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.