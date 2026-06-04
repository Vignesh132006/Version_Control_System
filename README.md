# File Version Control System

A complete, production-ready File Version Control System written in Python with a MySQL backend database. This system allows you to snapshot versions of a base file, view version history, compare two versions line-by-line, restore a specific version, and delete versions from both disk and the database.

It comes with two interfaces:
1. **Unified Command-Line Interface (CLI)**: A robust console application using `tabulate` grids.
2. **Offline Web UI (GitHub Profile Theme)**: A premium, modern, responsive web dashboard styled like a GitHub dark profile with a pure black and white monochrome aesthetic. It features an overview tab with contribution activity graphs, a commits list, a side-by-side file comparison tool, and an in-browser code editor.

## Folder Structure

```text
Version control System Project/
├── db_setup.py         # Script to auto-create the MySQL database and table
├── version_manager.py  # Business logic module containing the VersionManager class
├── main.py             # Main unified command-line interface (CLI)
├── app.py              # Flask server hosting the Web REST API and serving UI
├── project_base.txt    # The active base file under version control
├── versions/           # Folder containing versioned snapshot files (project_v1.txt, etc.)
├── templates/
│   └── index.html      # GitHub profile-themed single page HTML structure
├── static/
│   ├── style.css       # Custom black-and-white GitHub dark styling
│   └── script.js       # Core frontend JavaScript for state and REST API handling
└── README.md           # Setup and usage instructions (this file)
```

## Setup Instructions

### 1. Install Dependencies
Install the required Python packages using `pip`:
```bash
pip install mysql-connector-python tabulate flask
```

### 2. Start MySQL Service
Ensure that your MySQL server is running. On Windows, if the service `MYSQL80` is stopped, you can start it using an Administrator PowerShell terminal:
```powershell
Start-Service -Name MYSQL80
```
Or via Administrator Command Prompt:
```cmd
net start MYSQL80
```

### 3. Run Database Setup
Run the `db_setup.py` script once to auto-create the `version_system` database and the `version_history` table if they do not exist:
```bash
python db_setup.py
```

## How to Run the App

### Option A: Web User Interface (Recommended)
Launch the Flask development server:
```bash
python app.py
```
Then open your web browser and navigate to:
```text
http://localhost:5000
```

#### Web UI Features:
- **Overview Tab**: Displays project statistics, repository metadata, a monochrome contribution activity graph summarizing commit frequencies, and a quick actions panel.
- **Commits Tab**: Displays a chronological, group-by-date list of all versions (commit snapshots) with SHA signatures, relative times, text previews, and one-click action buttons to restore or delete them.
- **Diff Tab**: A side-by-side comparison page where you can select any two versions to output a clean, highlighted line-by-line diff.
- **Editor Tab**: An interactive editor showing the current contents of `project_base.txt` with line numbers and a **Save & Snapshot** button to commit changes directly.

---

### Option B: Command Line Interface (CLI)
Launch the unified CLI menu:
```bash
python main.py
```

#### CLI Menu Options:
- **`[1] Create new version snapshot`**: Creates a copy of `project_base.txt` as `versions/project_v{N}.txt` and records it in MySQL.
- **`[2] View all versions`**: Displays a beautifully formatted grid table of all snapshots retrieved from MySQL.
- **`[3] Compare any two versions`**: Prompts for two version numbers and outputs a line-by-line diff (`-` for lines in the first version not in the second, `+` for lines added in the second).
- **`[4] Restore a version`**: Overwrites `project_base.txt` with the contents of a selected version.
- **`[5] Delete a version`**: Removes the snapshot file from disk and deletes the metadata entry from the MySQL table.
- **`[6] Edit base file content and auto-snapshot`**: Displays current content, prompts for updates, writes to `project_base.txt`, and automatically takes a version snapshot.
- **`[0] Exit`**: Safely closes the CLI menu.

