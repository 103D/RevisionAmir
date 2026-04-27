#!/usr/bin/env python3
"""
One-time migration script: import local JSON files into Redis.
Run locally before deploying to Vercel (with REDIS_URL set),
or run once after deployment to seed initial data.
"""

import json
import os
from pathlib import Path

try:
    import redis
except ImportError:
    print("Error: redis-py not installed. Run: pip install redis")
    exit(1)


def get_redis_client():
    redis_url = os.environ.get('REDIS_URL') or os.environ.get('UPSTASH_REDIS_REST_URL')
    if not redis_url:
        print("Error: REDIS_URL or UPSTASH_REDIS_REST_URL not set")
        exit(1)
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        exit(1)


def migrate_store(redis_client):
    """Migrate store.json to Redis"""
    BASE_DIR = Path(__file__).resolve().parent.parent
    store_file = BASE_DIR / "data" / "store.json"

    if not store_file.exists():
        print(f"Warning: {store_file} not found, initializing empty store")
        data = {"filials": []}
    else:
        with store_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✓ Loaded store.json ({len(data.get('filials', []))} filials)")

    redis_client.set("store:data", json.dumps(data, ensure_ascii=False))
    print("✓ store:data migrated to Redis")


def migrate_holidays(redis_client):
    """Migrate holidays.json to Redis"""
    BASE_DIR = Path(__file__).resolve().parent.parent
    holidays_file = BASE_DIR / "data" / "holidays.json"

    if not holidays_file.exists():
        print(f"Warning: {holidays_file} not found, initializing empty holidays")
        data = {"holidays": []}
    else:
        with holidays_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✓ Loaded holidays.json ({len(data.get('holidays', []))} holidays)")

    redis_client.set("holidays:data", json.dumps(data, ensure_ascii=False))
    print("✓ holidays:data migrated to Redis")


def main():
    print("=== Redis Migration ===\n")

    # Ensure Redis URL is set
    redis_url = os.environ.get('REDIS_URL') or os.environ.get('UPSTASH_REDIS_REST_URL')
    if not redis_url:
        print("ERROR: Set REDIS_URL or UPSTASH_REDIS_REST_URL environment variable")
        print("\nExample:")
        print("  export REDIS_URL=rediss://default:password@...upstash.io:6379")
        print("  python migrate_to_redis.py")
        exit(1)

    redis_client = get_redis_client()

    # Confirm overwrite
    existing_store = redis_client.get("store:data")
    existing_holidays = redis_client.get("holidays:data")
    if existing_store or existing_holidays:
        answer = input("Warning: Redis already has data. Overwrite? (yes/no): ").strip().lower()
        if answer != "yes":
            print("Aborted.")
            exit(0)

    migrate_store(redis_client)
    migrate_holidays(redis_client)

    print("\n✅ Migration complete! Data is now in Redis.")
    print("\nNext steps:")
    print("1. Deploy backend to Vercel with REDIS_URL set")
    print("2. Deploy frontend with VITE_API_URL pointing to backend")


if __name__ == "__main__":
    main()
