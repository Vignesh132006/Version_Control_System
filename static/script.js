/* ═══════════════════════════════════════════════════
   File Version Control System – Frontend Logic
   ═══════════════════════════════════════════════════ */

// ─── State ──────────────────────────────────────────
let allVersions = [];

// ─── Initialization ─────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    // Tab switching
    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => switchTab(tab.dataset.tab));
    });

    // Editor line numbers
    const textarea = document.getElementById("editorTextarea");
    if (textarea) {
        textarea.addEventListener("input", updateLineNumbers);
        textarea.addEventListener("scroll", syncScroll);
    }

    // Initial data load
    loadStats();
    loadVersions();
    loadBaseFile();
});

// ─── Tab Switching ──────────────────────────────────
function switchTab(tabName) {
    // Deactivate all tabs and sections
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(s => s.classList.remove("active"));

    // Activate selected tab and section
    const tab = document.querySelector(`[data-tab="${tabName}"]`);
    const section = document.getElementById(`section${capitalize(tabName)}`);

    if (tab) tab.classList.add("active");
    if (section) section.classList.add("active");

    // Refresh data when switching to specific tabs
    if (tabName === "commits") loadVersions();
    if (tabName === "editor") loadBaseFile();
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ─── Load Project Stats ─────────────────────────────
async function loadStats() {
    try {
        const res = await fetch("/api/stats");
        const data = await res.json();

        if (data.success) {
            document.getElementById("statCommits").textContent = `${data.total_versions} Commits`;
            document.getElementById("statDate").textContent = `Since ${data.earliest_version_date}`;
            document.getElementById("commitCount").textContent = data.total_versions;
            document.getElementById("totalContributions").textContent = `${data.total_versions} contributions in the last year`;
            document.getElementById("repoSize").textContent = formatBytes(data.base_file_size);

            // Build contribution graph
            buildContributionGraph(data.activity);

            // DB status
            const dot = document.getElementById("dbStatusDot");
            dot.classList.add("online");
            dot.title = "MySQL Connected";
        }
    } catch (err) {
        const dot = document.getElementById("dbStatusDot");
        dot.classList.add("offline");
        dot.title = "MySQL Disconnected";
        console.error("Stats error:", err);
    }
}

// ─── Load Versions ──────────────────────────────────
async function loadVersions() {
    try {
        const res = await fetch("/api/versions");
        const data = await res.json();

        if (data.success) {
            allVersions = data.versions;
            renderCommitsList(data.versions);
            populateDiffSelectors(data.versions);
        }
    } catch (err) {
        console.error("Load versions error:", err);
        showToast("Failed to load versions", "error");
    }
}

// ─── Render Commits List ────────────────────────────
function renderCommitsList(versions) {
    const container = document.getElementById("commitsList");
    if (!versions || versions.length === 0) {
        container.innerHTML = `
            <div class="diff-empty" style="padding:40px;">
                <svg width="48" height="48" viewBox="0 0 16 16" fill="currentColor" opacity="0.3"><path d="M11.93 8.5a4.002 4.002 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 010 1.5zm-1.43-.5a2.5 2.5 0 10-5 0 2.5 2.5 0 005 0z"/></svg>
                <p>No versions found. Create your first snapshot!</p>
            </div>`;
        return;
    }

    // Group by date
    const groups = {};
    versions.forEach(v => {
        const date = v.created_at.split(" ")[0];
        if (!groups[date]) groups[date] = [];
        groups[date].push(v);
    });

    // Render groups in reverse chronological order
    const sortedDates = Object.keys(groups).sort().reverse();
    let html = "";

    sortedDates.forEach(date => {
        const formattedDate = formatDate(date);
        html += `<div class="commit-group-header">Commits on ${formattedDate}</div>`;

        // Reverse versions within each group too (newest first)
        const groupVersions = groups[date].reverse();
        groupVersions.forEach(v => {
            const sha = generateSha(v.version_no);
            html += `
            <div class="commit-item">
                <div class="commit-left">
                    <div class="commit-icon">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M11.93 8.5a4.002 4.002 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 010 1.5zm-1.43-.5a2.5 2.5 0 10-5 0 2.5 2.5 0 005 0z"/></svg>
                    </div>
                    <div class="commit-info">
                        <div class="commit-message">Version ${v.version_no} snapshot</div>
                        <div class="commit-meta">local-user committed ${v.relative_time} &middot; ${v.created_at}</div>
                        ${v.preview ? `<div class="commit-preview">${escapeHtml(v.preview)}</div>` : ""}
                    </div>
                </div>
                <span class="commit-sha" title="${sha}">${sha.substring(0, 7)}</span>
                <div class="commit-actions">
                    <button class="commit-btn" onclick="restoreVersion(${v.version_no})" title="Restore this version">
                        <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M1.705 8.005a.75.75 0 01.834.656 5.5 5.5 0 009.592 2.97l-1.204-1.204a.25.25 0 01.177-.427h3.646a.25.25 0 01.25.25v3.646a.25.25 0 01-.427.177l-1.38-1.38A7.002 7.002 0 011.05 8.84a.75.75 0 01.656-.834zM8 2.5a5.487 5.487 0 00-4.131 1.869l1.204 1.204A.25.25 0 014.896 6H1.25A.25.25 0 011 5.75V2.104a.25.25 0 01.427-.177l1.38 1.38A7.002 7.002 0 0114.95 7.16a.75.75 0 11-1.49.178A5.5 5.5 0 008 2.5z"/></svg>
                        Restore
                    </button>
                    <button class="commit-btn danger" onclick="deleteVersion(${v.version_no})" title="Delete this version">
                        <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M11 1.75V3h2.25a.75.75 0 010 1.5H2.75a.75.75 0 010-1.5H5V1.75C5 .784 5.784 0 6.75 0h2.5C10.216 0 11 .784 11 1.75zM4.496 6.675l.66 6.6a.25.25 0 00.249.225h5.19a.25.25 0 00.249-.225l.66-6.6a.75.75 0 011.492.149l-.66 6.6A1.748 1.748 0 0110.595 15h-5.19a1.75 1.75 0 01-1.741-1.575l-.66-6.6a.75.75 0 111.492-.15zM6.5 1.75V3h3V1.75a.25.25 0 00-.25-.25h-2.5a.25.25 0 00-.25.25z"/></svg>
                        Delete
                    </button>
                </div>
            </div>`;
        });
    });

    container.innerHTML = html;
}

// ─── Create Snapshot ────────────────────────────────
async function createSnapshot() {
    try {
        const res = await fetch("/api/versions/create", { method: "POST" });
        const data = await res.json();

        if (data.success) {
            showToast(`Version ${data.version_no} created successfully`, "success");
            loadVersions();
            loadStats();
        } else {
            showToast(data.error || "Failed to create snapshot", "error");
        }
    } catch (err) {
        showToast("Failed to create snapshot", "error");
        console.error(err);
    }
}

// ─── Restore Version ────────────────────────────────
function restoreVersion(versionNo) {
    showModal(
        "Restore Version",
        `Are you sure you want to restore Version ${versionNo}? This will overwrite the current base file.`,
        async () => {
            try {
                const res = await fetch("/api/versions/restore", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ version_no: versionNo })
                });
                const data = await res.json();

                if (data.success) {
                    showToast(`Version ${versionNo} restored to base file`, "success");
                    loadBaseFile();
                } else {
                    showToast(data.error || "Restore failed", "error");
                }
            } catch (err) {
                showToast("Restore failed", "error");
                console.error(err);
            }
            closeModal();
        }
    );
}

