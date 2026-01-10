export let CATEGORY_TYPES = [];
export let ACCOUNTS = [];

// Load categories and cache globally
export function loadCategories() {
    if (typeof CATEGORIES_API_URL === "undefined") return Promise.resolve();
    return fetch(CATEGORIES_API_URL, { credentials: "same-origin" })
        .then(res => res.json())
        .then(data => { CATEGORY_TYPES = data.category_types || []; });
}

// Load accounts and cache globally
export function loadAccounts() {
    if (typeof ACCOUNTS_API_URL === "undefined") return Promise.resolve();
    return fetch(ACCOUNTS_API_URL, { credentials: "same-origin" })
        .then(res => res.json())
        .then(data => { ACCOUNTS = data.accounts || []; });
}
