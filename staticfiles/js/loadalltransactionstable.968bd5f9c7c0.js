function loadTransactions({ method = "GET", body = null } = {}) {
    if (typeof ALL_TRANSACTIONS_API_URL === "undefined") {
        console.error("ALL_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    const tbody = document.getElementById("allTransactionsBody");
    if (!tbody) return;

    fetch(ALL_TRANSACTIONS_API_URL, {
        method,
        credentials: "same-origin",
        headers: body ? { "X-CSRFToken": body.get("csrfmiddlewaretoken") } : {},
        body,
    })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            tbody.innerHTML = "";

            if (!data.transactions || !data.transactions.length) {
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

            data.transactions.forEach(tx => {
                const tr = document.createElement("tr");
                tr.classList.add("transaction-row");
                tr.dataset.type = tx.type_name;

                tr.innerHTML = `
                    <td hidden>
                        <input class="form-check-input" type="checkbox" value="${tx.id}">
                    </td>
                    <td>${tx.formatted_date}</td>
                    <td>${tx.type_name}</td>
                    <td>${tx.category_name}</td>
                    <td class="text-truncate" title="${tx.note}">
                        ${tx.note}
                    </td>
                    <td>${tx.account_display}</td>
                    <td class="text-end fw-semibold text-primary">
                        $${tx.amount}
                    </td>
                `;
                fragment.appendChild(tr);
            });

            tbody.appendChild(fragment);
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
