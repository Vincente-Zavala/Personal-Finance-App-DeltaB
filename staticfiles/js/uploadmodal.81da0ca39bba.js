// ============================
//  Upload Wizard (AJAX)
// ============================

document.addEventListener("DOMContentLoaded", () => {

    const csrfToken = getCSRF();

    // ----------------------------
    // 1. Upload File (Step 1)
    // ----------------------------
    const fileInput = document.getElementById("uploadfile_input");
    if (fileInput) {
        fileInput.addEventListener("change", function () {
            let formData = new FormData();
            formData.append("uploadfile", this.files[0]);

            fetch("/uploadfile/", {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === "ok") {
                    // Insert column dropdowns dynamically
                    populateMappingModal(data.columns);
                    // Switch modals
                    showModal("#mapcolumns");
                } else {
                    alert(data.error);
                }
            });
        });
    }

    // ----------------------------
    // 2. Submit Column Mapping
    // ----------------------------
    const mapForm = document.getElementById("mapcolumns_form");
    if (mapForm) {
        mapForm.addEventListener("submit", function (e) {
            e.preventDefault();

            let formData = new FormData(mapForm);

            fetch("/adduploaddata/", {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === "require_polarity") {
                    // Fill polarity modal with sample row
                    populatePolarityModal(data.sample);
                    showModal("#accountpolarity");
                }
                else if (data.status === "preview_ready") {
                    loadUploadPreview();
                }
                else {
                    alert(data.error);
                }
            });
        });
    }


    // ----------------------------
    // 3. Polarity Selection
    // ----------------------------
    const polarityForm = document.getElementById("accountpolarity_form");
    if (polarityForm) {
        polarityForm.addEventListener("submit", function (e) {
            e.preventDefault();

            let formData = new FormData(polarityForm);

            fetch("/setpolarity/", {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === "ok") {
                    loadUploadPreview();
                } else {
                    alert(data.error);
                }
            });
        });
    }



    // ----------------------------
    // Load Upload Preview
    // ----------------------------
    function loadUploadPreview() {
        fetch("/getpreview/")
        .then(r => r.json())
        .then(data => {
            populatePreviewTable(data.transactions);
            showModal("#uploadpreview");
        });
    }


    // ============================
    // Helper Functions
    // ============================


    function populateMappingModal(columns) {
        const selects = document.querySelectorAll(".column-select");

        selects.forEach(sel => {
            sel.innerHTML = `<option disabled selected>Select Column</option>`;
            columns.forEach(col => {
                sel.innerHTML += `<option value="${col}">${col}</option>`;
            });
        });
    }


    function populatePolarityModal(sample) {
        document.getElementById("polarity_date").innerText     = sample.date;
        document.getElementById("polarity_note").innerText     = sample.note;
        document.getElementById("polarity_amount").innerText   = sample.amount;
        document.getElementById("polarity_account").innerText  = sample.account;
    }


    function populatePreviewTable(rows) {
        let table = document.getElementById("preview_table_body");
        table.innerHTML = "";

        rows.forEach(tx => {
            table.innerHTML += `
                <tr>
                    <td>${tx.date}</td>
                    <td>${tx.type}</td>
                    <td>${tx.category}</td>
                    <td>${tx.note}</td>
                    <td>${tx.account}</td>
                    <td class="text-end">$${tx.amount}</td>
                </tr>
            `;
        });
    }


    function showModal(selector) {
        const modal = new bootstrap.Modal(document.querySelector(selector));
        modal.show();
    }


    function getCSRF() {
        const cookieValue = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));
        return cookieValue ? cookieValue.split("=")[1] : "";
    }

});