// ─── Delete Version ─────────────────────────────────
function deleteVersion(versionNo) {
    showModal(
        "Delete Version",
        `Are you sure you want to permanently delete Version ${versionNo}? This will remove both the file and database record.`,
        async () => {
            try {
                const res = await fetch("/api/versions/delete", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ version_no: versionNo })
                });
                const data = await res.json();

                if (data.success) {
                    showToast(`Version ${versionNo} deleted`, "success");
                    loadVersions();
                    loadStats();
                } else {
                    showToast(data.error || "Delete failed", "error");
                }
            } catch (err) {
                showToast("Delete failed", "error");
                console.error(err);
            }
            closeModal();
        }
    );
}

// ─── Compare Versions ───────────────────────────────
async function compareVersions() {
    const v1 = parseInt(document.getElementById("diffV1").value);
    const v2 = parseInt(document.getElementById("diffV2").value);

    if (!v1 || !v2) {
        showToast("Please select two versions to compare", "error");
        return;
    }

    if (v1 === v2) {
        showToast("Please select two different versions", "error");
        return;
    }

    const diffOutput = document.getElementById("diffOutput");
    const diffEmpty = document.getElementById("diffEmpty");
    const diffLines = document.getElementById("diffLines");
    const diffHeader = document.getElementById("diffFileHeader");

    try {
        const res = await fetch("/api/versions/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ v1, v2 })
        });
        const data = await res.json();

        if (data.success) {
            diffEmpty.style.display = "none";
            diffOutput.style.display = "block";
            diffHeader.querySelector("span").textContent = `project_v${v1}.txt ... project_v${v2}.txt`;

            if (data.diff.length === 0) {
                diffLines.innerHTML = `<div class="diff-no-changes">No differences found. Both versions are identical.</div>`;
            } else {
                // Build unified diff view with context
                let html = "";
                const lines1 = data.content1.split("\n");
                const lines2 = data.content2.split("\n");
                const maxLines = Math.max(lines1.length, lines2.length);

                for (let i = 0; i < maxLines; i++) {
                    const l1 = i < lines1.length ? lines1[i] : "";
                    const l2 = i < lines2.length ? lines2[i] : "";

                    if (l1.trim() === l2.trim()) {
                        html += `<div class="diff-line unchanged">
                            <span class="diff-line-prefix"> </span>
                            <span class="diff-line-content">${escapeHtml(l1)}</span>
                        </div>`;
                    } else {
                        if (l1) {
                            html += `<div class="diff-line deletion">
                                <span class="diff-line-prefix">-</span>
                                <span class="diff-line-content">${escapeHtml(l1)}</span>
                            </div>`;
                        }
                        if (l2) {
                            html += `<div class="diff-line addition">
                                <span class="diff-line-prefix">+</span>
                                <span class="diff-line-content">${escapeHtml(l2)}</span>
                            </div>`;
                        }
                    }
                }

                diffLines.innerHTML = html;
            }
        } else {
            showToast(data.error || "Compare failed", "error");
        }
    } catch (err) {
        showToast("Compare failed", "error");
        console.error(err);
    }
}

