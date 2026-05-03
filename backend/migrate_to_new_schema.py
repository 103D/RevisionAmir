#!/usr/bin/env python3
"""
Migrate old schema to new schema:
- Move next_revision_date and previous_revision_date into revision_dates array
- Ensure revision_dates contains all unique dates
- Remove next_revision_date and previous_revision_date from stored data
"""

import json
import os
from pathlib import Path
from datetime import date

try:
    from app.store import JsonStore
except ImportError:
    from store import JsonStore

def migrate_store(store: JsonStore):
    """Migrate data in the store"""
    data = store.read()
    filials = data.get('filials', [])
    changed = False

    for filial in filials:
        # Collect all dates
        first_date = filial.get('first_revision_date')
        prev_date = filial.pop('previous_revision_date', None)
        next_date = filial.pop('next_revision_date', None)
        revision_dates = filial.get('revision_dates', [])

        # Combine all dates
        all_dates = set(revision_dates)
        if first_date:
            all_dates.add(first_date)
        if prev_date:
            all_dates.add(prev_date)
        if next_date:
            all_dates.add(next_date)

        # Sort
        sorted_dates = sorted(all_dates)
        if sorted_dates != revision_dates:
            filial['revision_dates'] = sorted_dates
            changed = True

        # Ensure shortage exists
        if 'shortage' not in filial:
            filial['shortage'] = 0
            changed = True

    if changed:
        store.write(data)
        print(f"Migrated store: {len(filials)} filials")
    else:
        print("No migration needed")

def main():
    # Check if we are in Vercel or local
    is_vercel = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))
    if is_vercel:
        print("Running on Vercel, using Redis or env store")
        # Use RedisStore if available
        try:
            from app.redis_store import RedisStore
            store = RedisStore()
            migrate_store(store)
        except Exception as e:
            print(f"Error: {e}")
        return

    # Local: use JsonStore with default path
    base = Path(__file__).resolve().parent
    data_dir = base / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    store_path = data_dir / 'store.json'
    store = JsonStore(str(store_path))
    migrate_store(store)

if __name__ == '__main__':
    main()
