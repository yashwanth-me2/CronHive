const API_BASE = '/api/v1';
let authToken = '';

// DOM Elements
const totalJobsEl = document.getElementById('total-jobs');
const activeJobsEl = document.getElementById('active-jobs');
const jobsListEl = document.getElementById('jobs-list');
const newJobBtn = document.getElementById('new-job-btn');
const newJobForm = document.getElementById('new-job-form');
const toastContainer = document.getElementById('toast-container');
const tenantNameEl = document.getElementById('tenant-name');
const apiKeyDisplay = document.getElementById('api-key-display');
const settingsEmail = document.getElementById('settings-email');

// Navigation Logic
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Remove active class from all links and sections
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
        
        // Add active class to clicked link and corresponding section
        link.classList.add('active');
        const viewId = link.getAttribute('data-view');
        document.getElementById(viewId).classList.add('active');
    });
});

// Initialize Dashboard
async function init() {
    try {
        const authRes = await fetch(`${API_BASE}/auth/demo`, { method: 'POST' });
        const data = await authRes.json();
        authToken = data.access_token;
        
        await Promise.all([fetchJobs(), fetchMe()]);
        
        // Auto refresh jobs every 10s
        setInterval(fetchJobs, 10000);
    } catch (err) {
        showToast("Failed to connect to API", "error");
        jobsListEl.innerHTML = `<tr><td colspan="6" style="color:var(--danger)">Failed to connect to API</td></tr>`;
    }
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        if(toast.parentElement) toast.remove();
    }, 3000);
}

async function fetchMe() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const me = await res.json();
        tenantNameEl.textContent = me.name;
        settingsEmail.textContent = me.email;
        apiKeyDisplay.value = me.api_key;
    } catch (err) {
        console.error("Failed to fetch profile");
    }
}

async function fetchJobs() {
    try {
        const res = await fetch(`${API_BASE}/jobs`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const jobs = await res.json();
        
        totalJobsEl.textContent = jobs.length;
        activeJobsEl.textContent = jobs.filter(j => j.status === 'active').length;
        
        if (jobs.length === 0) {
            jobsListEl.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--text-muted);">No jobs scheduled yet. Create one from the Templates tab!</td></tr>`;
            return;
        }
        
        jobsListEl.innerHTML = jobs.map(job => `
            <tr>
                <td><strong>${job.name}</strong></td>
                <td><span style="font-family: monospace; color: var(--text-muted)">${job.target_url}</span></td>
                <td>${job.cron_expression || 'One-time'}</td>
                <td>${formatDate(job.next_run_at)}</td>
                <td><span class="badge ${job.status}">${job.status}</span></td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-small" onclick="triggerJob('${job.id}')" title="Run Now">▶ Run</button>
                        ${job.status === 'active' 
                            ? `<button class="btn-small" onclick="toggleJob('${job.id}', 'pause')">Pause</button>`
                            : `<button class="btn-small" onclick="toggleJob('${job.id}', 'resume')">Resume</button>`}
                        <button class="btn-small" onclick="viewLogs('${job.id}')">Logs</button>
                        <button class="btn-small" onclick="deleteJob('${job.id}')" style="color: var(--accent); border-color: rgba(244, 63, 94, 0.3);">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error("Failed to fetch jobs", err);
    }
}

window.deleteJob = async (id) => {
    if (!confirm("Are you sure you want to delete this job?")) return;
    try {
        const res = await fetch(`${API_BASE}/jobs/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) throw new Error();
        showToast("Job deleted successfully");
        fetchJobs();
    } catch (err) {
        showToast("Failed to delete job", "error");
    }
};

window.toggleJob = async (id, action) => {
    try {
        await fetch(`${API_BASE}/jobs/${id}/${action}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        showToast(`Job ${action}d successfully`);
        fetchJobs();
    } catch (err) {
        showToast(`Failed to ${action} job`, "error");
    }
};

window.triggerJob = async (id) => {
    try {
        await fetch(`${API_BASE}/jobs/${id}/trigger`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        showToast(`Job manually triggered!`, "success");
        fetchJobs();
    } catch (err) {
        showToast(`Failed to trigger job`, "error");
    }
};

window.viewLogs = async (id) => {
    const modal = document.getElementById('executions-modal');
    const list = document.getElementById('executions-list');
    modal.classList.add('show');
    list.innerHTML = `<tr><td colspan="5" class="loading"><div class="spinner"></div> Loading logs...</td></tr>`;
    
    try {
        const res = await fetch(`${API_BASE}/jobs/${id}/executions`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const execs = await res.json();
        
        if (execs.length === 0) {
            list.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 1rem; color: var(--text-muted);">No executions found yet.</td></tr>`;
            return;
        }
        
        list.innerHTML = execs.map(ex => `
            <tr>
                <td><span class="badge ${ex.status === 'success' ? 'success' : 'failed'}">${ex.status}</span></td>
                <td>${ex.attempt_number}</td>
                <td>${ex.http_status_code || '-'}</td>
                <td>${ex.duration_ms.toFixed(0)} ms</td>
                <td>${formatDate(ex.completed_at)}</td>
            </tr>
        `).join('');
    } catch (err) {
        list.innerHTML = `<tr><td colspan="5" style="color:var(--danger)">Failed to load logs</td></tr>`;
    }
};

window.useTemplate = (name, url, cron) => {
    document.getElementById('job-name').value = name;
    document.getElementById('job-url').value = url;
    document.getElementById('job-cron').value = cron;
    document.getElementById('job-modal').classList.add('show');
};

newJobForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.innerHTML = `<div class="spinner" style="width:1rem;height:1rem;"></div> Creating...`;
    btn.disabled = true;
    
    try {
        const res = await fetch(`${API_BASE}/jobs`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify({
                name: document.getElementById('job-name').value,
                target_url: document.getElementById('job-url').value,
                cron_expression: document.getElementById('job-cron').value || null
            })
        });
        
        if (!res.ok) throw new Error((await res.json()).detail || "Failed to create job");
        
        document.getElementById('job-modal').classList.remove('show');
        newJobForm.reset();
        showToast("Job created successfully!");
        
        // Go back to dashboard view
        document.querySelector('.nav-link[data-view="view-dashboard"]').click();
        
        fetchJobs();
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.innerHTML = `Create Job`;
        btn.disabled = false;
    }
});

function formatDate(isoString) {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString(undefined, { 
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
}

newJobBtn.addEventListener('click', () => {
    newJobForm.reset();
    document.getElementById('job-modal').classList.add('show');
});

init();
