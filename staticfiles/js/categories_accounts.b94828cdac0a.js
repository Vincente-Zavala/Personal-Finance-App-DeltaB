// categories_accounts.js

export let CATEGORY_TYPES = [];
export let ACCOUNTS = [];

// -------------------------
// LOADERS
// -------------------------
export function loadCategories() {
    if (typeof CATEGORIES_API_URL === "undefined") return Promise.resolve();

    return fetch(CATEGORIES_API_URL, { credentials: "same-origin" })
        .then(res => res.json())
        .then(data => {
            CATEGORY_TYPES = data.category_types || [];
        });
}

export function loadAccounts() {
    if (typeof ACCOUNTS_API_URL === "undefined") return Promise.resolve();

    return fetch(ACCOUNTS_API_URL, { credentials: "same-origin" })
        .then(res => res.json())
        .then(data => {
            ACCOUNTS = data.accounts || [];
        });
}

// -------------------------
// BUILD TYPE SELECT (SHARED)
// -------------------------
export function buildTypeSelect(tx) {
    const select = document.createElement("select");
    select.className = "form-select form-select-sm rounded-pill type-select";
    select.name = `typechoice_${tx.id}`;
    select.dataset.transactionId = tx.id;

    select.innerHTML = `<option value="">Select Type...</option>`;

    CATEGORY_TYPES.forEach(ct => {
        const option = document.createElement("option");
        option.value = ct.name;
        option.textContent = ct.name;
        if (ct.name === tx.type_name) option.selected = true;
        select.appendChild(option);
    });

    return select;
}

// -------------------------
// BUILD CATEGORY SELECT (SHARED)
// -------------------------
export function buildCategorySelect(tx, type = null) {
    const select = document.createElement("select");
    select.className = "form-select form-select-sm rounded-pill category-select";
    select.name = `categorychoice_${tx.id}`;
    select.dataset.transactionId = tx.id;

    if (!type) select.style.display = "none";

    select.innerHTML = `<option value="">Select Category...</option>`;

    CATEGORY_TYPES.forEach(ct => {
        if (!type || ct.name.toLowerCase() !== type.toLowerCase()) return;

        ct.categories.forEach(cat => {
            const option = document.createElement("option");
            option.value = cat.id;
            option.textContent = cat.name;
            option.dataset.categorytype = ct.type;

            if (cat.name === tx.category_name) option.selected = true;
            select.appendChild(option);
        });
    });

    return select;
}
