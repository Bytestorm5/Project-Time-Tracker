// Global state
let projectsData = [];
let timerInterval = null;
let chart = null;

// Tabs and initial load
window.addEventListener('pywebviewready', () => {
    // Tab navigation
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    // Project form
    document.getElementById('add-project-form').addEventListener('submit', addProject);
    // Timer controls
    document.getElementById('clock-in').addEventListener('click', clockIn);
    document.getElementById('clock-out').addEventListener('click', clockOut);
    // Milestone form
    document.getElementById('add-milestone-form').addEventListener('submit', addMilestone);
    // On project select change, load milestones
    document.getElementById('project-select').addEventListener('change', () => {
        const pid = document.getElementById('project-select').value;
        loadMilestones(pid);
    });
    // Start with Projects tab
    loadProjects();
});

function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === tabId));
    if (tabId === 'projects-tab') loadProjects();
    else if (tabId === 'timer-tab') loadTimer();
    else if (tabId === 'analytics-tab') loadAnalytics();
}

// Projects functions
function loadProjects() {
    window.pywebview.api.get_projects().then(projects => {
        projectsData = projects;
        const list = document.getElementById('project-list');
        list.innerHTML = '';
        projects.forEach(p => {
            const li = document.createElement('li');
            li.dataset.id = p._id;
            li.innerHTML = `
                <span>${p.title}</span> ${p.public ? '(Public)' : ''}
                <button class="edit">Edit</button>
                <button class="delete">Delete</button>
                <div class="edit-form" style="display:none; margin-top:5px;">
                  <input type="text" class="edit-title" value="${p.title}" placeholder="Title" />
                  <input type="text" class="edit-description" value="${p.description}" placeholder="Description" />
                  <label><input type="checkbox" class="edit-public" ${p.public?'checked':''}/> Public</label>
                  <button class="save">Save</button>
                  <button class="cancel">Cancel</button>
                </div>
            `;
            list.appendChild(li);
            // Bind events
            li.querySelector('.edit').addEventListener('click', () => {
                li.querySelector('.edit-form').style.display = 'block';
            });
            li.querySelector('.cancel').addEventListener('click', () => {
                li.querySelector('.edit-form').style.display = 'none';
            });
            li.querySelector('.save').addEventListener('click', () => {
                const title = li.querySelector('.edit-title').value.trim();
                const desc = li.querySelector('.edit-description').value.trim();
                const pub = li.querySelector('.edit-public').checked;
                if (!title) return alert('Title is required');
                window.pywebview.api.edit_project(li.dataset.id, title, desc, pub).then(res => {
                    if (res.error) alert(res.error);
                    else loadProjects();
                });
            });
            li.querySelector('.delete').addEventListener('click', () => {
                if (confirm('Delete project?')) {
                    window.pywebview.api.delete_project(li.dataset.id).then(res => {
                        if (res.error) alert(res.error);
                        else loadProjects();
                    });
                }
            });
        });
    });
}

function addProject(e) {
    e.preventDefault();
    const title = document.getElementById('title').value.trim();
    const desc = document.getElementById('description').value.trim();
    const pub = document.getElementById('public').checked;
    if (!title) return alert('Title is required');
    window.pywebview.api.add_project(title, desc, pub).then(res => {
        if (res.error) alert(res.error);
        else {
            document.getElementById('add-project-form').reset();
            loadProjects();
        }
    });
}

// Timer and Milestones
function loadTimer() {
    if (timerInterval) clearInterval(timerInterval);
    window.pywebview.api.get_projects().then(projects => {
        projectsData = projects;
        const select = document.getElementById('project-select');
        select.innerHTML = '';
        projects.forEach(p => {
            const o = document.createElement('option'); o.value = p._id; o.textContent = p.title;
            select.appendChild(o);
        });
        window.pywebview.api.get_active_entry().then(entry => {
            const controls = document.getElementById('timer-controls');
            const status = document.getElementById('timer-status');
            if (entry) {
                controls.style.display = 'none'; status.style.display = 'block';
                const proj = projectsData.find(x => x._id === entry.project_id);
                document.getElementById('timer-project-title').textContent = (proj?proj.title:'') + ': ';
                const start = new Date(entry.start_time);
                function tick() {
                    const d = Date.now() - start.getTime();
                    const h = Math.floor(d / 3600000);
                    const m = Math.floor((d % 3600000) / 60000);
                    const s = Math.floor((d % 60000) / 1000);
                    document.getElementById('live-timer').textContent = `${h}h ${m}m ${s}s`;
                }
                tick(); timerInterval = setInterval(tick, 1000);
            } else {
                controls.style.display = 'block'; status.style.display = 'none';
            }
        }).finally(() => {
            const pid = document.getElementById('project-select').value;
            loadMilestones(pid);
        });
    });
}

function clockIn() {
    const pid = document.getElementById('project-select').value;
    if (!pid) return alert('Select a project');
    window.pywebview.api.clock_in(pid).then(res => {
        if (res.error) alert(res.error);
        else loadTimer();
    });
}

// Clock out the active entry (ignores project-select to avoid mismatch)
function clockOut() {
    window.pywebview.api.get_active_entry().then(entry => {
        if (!entry) return alert('No active entry to clock out');
        window.pywebview.api.clock_out(entry.project_id).then(res => {
            if (res.error) alert(res.error);
            else {
                if (timerInterval) clearInterval(timerInterval);
                loadTimer();
            }
        });
    });
}

