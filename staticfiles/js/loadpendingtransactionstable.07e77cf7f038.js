document.addEventListener("DOMContentLoaded", () => {
    if (typeof PENDING_TRANSACTIONS_API_URL === "undefined") {
        console.error("PENDING_TRANSACTIONS_API_URL is not defined!");
        return;
    }

    const tbody = document.getElementById("pendingTransactionsBody");
    const pendingloadingRow = document.getElementById("pendingloadingRow");

    fetch(PENDING_TRANSACTIONS_API_URL, { credentials: "same-origin" })
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

            if (!data.results || !data.results.length) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center text-muted py-4">No transactions found.</td>
                    </tr>
                `;
                return;
            }

            const fragment = document.createDocumentFragment();

            data.results.forEach(tx => {
                const tr = document.createElement("tr");
                tr.classList.add("transaction-row");
                tr.dataset.type = tx.type_name;

                tr.innerHTML = `
                    <td class="editcol" hidden><input class="form-check-input" type="checkbox" name="selectedtransactions" value="{tx.id}"></td>
                    <td>${tx.formatted_date}</td>
                    <td class="text-truncate" style="max-width:400px;" title="${tx.note}">${tx.note}</td>
                    <td>${tx.account_display}</td>
                    <td class="text-end fw-semibold text-primary">$${tx.amount}</td>
                    <td>
                        <select 
                            class="form-select form-select-sm rounded-pill category-select" 
                            name="categorychoice_{{ transaction.id }}"
                            data-transaction-id="{{ transaction.id }}">
                            <option value="" selected>Select Category...</option>
                            {% for categorytype in categorytypes %}
                            {% if categorytype.name == "Refund" or categorytype.name == "Reimbursement" %}
                            <optgroup label="{{ categorytype.name }}">
                            {% for category in categorytype.displaycategories %}
                                <option value="{tx.category.id}" data-categorytype="{{ categorytype.name|lower }}">{{ category.name }}</option>
                            {% endfor %}
                            </optgroup>
                            {% else %}
                            <optgroup label="{{ categorytype.name }}">
                            {% for category in categorytype.category_set.all %}
                                <option value="{tx.category.id}" data-categorytype="{{ categorytype.name|lower }}">{{ category.name }}</option>
                            {% endfor %}
                            </optgroup>
                            {% endif %}
                            {% endfor %}
                        </select>
                    <input type="hidden" name="transactiontype_{{ transaction.id }}" data-categorytype="{{ categorytype.name|lower }}" class="transaction-type-hidden" value="">
                  </td>
                  <td>
                    <select 
                        class="form-select form-select-sm rounded-pill account-select" 
                        name="accountchoice_{{ transaction.id }}"
                        id="accountchoice_{{ transaction.id }}">
                        <option value="" selected>**Select Destination Account**</option>
                        {% for account in accounts %}
                            <option value="{tx.account.id}">{{ account.institution.name }} - {{ account.name }}</option>
                        {% endfor %}
                    </select>
                  </td>
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
