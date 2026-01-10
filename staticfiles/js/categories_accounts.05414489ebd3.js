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

// // -------------------------
// // BUILD TYPE SELECT (SHARED)
// // -------------------------
// export function buildTypeSelect(tx) {
//     const select = document.createElement("select");
//     select.className = "form-select form-select-sm rounded-pill type-select";
//     select.name = `typechoice_${tx.id}`;
//     select.dataset.transactionId = tx.id;

//     select.innerHTML = `<option value="">Select Type...</option>`;

//     CATEGORY_TYPES.forEach(ct => {
//         const option = document.createElement("option");
//         option.value = ct.name;
//         option.textContent = ct.name;
//         if (ct.name === tx.type_name) option.selected = true;
//         select.appendChild(option);
//     });

//     return select;
// }

// // -------------------------
// // BUILD CATEGORY SELECT (SHARED)
// // -------------------------
// export function buildCategorySelect(tx, type = null) {
//     const select = document.createElement("select");
//     select.className = "form-select form-select-sm rounded-pill category-select";
//     select.name = `categorychoice_${tx.id}`;
//     select.dataset.transactionId = tx.id;

//     if (!type) select.style.display = "none";

//     select.innerHTML = `<option value="">Select Category...</option>`;

//     CATEGORY_TYPES.forEach(ct => {
//         if (!type || ct.name.toLowerCase() !== type.toLowerCase()) return;

//         ct.categories.forEach(cat => {
//             const option = document.createElement("option");
//             option.value = cat.id;
//             option.textContent = cat.name;
//             option.dataset.categorytype = ct.type;

//             if (cat.name === tx.category_name) option.selected = true;
//             select.appendChild(option);
//         });
//     });

//     return select;
// }


// Build Type Select
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

    // Attach the change listener directly here
    select.addEventListener("change", function () {
        const row = select.closest(".transaction-row");
        if (!row) return;
        const categorySelect = row.querySelector('.category-select');
        
        // Update category options based on the selected type
        updateCategorySelectOptions(categorySelect, select.value);
    });

    return select;
}

// Build Category Select (initial)
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

// Update Category Options based on Type Change
function updateCategorySelectOptions(categorySelect, selectedType) {
    if (!categorySelect) return;

    // Clear existing options
    categorySelect.innerHTML = `<option value="">Select Category...</option>`;

    CATEGORY_TYPES.forEach(ct => {
        if (ct.name.toLowerCase() !== selectedType.toLowerCase()) return;

        ct.categories.forEach(cat => {
            const option = document.createElement("option");
            option.value = cat.id;
            option.textContent = cat.name;
            option.dataset.categorytype = ct.type;
            categorySelect.appendChild(option);
        });
    });
}

// Inside the edit button handler (edited part)
if (editBtn) {
    const row = editBtn.closest(".transaction-row");
    if (!row) return;

    const inputs = row.querySelectorAll(".tx-input");
    const displays = row.querySelectorAll(".tx-display");
    const buttons = row.querySelectorAll(".tx-cancel, .tx-check");
    const editButton = row.querySelector(".edit-tx");

    // Close any other row in edit mode
    document.querySelectorAll(".transaction-row").forEach(r => {
        if (r !== row && r.dataset.editing === "true") {
            r.querySelectorAll(".tx-input").forEach(i => i.classList.add("d-none"));
            r.querySelectorAll(".tx-display").forEach(d => d.classList.remove("d-none"));
            r.querySelectorAll(".tx-cancel .tx-check").forEach(b => b.classList.add("d-none"));
            r.querySelector(".edit-tx")?.classList.remove("d-none");
            r.dataset.editing = "false";
        }
    });

    // Enter edit mode
    inputs.forEach(i => i.classList.remove("d-none"));
    displays.forEach(d => d.classList.add("d-none"));
    buttons.forEach(b => b.classList.remove("d-none"));
    if (editButton) editButton.classList.add("d-none");

    const originalData = {};
    inputs.forEach(input => {
        input.dataset.originalValue = input.value;
    });

    // Handle type → category dependency
    const typeSelect = row.querySelector('select[name="type"]');
    let categorySelect = row.querySelector('select[name="category"]');

    // Update the category options when type changes
    typeSelect.addEventListener("change", () => {
        const selectedType = typeSelect.value;
        const currentCategoryOriginal = categorySelect.value;

        // Update the category select options based on the new type
        updateCategorySelectOptions(categorySelect, selectedType);

        // Preserve original value after update
        categorySelect.value = currentCategoryOriginal;
    });

    row.dataset.editing = "true";
    return; // stop here
}

