"""
Flask Web Application for File Version Control System.
Serves a GitHub-like dark UI for managing file versions.
"""

import os
import datetime
from flask import Flask, render_template, jsonify, request
from version_manager import VersionManager

app = Flask(__name__)
vm = VersionManager()

# ─── Pages ────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main UI page."""
    return render_template("index.html")

# ─── API Endpoints ───────────────────────────────────────────────

@app.route("/api/versions", methods=["GET"])
def api_list_versions():
    """Return all versions as JSON."""
    try:
        versions = vm.list_versions()
        data = []
        for v in versions:
            # Read first line of version file as a preview
            preview = ""
            fname = f"project_v{v[0]}.txt"
            fpath = os.path.join(vm.versions_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        preview = f.read().strip()[:120]
                except Exception:
                    preview = "[unable to read]"

            data.append({
                "version_no": v[0],
                "file_name": v[1],
                "created_at": v[2].strftime("%Y-%m-%d %H:%M:%S") if v[2] else "N/A",
                "relative_time": _relative_time(v[2]) if v[2] else "N/A",
                "preview": preview
            })
        return jsonify({"success": True, "versions": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/versions/create", methods=["POST"])
def api_create_version():
    """Create a new version snapshot."""
    try:
        version_no, file_name, created_at = vm.create_version()
        return jsonify({
            "success": True,
            "version_no": version_no,
            "file_name": file_name,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/versions/compare", methods=["POST"])
def api_compare_versions():
    """Compare two versions."""
    try:
        body = request.get_json()
        v1 = int(body.get("v1", 0))
        v2 = int(body.get("v2", 0))
        if v1 == 0 or v2 == 0:
            return jsonify({"success": False, "error": "Please provide both version numbers."}), 400

        diff = vm.compare_versions(v1, v2)

        # Also read full file contents for side-by-side view
        path1 = os.path.join(vm.versions_dir, f"project_v{v1}.txt")
        path2 = os.path.join(vm.versions_dir, f"project_v{v2}.txt")
        content1 = ""
        content2 = ""
        if os.path.exists(path1):
            with open(path1, "r", encoding="utf-8") as f:
                content1 = f.read()
        if os.path.exists(path2):
            with open(path2, "r", encoding="utf-8") as f:
                content2 = f.read()

        return jsonify({
            "success": True,
            "diff": diff,
            "content1": content1,
            "content2": content2
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/versions/restore", methods=["POST"])
def api_restore_version():
    """Restore a version back to the base file."""
    try:
        body = request.get_json()
        version_no = int(body.get("version_no", 0))
        if version_no == 0:
            return jsonify({"success": False, "error": "Please provide a version number."}), 400

        restored_path = vm.restore_version(version_no)
        return jsonify({"success": True, "restored_to": restored_path})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/versions/delete", methods=["POST"])
def api_delete_version():
    """Delete a version (file + DB record)."""
    try:
        body = request.get_json()
        version_no = int(body.get("version_no", 0))
        if version_no == 0:
            return jsonify({"success": False, "error": "Please provide a version number."}), 400

        db_del, file_del = vm.delete_version(version_no)
        return jsonify({
            "success": True,
            "db_deleted": db_del,
            "file_deleted": file_del
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/basefile", methods=["GET"])
def api_get_basefile():
    """Get the current base file content."""
    try:
        content = ""
        if os.path.exists(vm.base_file):
            with open(vm.base_file, "r", encoding="utf-8") as f:
                content = f.read()
        return jsonify({"success": True, "content": content, "filename": vm.base_file})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/basefile", methods=["POST"])
def api_update_basefile():
    """Update the base file content and auto-snapshot."""
    try:
        body = request.get_json()
        new_content = body.get("content", "")

        with open(vm.base_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Auto-snapshot
        version_no, file_name, created_at = vm.create_version()
        return jsonify({
            "success": True,
            "version_no": version_no,
            "file_name": file_name,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Get project statistics."""
    try:
        versions = vm.list_versions()
        total = len(versions)

        # Count files on disk
        files_on_disk = 0
        if os.path.exists(vm.versions_dir):
            files_on_disk = len([f for f in os.listdir(vm.versions_dir) if f.endswith(".txt")])

        # Base file info
        base_size = 0
        if os.path.exists(vm.base_file):
            base_size = os.path.getsize(vm.base_file)

        # Latest version date
        latest = versions[-1][2].strftime("%Y-%m-%d") if versions else "N/A"
        earliest = versions[0][2].strftime("%Y-%m-%d") if versions else "N/A"

        # Build activity data (versions per date) for contribution graph
        activity = {}
        for v in versions:
            if v[2]:
                date_key = v[2].strftime("%Y-%m-%d")
                activity[date_key] = activity.get(date_key, 0) + 1

        return jsonify({
            "success": True,
            "total_versions": total,
            "files_on_disk": files_on_disk,
            "base_file_size": base_size,
            "latest_version_date": latest,
            "earliest_version_date": earliest,
            "activity": activity
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _relative_time(dt):
    """Convert datetime to relative time string like GitHub."""
    if not dt:
        return "N/A"
    now = datetime.datetime.now()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        m = seconds // 60
        return f"{m} minute{'s' if m != 1 else ''} ago"
    elif seconds < 86400:
        h = seconds // 3600
        return f"{h} hour{'s' if h != 1 else ''} ago"
    elif seconds < 2592000:
        d = seconds // 86400
        return f"{d} day{'s' if d != 1 else ''} ago"
    elif seconds < 31536000:
        mo = seconds // 2592000
        return f"{mo} month{'s' if mo != 1 else ''} ago"
    else:
        y = seconds // 31536000
        return f"{y} year{'s' if y != 1 else ''} ago"


if __name__ == "__main__":
    print("=" * 50)
    print("  File Version Control System - Web UI")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
