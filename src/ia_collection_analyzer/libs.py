from pathlib import Path
import json
import logging
import os
import time

import internetarchive as ia


CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
COLLECTION_TTL = 24 * 3600

logger = logging.getLogger(__name__)
ia_session = ia.ArchiveSession()


def get_cache_filename(key) -> Path:
    return CACHE_DIR / f"{key}.json"


def is_cache_valid(filename, ttl: float | int) -> bool:
    if not os.path.exists(filename):
        return False

    file_mtime = os.path.getmtime(filename)
    return (time.time() - file_mtime) < ttl


def get_collection(collection_id) -> list:
    cache_key = f"collection_{collection_id}"
    cache_filename = get_cache_filename(cache_key)

    if is_cache_valid(cache_filename, COLLECTION_TTL):
        logger.info(f"Using cache for {collection_id}")
        with open(cache_filename, "r") as cache_file:
            collection = json.load(cache_file)
    else:
        logger.info(f"Fetching collection {collection_id}")
        search = ia.Search(
            ia_session, query="collection:" + collection_id, sorts=["addeddate desc"]
        )
        collection = []
        for result in search:
            print(result["identifier"], end="       \r")
            collection.append(result)

        with open(cache_filename, "w") as cache_file:
            json.dump(collection, cache_file, indent=2)

    return collection


def get_collection_items(collection_id) -> list:
    collection = get_collection(collection_id)
    return [item["identifier"] for item in collection]


def get_item_metadata(item_id) -> dict:
    cache_key = f"item_metadata_{item_id}"
    cache_filename = get_cache_filename(cache_key)

    if os.path.exists(cache_filename):
        with open(cache_filename, "r") as cache_file:
            return json.load(cache_file)
    else:
        metadata = ia_session.get_item(item_id).metadata

        with open(cache_filename, "w") as cache_file:
            json.dump(metadata, cache_file)

        return metadata


def get_collection_items_metadata(collection_id) -> list[dict]:
    items = get_collection_items(collection_id)
    return [get_item_metadata(item) for item in items]


if __name__ == "__main__":
    collection_id = "speedydeletionwiki"
    items = get_collection_items(collection_id)
    print(items)
    metadata = get_item_metadata(items[0])
    print(metadata)
    items_metadata = get_collection_items_metadata(collection_id)
    print(items_metadata)