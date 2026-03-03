/**
 * dashboard.js – main entry point
 */

import { renderResults } from './renderResults.js';
import { loadStatistics } from './statistics.js';
import { loadAnalytics } from './analytics.js';
import { validatePrices, getPriceValues, setupPriceValidation } from './price-validation.js';

function debounce(fn, wait = 300) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
}

document.addEventListener('DOMContentLoaded', () => {
    window.openGroups = new Set();

    setupPanelSwitching();

    loadStatistics();
    loadMarketplaces();
    loadPriceRange();
    loadConditions();

    setupPriceValidation(loadConditions, debounce);
    setupDaysFilter();

    // Ensure mutual exclusivity of interest filters
    const showCb = document.getElementById('showInterested');
    const hideCb = document.getElementById('hideNotInterested');
    if (showCb && hideCb) {
        showCb.addEventListener('change', function() {
            if (this.checked) hideCb.checked = false;
            applyFilters();
        });
        hideCb.addEventListener('change', function() {
            if (this.checked) showCb.checked = false;
            renderFilteredResults(); // hide is client-side
        });
    }

    document.getElementById('showContact')?.addEventListener('change', applyFilters);
    document.getElementById('resetFiltersBtn')?.addEventListener('click', resetFilters);

    wireApplyFiltersButton();
    invokeApplyFiltersWhenReady();

    // Delegate clicks
    document.getElementById('resultsContainer')?.addEventListener('click', (e) => {
        const btn = e.target.closest('.star-btn, .not-interested-btn, .contact-btn');
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();
        if (btn.classList.contains('star-btn')) window.handleStarClick(btn);
        if (btn.classList.contains('not-interested-btn')) window.handleNotInterestedClick(btn);
        if (btn.classList.contains('contact-btn')) window.handleContactClick(btn);
    });

    const dateEl = document.getElementById('currentDate');
    if (dateEl) {
        dateEl.textContent = new Date().toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'numeric' });
    }
});

function setupPanelSwitching() {
    document.querySelectorAll('.nav-item[data-panel]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchPanel(item.dataset.panel);
        });
    });

    document.getElementById('hamburgerBtn')?.addEventListener('click', openSidebar);
    document.getElementById('sidebarClose')?.addEventListener('click', closeSidebar);
    document.getElementById('sidebarOverlay')?.addEventListener('click', closeSidebar);
}

function switchPanel(name) {
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById(`panel-${name}`);
    if (panel) panel.classList.add('active');

    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`.nav-item[data-panel="${name}"]`)?.classList.add('active');

    const titles = {
        dashboard: ['Market Dashboard',  'Real-time book market intelligence'],
        books:     ['Books Explorer',    'Browse all tracked listings'],
        analytics: ['Analytics',         'Market trends & seller insights']
    };
    const pageTitle = document.getElementById('pageTitle');
    const pageSubtitle = document.getElementById('pageSubtitle');
    if (titles[name]) {
        if (pageTitle) pageTitle.textContent = titles[name][0];
        if (pageSubtitle) pageSubtitle.textContent = titles[name][1];
    }

    if (name === 'analytics') loadAnalytics();

    closeSidebar();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function openSidebar() {
    document.getElementById('sidebar')?.classList.add('open');
    document.getElementById('sidebarOverlay')?.classList.add('active');
    document.body.style.overflow = 'hidden';
}
function closeSidebar() {
    document.getElementById('sidebar')?.classList.remove('open');
    document.getElementById('sidebarOverlay')?.classList.remove('active');
    document.body.style.overflow = '';
}

function setupDaysFilter() {
    const container = document.getElementById('daysFilter');
    const hidden    = document.getElementById('daysOld');
    if (!container || !hidden) return;
    if (container.dataset.bound === '1') return;
    container.dataset.bound = '1';

    const setActive = (btn) => {
        container.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        hidden.value = btn.dataset.days;
    };

    const initVal = hidden.value || '30';
    const initBtn = container.querySelector(`.day-btn[data-days="${initVal}"]`)
                 || container.querySelector('.day-btn');
    if (initBtn) setActive(initBtn);

    container.addEventListener('click', (e) => {
        const btn = e.target.closest('.day-btn');
        if (!btn) return;
        setActive(btn);
        applyFilters();
    });
}

function wireApplyFiltersButton() {
    const attach = () => {
        const btn = document.getElementById('applyFiltersBtn');
        if (!btn || btn.dataset.bound === '1') return !!btn;
        btn.addEventListener('click', (e) => { e.preventDefault(); applyFilters(); });
        btn.dataset.bound = '1';
        return true;
    };
    if (attach()) return;
    const obs = new MutationObserver(() => { if (attach()) obs.disconnect(); });
    obs.observe(document.body, { childList: true, subtree: true });
}