function populateDiffSelectors(versions) {
    const sel1 = document.getElementById("diffV1");
    const sel2 = document.getElementById("diffV2");

    const options = versions.map(v =>
        `<option value="${v.version_no}">v${v.version_no} - ${v.created_at}</option>`
    ).join("");

    sel1.innerHTML = options;
    sel2.innerHTML = options;

    // Default: select second-to-last and last
    if (versions.length >= 2) {
        sel1.value = versions[versions.length - 2].version_no;
        sel2.value = versions[versions.length - 1].version_no;
    }
}

// ─── Editor ─────────────────────────────────────────
async function loadBaseFile() {
    try {
        const res = await fetch("/api/basefile");
        const data = await res.json();

        if (data.success) {
            const textarea = document.getElementById("editorTextarea");
            textarea.value = data.content;
            updateLineNumbers();
        }
    } catch (err) {
        console.error("Load base file error:", err);
    }
}

async function saveAndSnapshot() {
    const textarea = document.getElementById("editorTextarea");
    const content = textarea.value;

    try {
        const res = await fetch("/api/basefile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content })
        });
        const data = await res.json();

        if (data.success) {
            showToast(`Saved & created Version ${data.version_no}`, "success");
            loadVersions();
            loadStats();
        } else {
            showToast(data.error || "Save failed", "error");
        }
    } catch (err) {
        showToast("Save failed", "error");
        console.error(err);
    }
}

