"""
Delete all test data completely
Removes all files prefixed with TEST_ and all processed/aggregated data
"""

import os
import shutil
from pathlib import Path

def delete_test_files():
    """Delete all test data files"""
    
    print("=" * 70)
    print("DELETE ALL TEST DATA")
    print("=" * 70)
    print("\n⚠️  This will permanently delete:")
    print("  - All TEST_ files in data/raw/")
    print("  - All processed data in data/processed/")
    print("  - All aggregated data in data/aggregated/")
    print("  - All audit reports in reports/")
    print("  - ID mapping file")
    print("  - Hashing salt (will be regenerated)")
    
    print("\n✅ This will NOT delete:")
    print("  - Any scripts")
    print("  - Documentation")
    print("  - Directory structure")
    
    response = input("\nAre you sure you want to delete all test data? (type 'DELETE' to confirm): ")
    
    if response != 'DELETE':
        print("\n❌ Deletion cancelled")
        return
    
    print("\n🗑️  Deleting test data...")
    
    deleted_count = 0
    
    # Delete TEST_ files in data/raw/
    for root, dirs, files in os.walk('data/raw'):
        for file in files:
            if file.startswith('TEST_'):
                filepath = Path(root) / file
                filepath.unlink()
                print(f"  ✓ Deleted: {filepath}")
                deleted_count += 1
    
    # Delete id_link_file.csv (was copied from TEST version)
    if Path('data/raw/master/id_link_file.csv').exists():
        Path('data/raw/master/id_link_file.csv').unlink()
        print(f"  ✓ Deleted: data/raw/master/id_link_file.csv")
        deleted_count += 1
    
    # Delete all processed data
    if Path('data/processed').exists():
        for item in Path('data/processed').iterdir():
            if item.is_file():
                item.unlink()
                print(f"  ✓ Deleted: {item}")
                deleted_count += 1
            elif item.is_dir():
                shutil.rmtree(item)
                print(f"  ✓ Deleted directory: {item}")
                deleted_count += 1
    
    # Delete all aggregated data
    if Path('data/aggregated').exists():
        for item in Path('data/aggregated').iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                print(f"  ✓ Deleted directory: {item}")
                deleted_count += 1
            elif item.is_file():
                item.unlink()
                print(f"  ✓ Deleted: {item}")
                deleted_count += 1
    
    # Delete reports
    if Path('reports').exists():
        for item in Path('reports').iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                print(f"  ✓ Deleted directory: {item}")
                deleted_count += 1
            elif item.is_file():
                item.unlink()
                print(f"  ✓ Deleted: {item}")
                deleted_count += 1
    
    # Delete hashing salt
    if Path('hashing_salt.txt').exists():
        Path('hashing_salt.txt').unlink()
        print(f"  ✓ Deleted: hashing_salt.txt")
        deleted_count += 1
    
    print("\n" + "=" * 70)
    print("TEST DATA DELETION COMPLETE")
    print("=" * 70)
    
    print(f"\n✓ Deleted {deleted_count} files/directories")
    print("\n✅ System is now clean and ready for real data")
    print("\n📋 Next steps:")
    print("  1. Get real ID link file from IT")
    print("  2. Save as: data/raw/master/id_link_file.csv (without TEST_ prefix)")
    print("  3. Process your real data files")
    
    print("\n⚠️  Note: Hashing salt was deleted")
    print("  - New salt will be generated when you process real data")
    print("  - This means anonymous IDs will be different from test")
    print("  - This is intentional to keep test and real data separate")

if __name__ == "__main__":
    delete_test_files()
