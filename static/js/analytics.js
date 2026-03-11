/**
 * analytics.js – loads and renders the Analytics panel.
 */

export function loadAnalytics() {
    const container = document.getElementById('analyticsContent');
    if (!container) return;
    if (container.dataset.loaded === '1') return;

    Promise.all([
        fetch('/api/main_stats/').then(r => r.json()),
        fetch('/api/market_place_names/').then(r => r.json())
    ])
    .then(([stats, markets]) => {
        const totalMarkets = Object.keys(markets).length;
        const totalVariants = Object.values(markets).reduce((sum, arr) => sum + arr.length, 0);
        const rotNum = parseFloat(stats['Rotation Rate']) || 0;
        const hotPct = stats['Total Books'] ? Math.round((stats['Hot Books'] / stats['Total Books']) * 100) : 0;
        const soldPct = stats['Total Books'] ? Math.round((stats['Sold Books'] / stats['Total Books']) * 100) : 0;

        const anCards = [
            { icon:'📚', value:(stats['Total Books']    ||0).toLocaleString(), label:'Total Books',    desc:'All tracked listings',   bg:'#2196F3' },
            { icon:'👥', value:(stats['Unique Sellers'] ||0).toLocaleString(), label:'Unique Sellers', desc:'Distinct vendors',        bg:'#4CAF50' },
            { icon:'💰', value:'€'+Number(stats['Average Price']||0).toFixed(2),label:'Avg Price',    desc:'Average book price',      bg:'#00BCD4' },
            { icon:'🔄', value: stats['Rotation Rate']  ||'0%',                 label:'Rotation Rate', desc:'Inventory turnover rate', bg:'#FFC107' },
            { icon:'🔥', value:(stats['Hot Books']       ||0).toLocaleString(), label:'Hot Books',      desc:'High-demand books',       bg:'#F44336' },
            { icon:'🛒', value:(stats['Sold Books']      ||0).toLocaleString(), label:'Sold Books',     desc:'Books sold',              bg:'#9E9E9E' }
        ];

        container.innerHTML = `
            <div class="an-cards" style="margin-bottom:20px">
                ${anCards.map(c => `
                    <div class="an-stat-card">
                        <div class="an-stat-top" style="background:${c.bg}">
                            <span class="an-stat-icon">${c.icon}</span>
                            <div class="an-stat-value">${c.value}</div>
                        </div>
                        <div class="an-stat-bottom">
                            <div class="an-stat-label">${c.label}</div>
                            <div class="an-stat-desc">${c.desc}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="an-detail-cards">
                <div class="an-card an-card--wide">
                    <div class="an-card-label">Inventory Health</div>
                    <div class="an-bars">
                        <div class="an-bar-row">
                            <span class="an-bar-name">Available</span>
                            <div class="an-bar-track"><div class="an-bar-fill" style="width:${hotPct}%;background:#22c55e"></div></div>
                            <span class="an-bar-val">${hotPct}%</span>
                        </div>
                        <div class="an-bar-row">
                            <span class="an-bar-name">Sold</span>
                            <div class="an-bar-track"><div class="an-bar-fill" style="width:${soldPct}%;background:#e8c97e"></div></div>
                            <span class="an-bar-val">${soldPct}%</span>
                        </div>
                        <div class="an-bar-row">
                            <span class="an-bar-name">Rotation</span>
                            <div class="an-bar-track"><div class="an-bar-fill" style="width:${Math.min(rotNum,100)}%;background:#6366f1"></div></div>
                            <span class="an-bar-val">${rotNum}%</span>
                        </div>
                    </div>
                </div>
                <div class="an-card">
                    <div class="an-card-label">Marketplace Coverage</div>
                    <div style="font-family:'DM Serif Display',serif;font-size:36px;letter-spacing:-1px;color:var(--text-primary);line-height:1">${totalMarkets}</div>
                    <div style="font-size:12px;color:var(--text-muted);margin-top:6px">${totalVariants} total sources</div>
                </div>
                <div class="an-card an-card--wide">
                    <div class="an-card-label">Marketplace Breakdown</div>
                    <div class="an-market-list">
                        ${Object.entries(markets).map(([name, variants]) => `
                            <div class="an-market-row">
                                <span class="an-market-name">${name}</span>
                                <span class="an-market-variants">${variants.length} source${variants.length !== 1 ? 's' : ''}</span>
                                <div class="an-market-dots">
                                    ${variants.map(v => `<span class="an-dot">${v}</span>`).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        container.dataset.loaded = '1';
    })
    .catch(() => {
        container.innerHTML = '<div class="info-tip">Could not load analytics data. Please try again.</div>';
    });
}