document.addEventListener("DOMContentLoaded", () => {
    if (typeof ALL_TRANSACTIONS_API_URL === "undefined") {
        console.error("ALL_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    const tbody = document.getElementById("allTransactionsBody");
    const allloadingRow = document.getElementById("allloadingRow");

    fetch(ALL_TRANSACTIONS_API_URL, { credentials: "same-origin" })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            if (!tbody) {
                console.error("Table body not found!");
                return;
            }

            tbody.innerHTML = ""; // clear loading row

            if (!data.transactions || !data.transactions.length) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center text-muted py-4">No transactions found.</td>
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
                    <td class="editcol" hidden><input class="form-check-input" type="checkbox" name="selectedtransactions" value="${tx.id}"></td>
                    <td>${tx.formatted_date}</td>
                    <td class="category-cell">${tx.type_name}</td>
                    <td>${tx.category_name}</td>
                    <td class="text-truncate" style="max-width:400px;" title="${tx.note}">${tx.note}</td>
                    <td>${tx.account_display}</td>
                    <td class="text-end fw-semibold text-primary">$${tx.amount}</td>
                `;
                fragment.appendChild(tr);
            });

            tbody.appendChild(fragment);
        })
        .catch(err => {
            console.error("Transaction load failed:", err);
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center text-danger py-4">
                            Failed to load transactions.
                        </td>
                    </tr>
                `;
            }
        });
});