function invokeApplyFiltersWhenReady() {
    if (typeof applyFilters === 'function') { applyFilters(); return; }
    let attempts = 0;
    const t = setInterval(() => {
        if (typeof applyFilters === 'function' || ++attempts >= 50) {
            clearInterval(t);
            if (typeof applyFilters === 'function') applyFilters();
        }
    }, 100);
}

async function loadMarketplaces() {
    try {
        const res  = await fetch('/api/market_place_names/');
        const data = await res.json();
        const container = document.getElementById('marketplaceContainer');
        container.innerHTML = '';

        let hidden = document.getElementById('marketplace');
        if (!hidden) {
            hidden = document.createElement('input');
            hidden.type = 'hidden'; hidden.id = 'marketplace'; hidden.name = 'marketplace';
            container.parentElement.appendChild(hidden);
        }

        const state = new Map();
        const updateHidden = () => {
            const items = [];
            state.forEach((arr, key) => arr.forEach(v => items.push(`${key}_${v}`)));
            hidden.value = items.join(',');
            loadConditions();
        };

        Object.entries(data).forEach(([marketplace, variants]) => {
            const card = document.createElement('div');
            card.className = 'd-flex flex-column p-2 border rounded';

            const header = document.createElement('div');
            header.className = 'fw-semibold cursor-pointer';
            header.textContent = marketplace;

            const panel = document.createElement('div');
            panel.style.display = 'none';
            panel.className = 'mt-2';

            const cbs = [];
            (variants || []).forEach(v => {
                const wrap = document.createElement('div');
                wrap.className = 'form-check';
                const cb = document.createElement('input');
                cb.type = 'checkbox'; cb.className = 'form-check-input'; cb.value = v;
                const lbl = document.createElement('label');
                lbl.className = 'form-check-label'; lbl.textContent = v;
                wrap.append(cb, lbl); panel.appendChild(wrap); cbs.push(cb);
            });

            header.addEventListener('click', () => {
                panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            });
            cbs.forEach(cb => cb.addEventListener('change', () => {
                const selected = cbs.filter(x => x.checked).map(x => x.value);
                selected.length ? state.set(marketplace, selected) : state.delete(marketplace);
                updateHidden();
            }));

            card.append(header, panel);
            container.appendChild(card);
        });

        updateHidden();
    } catch(e) {
        console.error('loadMarketplaces error:', e);
    }
}

async function loadPriceRange() {
    try {
        const res  = await fetch('/api/price_range_of_books/');
        const data = await res.json();
        const minEl = document.getElementById('minPrice');
        const maxEl = document.getElementById('maxPrice');
        if (minEl && !minEl.value) minEl.value = data.min_price ?? '';
        if (maxEl && !maxEl.value) maxEl.value = data.max_price ?? '';
    } catch(e) {
        console.error('loadPriceRange error:', e);
    }
}

async function loadConditions() {
    const minEl = document.getElementById('minPrice');
    const maxEl = document.getElementById('maxPrice');
    const marketHidden = document.getElementById('marketplace');
    const params = new URLSearchParams();

    if (marketHidden?.value) params.set('domains', marketHidden.value);
    const prices = getPriceValues(minEl, maxEl);
    if (prices?.min !== undefined) params.set('min_price', prices.min);
    if (prices?.max !== undefined) params.set('max_price', prices.max);

    try {
        const url = `/api/conditions_of_books/${params.toString() ? '?' + params : ''}`;
        const res = await fetch(url);
        populateConditions(await res.json());
    } catch {
        populateConditions([]);
    }
}

function populateConditions(list) {
    const select = document.getElementById('condition');
    if (!select) return;
    const current = select.value;
    select.innerHTML = '<option value="">All Conditions</option>';
    list.filter(c => c !== 'All').forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.textContent = c;
        if (c === current) opt.selected = true;
        select.appendChild(opt);
    });
}

