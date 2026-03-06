export function loadStatistics() {
    const container = document.getElementById('statsContainer');
    if (!container) return;

    fetch('/api/main_stats/')
        .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(renderStatistics)
        .catch(() => {
            if (container) container.innerHTML = `
                <div style="grid-column:1/-1">
                    <div class="alert alert-warning">Could not load statistics. Please try again.</div>
                </div>`;
        });
}

function renderStatistics(stats) {
    const container = document.getElementById('statsContainer');
    if (!container) return;

    const cards = [
        { icon: '📚', value: (stats['Total Books']    ?? 0).toLocaleString(),      label: 'Total Books',    desc: 'Total books in the system', bg: '#2196F3' },
        { icon: '👥', value: (stats['Unique Sellers'] ?? 0).toLocaleString(),      label: 'Unique Sellers', desc: 'Distinct sellers',           bg: '#4CAF50' },
        { icon: '💰', value: `€${Number(stats['Average Price'] ?? 0).toFixed(2)}`, label: 'Average Price',  desc: 'Average book price',         bg: '#00BCD4' },
        { icon: '🔄', value:  stats['Rotation Rate']  ?? '0 %',                    label: 'Rotation Rate',  desc: 'Inventory turnover rate',    bg: '#FFC107' },
        { icon: '🔥', value: (stats['Hot Books']       ?? 0).toLocaleString(),      label: 'Hot Books',      desc: 'Currently available',        bg: '#F44336' },
        { icon: '🛒', value: (stats['Sold Books']      ?? 0).toLocaleString(),      label: 'Sold Books',     desc: 'Books sold',                 bg: '#9E9E9E' },
    ];

    container.innerHTML = cards.map(c => `
        <div class="stat-card">
            <div class="stat-card-top" style="background:${c.bg}">
                <span class="stat-card-icon">${c.icon}</span>
                <div class="stat-card-value">${c.value}</div>
            </div>
            <div class="stat-card-bottom">
                <div class="stat-card-label">${c.label}</div>
                <div class="stat-card-desc">${c.desc}</div>
            </div>
        </div>
    `).join('');
}