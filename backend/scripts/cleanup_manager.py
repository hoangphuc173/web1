#!/usr/bin/env python3
"""
Auto Cleanup Script for Test Files
Automatically removes temporary test files when tasks are completed
"""

import os
import glob
import time
from datetime import datetime
import json

class FileCleanupManager:
    def __init__(self, workspace_dir='.'):
        self.workspace_dir = workspace_dir
        self.cleanup_log = 'cleanup_log.json'
        self.test_patterns = [
            'test_*.py',
            'check_*.py',
            'migrate_*.py',
            'temp_*.py',
            'debug_*.py',
            '*_test.py',
            '*_check.py',
            '*.tmp',
            '*.temp'
        ]
        self.load_log()
    
    def load_log(self):
        """Load cleanup log"""
        if os.path.exists(self.cleanup_log):
            with open(self.cleanup_log, 'r', encoding='utf-8') as f:
                self.log = json.load(f)
        else:
            self.log = {
                'created': [],
                'deleted': [],
                'last_cleanup': None
            }
    
    def save_log(self):
        """Save cleanup log"""
        with open(self.cleanup_log, 'w', encoding='utf-8') as f:
            json.dump(self.log, f, indent=2)
    
    def register_test_file(self, filepath):
        """Register a test file for tracking"""
        if filepath not in self.log['created']:
            self.log['created'].append({
                'file': filepath,
                'created_at': datetime.now().isoformat(),
                'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
            })
            self.save_log()
            print(f"✓ Registered test file: {filepath}")
    
    def find_test_files(self):
        """Find all test files matching patterns"""
        test_files = []
        for pattern in self.test_patterns:
            matches = glob.glob(os.path.join(self.workspace_dir, pattern))
            test_files.extend(matches)
        
        # Remove duplicates
        test_files = list(set(test_files))
        
        # Exclude important files
        exclude_files = ['test_api.py', 'requirements.txt', 'setup.py']
        test_files = [f for f in test_files if os.path.basename(f) not in exclude_files]
        
        return test_files
    
    def cleanup_test_files(self, dry_run=False):
        """Remove test files"""
        test_files = self.find_test_files()
        
        if not test_files:
            print("✓ No test files to clean up")
            return []
        
        print(f"\n{'DRY RUN: ' if dry_run else ''}Found {len(test_files)} test files:")
        
        cleaned_files = []
        for filepath in test_files:
            try:
                file_size = os.path.getsize(filepath)
                print(f"  - {filepath} ({file_size} bytes)")
                
                if not dry_run:
                    os.remove(filepath)
                    cleaned_files.append({
                        'file': filepath,
                        'deleted_at': datetime.now().isoformat(),
                        'size': file_size
                    })
                    print("    ✓ Deleted")
                
            except Exception as e:
                print(f"    ✗ Error: {e}")
        
        if not dry_run and cleaned_files:
            self.log['deleted'].extend(cleaned_files)
            self.log['last_cleanup'] = datetime.now().isoformat()
            self.save_log()
            
            total_size = sum(f['size'] for f in cleaned_files)
            print(f"\n✓ Cleaned up {len(cleaned_files)} files ({total_size:,} bytes)")
        
        return cleaned_files
    
    def cleanup_old_files(self, max_age_hours=24):
        """Remove files older than specified hours"""
        current_time = time.time()
        old_files = []
        
        for file_info in self.log['created']:
            filepath = file_info['file']
            if os.path.exists(filepath):
                file_age = (current_time - os.path.getmtime(filepath)) / 3600
                if file_age > max_age_hours:
                    old_files.append(filepath)
        
        if old_files:
            print(f"\nFound {len(old_files)} files older than {max_age_hours} hours")
            for filepath in old_files:
                try:
                    os.remove(filepath)
                    print(f"✓ Deleted old file: {filepath}")
                except Exception as e:
                    print(f"✗ Error deleting {filepath}: {e}")
        
        return old_files
    
    def show_status(self):
        """Show cleanup status"""
        print("\n" + "="*60)
        print("FILE CLEANUP STATUS")
        print("="*60)
        
        # Created files
        print(f"\n📝 Tracked Test Files: {len(self.log['created'])}")
        if self.log['created']:
            for file_info in self.log['created'][-5:]:  # Show last 5
                print(f"  - {file_info['file']} ({file_info['size']} bytes)")
            if len(self.log['created']) > 5:
                print(f"  ... and {len(self.log['created']) - 5} more")
        
        # Deleted files
        print(f"\n🗑️  Deleted Files: {len(self.log['deleted'])}")
        if self.log['deleted']:
            total_size = sum(f['size'] for f in self.log['deleted'])
            print(f"  Total space freed: {total_size:,} bytes")
        
        # Last cleanup
        if self.log['last_cleanup']:
            print(f"\n🕐 Last Cleanup: {self.log['last_cleanup']}")
        
        # Current test files
        current_files = self.find_test_files()
        print(f"\n📂 Current Test Files: {len(current_files)}")
        if current_files:
            for f in current_files:
                size = os.path.getsize(f)
                print(f"  - {f} ({size} bytes)")
        
        print("="*60)
    
    def auto_cleanup(self):
        """Automatic cleanup with confirmation"""
        test_files = self.find_test_files()
        
        if not test_files:
            print("✓ No test files to clean up")
            return
        
        print(f"\n⚠️  Found {len(test_files)} test files to clean up:")
        for f in test_files:
            print(f"  - {f}")
        
        # Auto-confirm in script mode
        response = 'y'
        
        if response.lower() == 'y':
            self.cleanup_test_files()
        else:
            print("Cleanup cancelled")


def main():
    """Main function"""
    import sys
    
    manager = FileCleanupManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'cleanup':
            manager.cleanup_test_files()
        elif command == 'dry-run':
            manager.cleanup_test_files(dry_run=True)
        elif command == 'status':
            manager.show_status()
        elif command == 'old':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            manager.cleanup_old_files(max_age_hours=hours)
        elif command == 'auto':
            manager.auto_cleanup()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python cleanup_manager.py [cleanup|dry-run|status|old|auto]")
    else:
        # Default: show status and auto cleanup
        manager.show_status()
        print("\nDo you want to clean up test files? (y/n): ", end='')
        if input().lower() == 'y':
            manager.cleanup_test_files()


if __name__ == '__main__':
    main()
