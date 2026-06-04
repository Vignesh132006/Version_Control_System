import os
import sys
from version_manager import VersionManager

try:
    from tabulate import tabulate
except ImportError:
    print("[WARNING] The 'tabulate' library is not installed. Please install it using: pip install tabulate")
    sys.exit(1)

def print_menu():
    print("\n" + "=" * 50)
    print("      FILE VERSION CONTROL SYSTEM (MYSQL BACKEND)     ")
    print("=" * 50)
    print(" [1] Create new version snapshot")
    print(" [2] View all versions (from MySQL)")
    print(" [3] Compare any two versions (line-by-line diff)")
    print(" [4] Restore a version (overwrite base file)")
    print(" [5] Delete a version (file + MySQL record)")
    print(" [6] Edit base file content and auto-snapshot")
    print(" [0] Exit")
    print("=" * 50)

def main():
    # Initialize version manager
    vm = VersionManager()

    while True:
        print_menu()
        choice = input("Select an option (0-6): ").strip()

        try:
            if choice == "1":
                print("\n[INFO] Creating a new version snapshot...")
                version_no, file_name, created_at = vm.create_version()
                print(f"[SUCCESS] Version {version_no} created.")
                print(f"   File path: {file_name}")
                print(f"   Timestamp: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")

            elif choice == "2":
                print("\n[INFO] Fetching versions from MySQL...")
                versions = vm.list_versions()
                if not versions:
                    print("[INFO] No versions found in database.")
                else:
                    # Format for tabulate
                    headers = ["Version No", "File Name", "Created At"]
                    formatted_versions = [
                        [v[0], v[1], v[2].strftime('%Y-%m-%d %H:%M:%S') if v[2] else "N/A"]
                        for v in versions
                    ]
                    print(tabulate(formatted_versions, headers=headers, tablefmt="grid"))

            elif choice == "3":
                print("\n[INFO] Compare Two Versions")
                try:
                    v1 = int(input("Enter first version number: ").strip())
                    v2 = int(input("Enter second version number: ").strip())
                except ValueError:
                    print("[ERROR] Version numbers must be integers.")
                    continue

                print(f"Comparing Version {v1} and Version {v2}...")
                diff = vm.compare_versions(v1, v2)
                
                print("\n" + "-" * 20 + " File Difference " + "-" * 20)
                if not diff:
                    print("No differences found. Both files are identical.")
                else:
                    for line in diff:
                        print(line)
                print("-" * 57)

            elif choice == "4":
                print("\n[INFO] Restore a Version")
                try:
                    version_no = int(input("Enter version number to restore: ").strip())
                except ValueError:
                    print("[ERROR] Version number must be an integer.")
                    continue

                confirm = input(f"[WARNING] Are you sure you want to overwrite '{vm.base_file}' with Version {version_no}? (y/n): ").strip().lower()
                if confirm == 'y':
                    restored_path = vm.restore_version(version_no)
                    print(f"[SUCCESS] Restored Version {version_no} back to '{restored_path}'.")
                else:
                    print("Restore cancelled.")

            elif choice == "5":
                print("\n[INFO] Delete a Version")
                try:
                    version_no = int(input("Enter version number to delete: ").strip())
                except ValueError:
                    print("[ERROR] Version number must be an integer.")
                    continue

                confirm = input(f"[WARNING] Are you sure you want to delete Version {version_no} from both disk and database? (y/n): ").strip().lower()
                if confirm == 'y':
                    db_del, file_del = vm.delete_version(version_no)
                    if db_del and file_del:
                        print(f"[SUCCESS] Deleted Version {version_no} from database and disk.")
                    elif db_del:
                        print(f"[WARNING] Deleted Version {version_no} from database, but file was already missing on disk.")
                    elif file_del:
                        print(f"[WARNING] Deleted Version {version_no} file from disk, but no database record was found.")
                else:
                    print("Deletion cancelled.")

            elif choice == "6":
                print("\n[INFO] Edit Base File & Auto-Snapshot")
                current_content = ""
                if os.path.exists(vm.base_file):
                    try:
                        with open(vm.base_file, "r", encoding="utf-8") as f:
                            current_content = f.read()
                    except Exception as err:
                        print(f"[WARNING] Could not read base file: {err}")

                print("-" * 50)
                print("Current content of base file:")
                print(current_content if current_content.strip() else "[File is empty]")
                print("-" * 50)

                print("Enter new content (Type 'CANCEL' to abort, or press Enter to keep current):")
                new_content = input("New Content: ").strip()

                if new_content == "CANCEL":
                    print("Edit cancelled.")
                    continue

                if new_content:
                    try:
                        with open(vm.base_file, "w", encoding="utf-8") as f:
                            f.write(new_content + "\n")
                        print("Base file updated successfully.")
                    except Exception as err:
                        print(f"[ERROR] Error updating base file: {err}")
                        continue
                else:
                    print("Keeping current content.")

                print("Creating auto-snapshot...")
                version_no, file_name, created_at = vm.create_version()
                print(f"[SUCCESS] Auto-snapshot created: Version {version_no}")
                print(f"   File path: {file_name}")

            elif choice == "0":
                print("\n[INFO] Exiting File Version Control System. Goodbye!")
                break

            else:
                print("[ERROR] Invalid option. Please enter a number between 0 and 6.")

        except Exception as e:
            print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Program interrupted. Exiting...")
        sys.exit(0)