function updateLineNumbers() {
    const textarea = document.getElementById("editorTextarea");
    const lineNumbers = document.getElementById("lineNumbers");
    const lines = textarea.value.split("\n").length;
    let html = "";
    for (let i = 1; i <= lines; i++) {
        html += i + "\n";
    }
    lineNumbers.textContent = html;
}

function syncScroll() {
    const textarea = document.getElementById("editorTextarea");
    const lineNumbers = document.getElementById("lineNumbers");
    lineNumbers.scrollTop = textarea.scrollTop;
}

// ─── Contribution Graph ─────────────────────────────
function buildContributionGraph(activity) {
    const graph = document.getElementById("contributionGraph");
    graph.innerHTML = "";

    // Generate 52 weeks x 7 days = 364 cells
    const today = new Date();
    const cells = [];

    for (let i = 363; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const key = date.toISOString().split("T")[0];
        const count = activity[key] || 0;

        let level = 0;
        if (count === 1) level = 1;
        else if (count === 2) level = 2;
        else if (count <= 4) level = 3;
        else if (count > 4) level = 4;

        cells.push({ date: key, count, level });
    }

    cells.forEach(cell => {
        const div = document.createElement("div");
        div.className = `contrib-cell level-${cell.level}`;
        div.title = `${cell.count} contribution${cell.count !== 1 ? "s" : ""} on ${cell.date}`;
        graph.appendChild(div);
    });
}

// ─── Toast Notifications ────────────────────────────
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icons = {
        success: `<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.751.751 0 01.018-1.042.751.751 0 011.042-.018L6 10.94l6.72-6.72a.75.75 0 011.06 0z"/></svg>`,
        error: `<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M3.72 3.72a.75.75 0 011.06 0L8 6.94l3.22-3.22a.751.751 0 011.042.018.751.751 0 01.018 1.042L9.06 8l3.22 3.22a.751.751 0 01-.018 1.042.751.751 0 01-1.042.018L8 9.06l-3.22 3.22a.751.751 0 01-1.042-.018.751.751 0 01-.018-1.042L6.94 8 3.72 4.78a.75.75 0 010-1.06z"/></svg>`,
        info: `<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M0 8a8 8 0 1116 0A8 8 0 010 8zm8-6.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM6.5 7.75A.75.75 0 017.25 7h1a.75.75 0 01.75.75v2.75h.25a.75.75 0 010 1.5h-2a.75.75 0 010-1.5h.25v-2h-.25a.75.75 0 01-.75-.75zM8 6a1 1 0 110-2 1 1 0 010 2z"/></svg>`
    };

    toast.innerHTML = `${icons[type] || icons.info}<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    // Remove after animation
    setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 4000);
}

// ─── Modal ──────────────────────────────────────────
function showModal(title, message, onConfirm) {
    document.getElementById("modalTitle").textContent = title;
    document.getElementById("modalMessage").textContent = message;
    document.getElementById("modalOverlay").style.display = "flex";

    const confirmBtn = document.getElementById("modalConfirmBtn");
    confirmBtn.onclick = onConfirm;
}

function closeModal() {
    document.getElementById("modalOverlay").style.display = "none";
}

// ─── Utility Functions ──────────────────────────────
function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function formatDate(dateStr) {
    const date = new Date(dateStr + "T00:00:00");
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function generateSha(versionNo) {
    // Generate a deterministic pseudo-SHA for display
    const base = "abcdef0123456789";
    let hash = "";
    let seed = versionNo * 2654435761;
    for (let i = 0; i < 40; i++) {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff;
        hash += base[seed % 16];
    }
    return hash;
}
