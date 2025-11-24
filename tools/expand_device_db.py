#!/usr/bin/env python3
"""Helper untuk expand device_db.json dari berbagai sumber"""

import json
from pathlib import Path

def expand_device_db_from_csv(csv_file: str) -> int:
    """Import device dari CSV (hasil scrape GSMArena, dsb)"""
    try:
        import csv
        
        db_file = Path('data/device_db_full.json')
        existing_db = []
        
        if db_file.exists():
            with open(db_file, 'r', encoding='utf-8') as f:
                existing_db = json.load(f)
        
        max_id = max((d.get('id', 0) for d in existing_db), default=0)
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                max_id += 1
                device = {
                    'id': max_id,
                    'brand': row.get('brand', '').lower(),
                    'manufacturer': row.get('manufacturer', ''),
                    'model': row.get('model', ''),
                    'device': row.get('device', '').lower(),
                    'product': row.get('product', '').lower(),
                    'android_version': int(row.get('android_version', 11)),
                    'cpu': row.get('cpu', ''),
                    'ram_gb': int(row.get('ram_gb', 4)),
                    'rom_gb': int(row.get('rom_gb', 64)),
                    'screen_dpi': int(row.get('screen_dpi', 400)),
                    'screen_size': row.get('screen_size', '6.0'),
                    'premium': row.get('premium', 'false').lower() == 'true',
                    'allow_pool': row.get('allow_pool', 'public,mass').split(',')
                }
                existing_db.append(device)
        
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(existing_db, f, indent=2, ensure_ascii=False)
        
        return max_id
    
    except Exception as e:
        print(f"❌ Error expanding DB: {e}")
        return 0

if __name__ == '__main__':
    # Usage: python tools/expand_device_db.py devices.csv
    import sys
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        count = expand_device_db_from_csv(csv_file)
        print(f"✅ Expanded DB: total {count} devices")
    else:
        print("Usage: python expand_device_db.py <csv_file>")