// Star handler
function handleStarClick(btn) {
    const detailId = parseInt(btn.dataset.detailId, 10);
    const current  = btn.dataset.interest || 'pending';
    // Toggle between interested and pending (never set to not_interested)
    const next = current === 'interested' ? 'pending' : 'interested';

    if (!detailId) return;

    // Optimistic update
    btn.dataset.interest = next;
    updateStarButton(btn, next);
    btn.disabled = true;

    // Also update the corresponding not-interested button (in the same card)
    const card = btn.closest('a');
    const notInterestedBtn = card?.querySelector('.not-interested-btn');
    if (notInterestedBtn && next === 'interested') {
        // If we just set interested, ensure not-interested is reset to pending
        notInterestedBtn.dataset.interest = 'pending';
        updateNotInterestedButton(notInterestedBtn, 'pending');
    }

    fetch(`/api/interest/${detailId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ interest: next })
    })
    .then(res => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    })
    .then(() => {
        if (window.lastResultsData) {
            window.lastResultsData.forEach(group => {
                (group.results || []).forEach(item => {
                    if (item.detail_id === detailId) item.interest = next;
                });
            });
        }
        if (filtersActive()) renderFilteredResults();
        else updateInterestedBadge();
        btn.disabled = false;
    })
    .catch(err => {
        console.error('Star update failed:', err);
        btn.dataset.interest = current;
        updateStarButton(btn, current);
        btn.disabled = false;
    });
}

function updateStarButton(btn, interest) {
    const isInterested = interest === 'interested';
    btn.innerHTML = isInterested ? '★' : '☆';
    btn.classList.remove('star-filled', 'star-outline');
    btn.classList.add(isInterested ? 'star-filled' : 'star-outline');
    btn.title = isInterested ? 'Mark as Not Interested' : 'Mark as Interested';
    btn.dataset.interest = interest;
}

// Not Interested handler
function handleNotInterestedClick(btn) {
    const detailId = parseInt(btn.dataset.detailId, 10);
    const current  = btn.dataset.interest || 'pending';
    // Toggle between not_interested and pending (never set to interested)
    const next = current === 'not_interested' ? 'pending' : 'not_interested';

    if (!detailId) return;

    btn.dataset.interest = next;
    updateNotInterestedButton(btn, next);
    btn.disabled = true;

    const card = btn.closest('a');
    const starBtn = card?.querySelector('.star-btn');
    if (starBtn && next === 'not_interested') {
        // If we just set not_interested, reset star to outline
        starBtn.dataset.interest = 'pending';
        updateStarButton(starBtn, 'pending');
    }

    fetch(`/api/interest/${detailId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ interest: next })
    })
    .then(res => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    })
    .then(() => {
        if (window.lastResultsData) {
            window.lastResultsData.forEach(group => {
                (group.results || []).forEach(item => {
                    if (item.detail_id === detailId) item.interest = next;
                });
            });
        }
        if (filtersActive()) renderFilteredResults();
        else updateInterestedBadge();
        btn.disabled = false;
    })
    .catch(err => {
        console.error('Not Interested update failed:', err);
        btn.dataset.interest = current;
        updateNotInterestedButton(btn, current);
        btn.disabled = false;
    });
}

function updateNotInterestedButton(btn, interest) {
    const isNotInterested = interest === 'not_interested';
    btn.classList.remove('not-interested-active', 'not-interested-inactive');
    btn.classList.add(isNotInterested ? 'not-interested-active' : 'not-interested-inactive');
    btn.title = isNotInterested ? 'Reset to Pending' : 'Mark as Not Interested';
    btn.dataset.interest = interest;
    // Text stays "Not Interested"
}

