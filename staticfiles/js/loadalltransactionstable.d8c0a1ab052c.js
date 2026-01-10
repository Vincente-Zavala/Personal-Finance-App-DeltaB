document.addEventListener("DOMContentLoaded", () => {
    if (typeof ALL_TRANSACTIONS_API_URL === "undefined") {
        console.error("ALL_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    // Initial load
    loadTransactions();

    // Attach filter form submit
    const filterForm = document.getElementById("filterTransactionsForm");
    if (filterForm) {
        filterForm.addEventListener("submit", handleFilterSubmit);
    }
});

/* -----------------------------
   LOAD TRANSACTIONS (GET / POST)
-------------------------------- */
function loadTransactions({ method = "GET", body = null } = {}) {
    const tbody = document.getElementById("allTransactionsBody");
    if (!tbody) {
        console.error("allTransactionsBody not found");
        return;
    }

    // Show loading row
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center text-muted py-4">
                Loading transactions…
            </td>
        </tr>
    `;

    const options = {
        method,
        credentials: "same-origin",
    };

    if (method === "POST" && body) {
        options.body = body;
        options.headers = {
            "X-CSRFToken": body.get("csrfmiddlewaretoken"),
        };
    }

    fetch(ALL_TRANSACTIONS_API_URL, options)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            renderTransactions(data.transactions || []);
        })
        .catch(err => {
            console.error("Transaction load failed:", err);
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger py-4">
                        Failed to load transactions.
                    </td>
                </tr>
            `;
        });
}

/* -----------------------------
   RENDER TRANSACTIONS
-------------------------------- */
function renderTransactions(transactions) {
    const tbody = document.getElementById("allTransactionsBody");
    tbody.innerHTML = "";

    if (!transactions.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    No transactions found.
                </td>
            </tr>
        `;
        return;
    }

    const fragment = document.createDocumentFragment();

    transactions.forEach(tx => {
        const tr = document.createElement("tr");
        tr.classList.add("transaction-row");
        tr.dataset.type = tx.type_name;

        tr.innerHTML = `
            <td hidden>
                <input class="form-check-input" type="checkbox" name="selectedtransactions" value="${tx.id}">
            </td>
            <td>${tx.formatted_date}</td>
            <td>${tx.type_name}</td>
            <td>${tx.category_name || ""}</td>
            <td class="text-truncate" style="max-width:400px;" title="${tx.note || ""}">
                ${tx.note || ""}
            </td>
            <td>${tx.account_display}</td>
            <td class="text-end fw-semibold text-primary">
                $${tx.amount}
            </td>
        `;

        fragment.appendChild(tr);
    });

    tbody.appendChild(fragment);
}

/* -----------------------------
   HANDLE FILTER FORM SUBMIT
-------------------------------- */
function handleFilterSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    // Reuse loadTransactions with POST
    loadTransactions({ method: "POST", body: formData });
}
