import os
import shutil
import datetime
import mysql.connector
from mysql.connector import Error

class VersionManager:
    def __init__(self, host="localhost", user="root", password="Pinky@143", database="version_system", base_file="project_base.txt", versions_dir="versions"):
        self.db_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.base_file = base_file
        self.versions_dir = versions_dir

    def _get_connection(self):
        """Establish and return a connection to the MySQL database."""
        try:
            return mysql.connector.connect(**self.db_config)
        except Error as err:
            raise RuntimeError(f"Database connection failed: {err}")

    def create_version(self):
        """
        Creates a new version snapshot of the base file.
        Copies base file to the versions folder with incremented version number
        and saves version metadata in MySQL.
        """
        if not os.path.exists(self.base_file):
            # If base file does not exist, initialize it with a default message
            with open(self.base_file, "w", encoding="utf-8") as f:
                f.write("This is version 1\n")
            print(f"[INFO] Base file '{self.base_file}' did not exist. Created a default one.")

        # Ensure the versions directory exists
        if not os.path.exists(self.versions_dir):
            os.makedirs(self.versions_dir)

        db = None
        cursor = None
        try:
            db = self._get_connection()
            cursor = db.cursor()

            # 1. Determine next version number robustly
            # Query maximum version from MySQL
            cursor.execute("SELECT MAX(version_no) FROM version_history")
            db_max = cursor.fetchone()[0]
            db_max = db_max if db_max is not None else 0

            # Inspect versions directory to find the max version number of files
            fs_max = 0
            for fname in os.listdir(self.versions_dir):
                # Expecting format project_v{no}.txt
                if fname.startswith("project_v") and fname.endswith(".txt"):
                    try:
                        v_num = int(fname[len("project_v"):-len(".txt")])
                        fs_max = max(fs_max, v_num)
                    except ValueError:
                        pass

            # Next version number is max of both + 1
            version_no = max(db_max, fs_max) + 1

            # 2. Copy the base file to the versions folder
            new_version_file = f"project_v{version_no}.txt"
            new_version_path = os.path.join(self.versions_dir, new_version_file)
            shutil.copy(self.base_file, new_version_path)

            # Normalize path slashes to match original format (versions/project_v{no}.txt)
            db_file_path = f"{self.versions_dir}/{new_version_file}"

            # 3. Save metadata into MySQL database
            created_at = datetime.datetime.now()
            query = "INSERT INTO version_history (version_no, file_name, created_at) VALUES (%s, %s, %s)"
            cursor.execute(query, (version_no, db_file_path, created_at))
            db.commit()

            return version_no, db_file_path, created_at

        except Error as err:
            raise RuntimeError(f"MySQL Error during version creation: {err}")
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    def list_versions(self):
        """
        Retrieves all version records from the MySQL database.
        Returns a list of tuples: (version_no, file_name, created_at).
        """
        db = None
        cursor = None
        try:
            db = self._get_connection()
            cursor = db.cursor()
            cursor.execute("SELECT version_no, file_name, created_at FROM version_history ORDER BY version_no ASC")
            return cursor.fetchall()
        except Error as err:
            raise RuntimeError(f"MySQL Error during retrieval: {err}")
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    def compare_versions(self, v1, v2):
        """
        Compares two version files line-by-line.
        Returns a list of strings representing the differences (deletions with '-' and additions with '+').
        """
        path1 = os.path.join(self.versions_dir, f"project_v{v1}.txt")
        path2 = os.path.join(self.versions_dir, f"project_v{v2}.txt")

        # Validate file existence
        missing = []
        if not os.path.exists(path1):
            missing.append(f"Version {v1} (file: {path1})")
        if not os.path.exists(path2):
            missing.append(f"Version {v2} (file: {path2})")
        
        if missing:
            raise FileNotFoundError(f"Missing files for: {', '.join(missing)}")

        try:
            with open(path1, "r", encoding="utf-8") as f1:
                lines1 = f1.readlines()
            with open(path2, "r", encoding="utf-8") as f2:
                lines2 = f2.readlines()
        except Exception as err:
            raise RuntimeError(f"Error reading version files: {err}")

        diff = []
        max_len = max(len(lines1), len(lines2))

        for i in range(max_len):
            l1 = lines1[i].strip() if i < len(lines1) else ""
            l2 = lines2[i].strip() if i < len(lines2) else ""

            if l1 != l2:
                if l1:
                    diff.append(f"- {l1}")
                if l2:
                    diff.append(f"+ {l2}")
                    
        return diff

    def restore_version(self, version_no):
        """
        Restores an older version file by copying it back as the base file.
        """
        version_file = f"project_v{version_no}.txt"
        version_path = os.path.join(self.versions_dir, version_file)

        if not os.path.exists(version_path):
            raise FileNotFoundError(f"Version {version_no} file does not exist at '{version_path}'.")

        try:
            shutil.copy(version_path, self.base_file)
            return self.base_file
        except Exception as err:
            raise RuntimeError(f"Error copying version file to base file: {err}")

    def delete_version(self, version_no):
        """
        Deletes a version: removes the version file and deletes the MySQL record.
        Returns True if successful.
        """
        db = None
        cursor = None
        try:
            db = self._get_connection()
            cursor = db.cursor()

            # 1. Delete from database
            query = "DELETE FROM version_history WHERE version_no = %s"
            cursor.execute(query, (version_no,))
            deleted_rows = cursor.rowcount
            db.commit()

            # 2. Delete file if it exists
            version_file = f"project_v{version_no}.txt"
            version_path = os.path.join(self.versions_dir, version_file)
            file_deleted = False
            if os.path.exists(version_path):
                os.remove(version_path)
                file_deleted = True

            if deleted_rows == 0 and not file_deleted:
                raise ValueError(f"Version {version_no} not found in database or disk.")

            return deleted_rows > 0, file_deleted

        except Error as err:
            raise RuntimeError(f"MySQL Error during version deletion: {err}")
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()
