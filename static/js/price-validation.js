/**
 * price-validation.js
 * Enforces integer-only input and ensures min < max by auto‑correcting values.
 */

export function validatePrices(changedEl, otherEl) {
    // Remove any non‑digit characters (allow leading minus, but we handle negatives separately)
    changedEl.value = changedEl.value.replace(/[^\d-]/g, '');
    otherEl.value = otherEl.value.replace(/[^\d-]/g, '');

    let changed = parseInt(changedEl.value, 10);
    let other   = parseInt(otherEl.value, 10);

    // Handle empty/invalid
    if (isNaN(changed)) changed = null;
    if (isNaN(other)) other = null;

    // Clamp negatives to 0
    if (changed !== null && changed < 0) {
        changedEl.value = 0;
        changed = 0;
        alert('Negative values are not allowed. Set to 0.');
    }
    if (other !== null && other < 0) {
        otherEl.value = 0;
        other = 0;
        alert('Negative values are not allowed. Set to 0.');
    }

    // Determine which input is min and which is max
    const isMinChanged = changedEl.id === 'minPrice';
    const minEl = isMinChanged ? changedEl : otherEl;
    const maxEl = isMinChanged ? otherEl : changedEl;

    let min = isMinChanged ? changed : other;
    let max = isMinChanged ? other : changed;

    // If both present and min >= max, correct the value that was just changed
    if (min !== null && max !== null && min >= max) {
        if (isMinChanged) {
            // User changed min: set max = min + 1
            max = min + 1;
            maxEl.value = max;
            alert('Minimum must be less than maximum. Maximum adjusted to ' + max + '.');
        } else {
            // User changed max: set min = max - 1 (but not below 0)
            min = Math.max(0, max - 1);
            minEl.value = min;
            alert('Minimum must be less than maximum. Minimum adjusted to ' + min + '.');
        }
    }

    // Visual feedback (red border) – still show if invalid after correction? Actually after correction it's valid.
    minEl.style.borderColor = '';
    maxEl.style.borderColor = '';

    // Store last value for decimal detection (optional)
    changedEl.dataset.lastValue = changedEl.value;
    otherEl.dataset.lastValue = otherEl.value;
}

export function getPriceValues(minEl, maxEl) {
    const min = parseInt(minEl?.value, 10);
    const max = parseInt(maxEl?.value, 10);
    const hasMin = !Number.isNaN(min) && min >= 0;
    const hasMax = !Number.isNaN(max) && max >= 0;

    // If both present, ensure min < max (should be already enforced)
    if (hasMin && hasMax && min >= max) return null;

    const out = {};
    if (hasMin) out.min = min;
    if (hasMax) out.max = max;
    return Object.keys(out).length ? out : null;
}

export function setupPriceValidation(onPriceChange, debounceFn) {
    const minEl = document.getElementById('minPrice');
    const maxEl = document.getElementById('maxPrice');
    if (!minEl || !maxEl) return;

    const debouncedReload = debounceFn(() => {
        const prices = getPriceValues(minEl, maxEl);
        if (prices !== null || (minEl.value === '' && maxEl.value === '')) {
            onPriceChange();
        }
    }, 400);

    minEl.addEventListener('input', () => {
        validatePrices(minEl, maxEl);
        debouncedReload();
    });

    maxEl.addEventListener('input', () => {
        validatePrices(maxEl, minEl);
        debouncedReload();
    });
}