// Milestone functions
function loadMilestones(projectId) {
    const container = document.getElementById('milestones-list');
    if (!projectId) { container.innerHTML = ''; return; }
    window.pywebview.api.get_milestones(projectId).then(list => {
        container.innerHTML = '';
        list.forEach(ms => {
            const li = document.createElement('li'); li.dataset.id = ms._id;
            li.innerHTML = `
                <div class="milestone-view">
                    <strong>${ms.title}</strong> (${ms.significance})<br/>
                    ${new Date(ms.timestamp).toLocaleString()} ${ms.public ? '(Public)' : ''}
                    <button class="edit-ms">Edit</button>
                    <button class="delete-ms">Delete</button>
                </div>
                <div class="milestone-edit-form" style="display:none; margin-top:5px;">
                    <input type="text" class="edit-ms-title" value="${ms.title}" />
                    <input type="text" class="edit-ms-description" value="${ms.description}" />
                    <select class="edit-ms-significance">
                        <option value="Landmark"${ms.significance==='Landmark'?' selected':''}>Landmark</option>
                        <option value="Major"${ms.significance==='Major'?' selected':''}>Major</option>
                        <option value="Incremental"${ms.significance==='Incremental'?' selected':''}>Incremental</option>
                    </select>
                    <label><input type="checkbox" class="edit-ms-public"${ms.public?' checked':''}/> Public</label>
                    <button class="save-ms">Save</button>
                    <button class="cancel-ms">Cancel</button>
                </div>
            `;
            container.appendChild(li);
            li.querySelector('.edit-ms').addEventListener('click', () => li.querySelector('.milestone-edit-form').style.display = 'block');
            li.querySelector('.cancel-ms').addEventListener('click', () => li.querySelector('.milestone-edit-form').style.display = 'none');
            li.querySelector('.save-ms').addEventListener('click', () => {
                const title = li.querySelector('.edit-ms-title').value.trim();
                const desc = li.querySelector('.edit-ms-description').value.trim();
                const sign = li.querySelector('.edit-ms-significance').value;
                const pub = li.querySelector('.edit-ms-public').checked;
                if (!title) return alert('Title is required');
                window.pywebview.api.edit_milestone(li.dataset.id, title, desc, pub, sign).then(res => {
                    if (res.error) alert(res.error);
                    else loadMilestones(projectId);
                });
            });
            li.querySelector('.delete-ms').addEventListener('click', () => {
                if (confirm('Delete milestone?')) window.pywebview.api.delete_milestone(li.dataset.id).then(res => {
                    if (res.error) alert(res.error);
                    else loadMilestones(projectId);
                });
            });
        });
    });
}

function addMilestone(e) {
    e.preventDefault();
    const pid = document.getElementById('project-select').value;
    const title = document.getElementById('ms-title').value.trim();
    const desc = document.getElementById('ms-description').value.trim();
    const sign = document.getElementById('ms-significance').value;
    const pub = document.getElementById('ms-public').checked;
    if (!pid) return alert('Select a project');
    if (!title) return alert('Title is required');
    window.pywebview.api.add_milestone(pid, title, desc, pub, sign).then(res => {
        if (res.error) alert(res.error);
        else {
            document.getElementById('add-milestone-form').reset();
            loadMilestones(pid);
        }
    });
}
// Analytics: stacked daily hours per project
function loadAnalytics() {
    window.pywebview.api.get_daily_analytics().then(data => {
        const daysSet = new Set();
        const projectsMap = {};
        data.forEach(item => {
            daysSet.add(item.day);
            if (!projectsMap[item.project_id]) {
                projectsMap[item.project_id] = { title: item.title, data: {} };
            }
            projectsMap[item.project_id].data[item.day] = parseFloat(item.total_hours.toFixed(2));
        });
        const days = Array.from(daysSet).sort();
        const datasets = [];
        const colorPalette = [
            'rgba(75, 192, 192, 0.6)',
            'rgba(255, 99, 132, 0.6)',
            'rgba(255, 205, 86, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(201, 203, 207, 0.6)'
        ];
        let colorIndex = 0;
        Object.values(projectsMap).forEach(proj => {
            const dataPoints = days.map(day => proj.data[day] || 0);
            const bgColor = colorPalette[colorIndex % colorPalette.length];
            datasets.push({
                label: proj.title,
                data: dataPoints,
                backgroundColor: bgColor,
                borderColor: bgColor.replace('0.6', '1'),
                borderWidth: 1
            });
            colorIndex++;
        });
        const ctx = document.getElementById('analytics-chart').getContext('2d');
        if (chart) {
            chart.data.labels = days;
            chart.data.datasets = datasets;
            chart.update();
        } else {
            chart = new Chart(ctx, {
                type: 'bar',
                data: { labels: days, datasets: datasets },
                options: {
                    responsive: true,
                    plugins: {
                        tooltip: { mode: 'index', intersect: false, callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.formattedValue} h` } }
                    },
                    scales: {
                        x: { stacked: true },
                        y: { stacked: true, beginAtZero: true, title: { display: true, text: 'Hours' } }
                    }
                }
            });
        }
    });
}