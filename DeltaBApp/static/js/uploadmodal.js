document.addEventListener("DOMContentLoaded", () => {

    function getCSRF() {
        const cookie = document.cookie.split("; ").find(row => row.startsWith("csrftoken="));
        return cookie ? cookie.split("=")[1] : "";
    }
    const csrfToken = getCSRF();

    function showModal(selector) {
        const modalEl = document.querySelector(selector);
        if (!modalEl) return;
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
    
    function hideModal(selector) {
        const modalEl = document.querySelector(selector);
        if (!modalEl) return;
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }

    const confirmImportBtn = document.getElementById("confirmImportBtn");
    confirmImportBtn.addEventListener("click", () => {
        hideModal("#duplicatesModal");
        loadUploadPreview();
    });
    


    // -------------------------------
    // Upload File
    // -------------------------------
    const uploadInput = document.getElementById("uploadfileinput");
    if (uploadInput) {
        uploadInput.addEventListener("change", () => {
            const file = uploadInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("uploadfile", file);

            fetch("/uploadfile/", {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (!data.success) return alert("Upload failed.");
                populateMappingModal(data.columns);
                populateAccountDropdown(data.accounts);
                hideModal("#uploadfilemodal");
                showModal("#mapcolumns");
            })
            .catch(err => {
                console.error(err);
                alert("Upload error.");
            });
        });
    }

    // -------------------------------
    // Map Columns → Check Polarity / Preview
    // -------------------------------
    const mapForm = document.getElementById("mapcolumns_form");
    if (mapForm) {
        mapForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const formData = new FormData(mapForm);

            fetch("/processupload/", {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === "preview_ready") {
                    console.log("Within preview")
                    loadUploadPreview()
                    hideModal("#mapcolumns");
                } else if (data.status === "duplicates") {
                    console.log("Within Duplicates")
                    populateDuplicatesModal(data.groups);
                    hideModal("#mapcolumns")
                } else {
                    alert(data.error || "Mapping failed.");
                }
            });
        });
    }


    const previewForm = document.getElementById("uploadpreview-form");

    if (previewForm) {
        previewForm.addEventListener("submit", function (e) {
            e.preventDefault();

            fetch("/submitupload/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                },
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === "ok") {
                    alert("Upload complete!");
                    location.reload();
                    hideModal("#uploadpreview");
                    hideModal("#uploadfile")
                } else {
                    alert(data.error || "Upload failed.");
                }
            })
            .catch(err => {
                console.error(err);
                alert("Error submitting upload.");
            });
        });
    }


    // -------------------------------
    // Show Preview
    // -------------------------------
    function loadUploadPreview() {
        console.log("Debug: within loaduploadpreview")
        fetch("/getpreview/")
            .then(r => r.json())
            .then(data => {
                console.log("DEBUG PREVIEW:", data);
            
                
                const tbody = document.getElementById("previewTableBody");
                tbody.innerHTML = "";
    
                data.transactions.forEach(tx => {
                    const row = `
                        <tr class="text-light">
                            <td hidden></td>
                            <td>${tx.date}</td>
                            <td class="text-truncate" style="max-width:150px;" title="${tx.note}">
                                ${tx.note}
                            </td>
                            <td>${tx.account}</td>
                            <td class="text-end fw-semibold text-primary">$${tx.amount}</td>
                        </tr>
                    `;
                    tbody.insertAdjacentHTML("beforeend", row);
                });
    
                showModal("#uploadpreview");
            })
            .catch(err => {
                console.error(err);
                alert("Error loading preview.");
            });
    }
    

    // -------------------------------
    // Helper functions
    // -------------------------------
    function populateMappingModal(columns) {
        document.querySelectorAll(".column-select").forEach(sel => {
            sel.innerHTML = `<option disabled selected>Select Column</option>`;
            columns.forEach(col => sel.innerHTML += `<option value="${col}">${col}</option>`);
        });
    }

    function populateAccountDropdown(accounts) {
        const accountSelect = document.getElementById("accountselection");
        accountSelect.innerHTML = `<option disabled selected>Select Account</option>`;
    
        accounts.forEach(acc => {
            accountSelect.innerHTML += `
                <option value="${acc.id}">
                    ${acc.institution} - ${acc.name}
                </option>
            `;
        });
    }
    


    function populateDuplicatesModal(groups) {
        const tbody = document.getElementById("duplicatesTableBody");
        tbody.innerHTML = "";
    
        let totalDuplicates = 0;
    
        groups.forEach(group => {
            const newTx = group.new;
            const existing = group.existing;
    
            if (existing.length === 0) return;
    
            totalDuplicates++;
    
            tbody.insertAdjacentHTML("beforeend", `
                <tr class="table-warning transaction-row">
                    <td>${newTx.date}</td>
                    <td class="text-truncate" style="max-width: 200px;">${newTx.note}</td>
                    <td>${newTx.account}</td>
                    <td class="text-end amount-cell">$${newTx.amount}</td>
                    <td>New Row</td>
                </tr>
            `);
    
            existing.forEach(ex => {
                tbody.insertAdjacentHTML("beforeend", `
                    <tr class="table-danger">
                        <td>${ex.date}</td>
                        <td>${ex.note}</td>
                        <td>${ex.account}</td>
                        <td class="text-end">$${ex.amount}</td>
                        <td>Existing</td>
                    </tr>
                `);
            });
    

            tbody.insertAdjacentHTML("beforeend", `
                <tr><td colspan="5" class="bg-dark border-0" style="height: 8px;"></td></tr>
            `);
        });
    

        document.getElementById("duplicateCount").textContent = totalDuplicates;
    
        showModal("#duplicatesModal");
    }

    function populatePolarityModal(sample) {
        document.getElementById("sampledate").innerText = sample.date;
        document.getElementById("samplenote").innerText = sample.note;
        document.getElementById("sampleamount").innerText = sample.amount;
        document.getElementById("sampleaccount").innerText = sample.account;
        document.getElementById("sampleaccountid").value = sample.account_id || "";
    }

    function populatePreviewTable(rows) {
        const table = document.getElementById("preview_table_body");
        table.innerHTML = "";
        rows.forEach(tx => {
            table.innerHTML += `
                <tr>
                    <td>${tx.date}</td>
                    <td>${tx.type}</td>
                    <td>${tx.category || ""}</td>
                    <td>${tx.note}</td>
                    <td>${tx.account}</td>
                    <td class="text-end">$${tx.amount}</td>
                </tr>
            `;
        });
    }


    function showModal(selector) {
        const modalEl = document.querySelector(selector);
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }

    function hideModal(selector) {
        const modalEl = document.querySelector(selector);
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }
});