function handleContactClick(btn) {
    const detailId = parseInt(btn.dataset.detailId, 10);
    const current  = btn.dataset.contact === 'true';
    const next     = !current;

    if (!detailId) return;

    btn.dataset.contact = next;
    btn.classList.remove('contact-true', 'contact-false');
    btn.classList.add('contact-btn', next ? 'contact-true' : 'contact-false');
    btn.innerHTML = next ? '📞' : '✆';
    btn.title = next ? 'Contacted' : 'Mark as contacted';
    btn.disabled = true;

    fetch(`/api/contact/${detailId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ contact: next })
    })
    .then(res => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    })
    .then(() => {
        if (window.lastResultsData) {
            window.lastResultsData.forEach(group => {
                (group.results || []).forEach(item => {
                    if (item.detail_id === detailId) item.contact = next;
                });
            });
        }
        btn.disabled = false;
    })
    .catch(err => {
        console.error('Contact update failed:', err);
        btn.dataset.contact = current;
        btn.classList.remove('contact-true', 'contact-false');
        btn.classList.add('contact-btn', current ? 'contact-true' : 'contact-false');
        btn.innerHTML = current ? '📞' : '✆';
        btn.title = current ? 'Contacted' : 'Mark as contacted';
        btn.disabled = false;
    });
}

function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

function updateInterestedBadge() {
    let interested = 0;
    if (window.lastResultsData) {
        window.lastResultsData.forEach(g => {
            (g.results || []).forEach(item => {
                if (item.interest === 'interested') interested++;
            });
        });
    }
    const badge = document.getElementById('interestedCount');
    if (badge) { badge.textContent = interested; badge.style.display = interested ? 'inline-flex' : 'none'; }
}

function filtersActive() {
    const showInterested = document.getElementById('showInterested')?.checked;
    const hideNotInterested = document.getElementById('hideNotInterested')?.checked;
    const showContact = document.getElementById('showContact')?.checked;
    return showInterested || hideNotInterested || showContact;
}

function renderFilteredResults() {
    if (!window.lastResultsData) return;

    const showInterested = document.getElementById('showInterested')?.checked;
    const hideNotInterested = document.getElementById('hideNotInterested')?.checked;
    const showContact = document.getElementById('showContact')?.checked;

    let dataToRender = window.lastResultsData;

    dataToRender = window.lastResultsData
        .map(group => {
            let filtered = group.results || [];
            if (showInterested) {
                filtered = filtered.filter(item => item.interest === 'interested');
            }
            if (hideNotInterested) {
                filtered = filtered.filter(item => item.interest === 'not_interested');
            }
            if (showContact) {
                filtered = filtered.filter(item => item.contact === true);
            }
            return filtered.length ? { ...group, results: filtered } : null;
        })
        .filter(Boolean);

    const totalItems = dataToRender.reduce((acc, g) => acc + (g.results?.length || 0), 0);
    const countEl = document.getElementById('resultsCount');
    if (countEl) countEl.textContent = totalItems ? `${totalItems} listing${totalItems !== 1 ? 's' : ''}` : '';

    updateInterestedBadge();

    renderResults(dataToRender);
}

export function applyFilters() {
    const params = new URLSearchParams();

    const marketplace   = document.getElementById('marketplace')?.value;
    const minPrice      = document.getElementById('minPrice')?.value;
    const maxPrice      = document.getElementById('maxPrice')?.value;
    const condition     = document.getElementById('condition')?.value;
    const groupBy       = document.getElementById('groupBy')?.value || 'isbn';
    const days          = document.getElementById('daysOld')?.value;
    const showInterested = document.getElementById('showInterested')?.checked;
    const showContact   = document.getElementById('showContact')?.checked;

    if (marketplace)  params.append('domains',   marketplace);
    if (minPrice)     params.append('min_price',  minPrice);
    if (maxPrice)     params.append('max_price',  maxPrice);
    if (condition)    params.append('condition',  condition);
    if (groupBy)      params.append('group_by',   groupBy);
    if (days && days !== 'all' && !isNaN(parseInt(days, 10))) {
        params.append('days_old', days);
    }
    if (showInterested) {
        params.append('interest', 'interested');
    }
    if (showContact) {
        params.append('contact', 'true');
    }

    const container = document.getElementById('resultsContainer');
    if (container) {
        container.innerHTML = `
            <div style="display:flex;align-items:center;gap:10px;color:#9e9e9e;padding:32px 0">
                <div class="spinner"></div>
                <span>Loading results…</span>
            </div>`;
    }

    fetch(`/api/all_filtered_results/?${params.toString()}`)
        .then(res => { if (!res.ok) throw new Error(res.status); return res.json(); })
        .then(data => {
            window.lastResultsData = data;
            renderFilteredResults();
        })
        .catch(err => {
            console.error('Error fetching filtered results:', err);
            if (container) {
                container.innerHTML = `<div class="alert alert-warning">Could not load results. Please try again.</div>`;
            }
        });
}

function resetFilters() {
    document.getElementById('minPrice').value = '';
    document.getElementById('maxPrice').value = '';
    document.getElementById('minPrice').style.borderColor = '';
    document.getElementById('maxPrice').style.borderColor = '';
    document.getElementById('condition').value = '';
    document.getElementById('groupBy').value = 'isbn';
    document.getElementById('daysOld').value = '30';
    document.getElementById('marketplace').value = '';

    document.getElementById('showInterested').checked = false;
    document.getElementById('hideNotInterested').checked = false;
    document.getElementById('showContact').checked = false;
    document.querySelectorAll('#marketplaceContainer input[type="checkbox"]').forEach(cb => cb.checked = false);

    document.querySelectorAll('.day-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.days === '30');
    });

    applyFilters();
}

// Expose globally
window.handleStarClick = handleStarClick;
window.handleNotInterestedClick = handleNotInterestedClick;
window.handleContactClick = handleContactClick;
window.applyFilters = applyFilters;
window.switchPanel = switchPanel;