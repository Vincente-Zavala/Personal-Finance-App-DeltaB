document.addEventListener("DOMContentLoaded", function () {

  // Map transaction types to fields that should be shown
  const typeToFields = {
      income: ["datefields", "categoryfields", "initialaccountfields", "amountfields", "notefields"],
      expense: ["datefields", "categoryfields", "initialaccountfields", "amountfields", "notefields", "refundfields"],
      savings: ["datefields", "categoryfields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      investment: ["datefields", "categoryfields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      debt: ["datefields", "categoryfields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      transfer: ["datefields", "categoryfields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      fee: ["datefields", "categoryfields", "initialaccountfields", "amountfields", "notefields"]
  };

  // Map transaction types to allowed account types
  const typeToInitialAccounts = {
      income: ["Checking Account", "Savings Account", "Retirement"],
      expense: ["Checking Account", "Savings Account", "Credit Card"],
      savings: ["Checking Account"],
      investment: ["Checking Account", "Savings Account", "Credit Card"],
      debt: ["Checking Account", "Savings Account", "Credit Card"],
      transfer: ["Savings Account", "Credit Card", "Investment", "Loan", "Retirement"],
  };

  // INPUTS WITH FINAL ACCOUNTS
  const typeToFinalAccounts = {
      income: [],
      expense: [],
      savings: ["Savings Account"],
      investment: ["Investment"],
      debt: ["Loan", "Credit Card"],
      transfer: ["Checking Account", "Credit Card", "Loan"],
  };

  const allFieldIds = [
      "datefields",
      "categoryfields",
      "initialaccountfields",
      "finalaccountfields",
      "amountfields",
      "notefields",
      "refundfields"
  ];

  const transactionType = document.getElementById("inputtransaction");

  // HIDE ALL FIELDS
  function hideAllFields() {
      allFieldIds.forEach((id) => {
          const el = document.getElementById(id);
          if (el) el.style.display = "none";
      });
  }

  // FILTER BY CATEGORY
  function filterCategoryOptions(type) {
    const container = document.getElementById("categoryfields");
    if (!container) return;

    const categories = container.querySelectorAll(".form-check");
    categories.forEach(cat => {
      if (cat.getAttribute("data-type")?.toLowerCase() === type.toLowerCase())
      {
            cat.style.display = "block";
        } else {
            const radio = cat.querySelector("input[type='radio']");
            if (radio) radio.checked = false;
            cat.style.display = "none";
        }
    });
}

    // DISPLAY FIELDS FOR TYPE
  function showFieldsForType(type) {
      hideAllFields();
      if (!type || !typeToFields[type]) return;
      typeToFields[type].forEach((id) => {
          const el = document.getElementById(id);
          if (el) el.style.display = "block";
      });
      filterRadioOptions("initialaccountfields", typeToInitialAccounts[type]);
      filterRadioOptions("finalaccountfields", typeToFinalAccounts[type]);
      if (type && typeToFields[type].includes("categoryfields")) {
        filterCategoryOptions(type);
    }
  }

  // FILTER RADIO
  function filterRadioOptions(containerId, allowedTypes) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const radios = container.querySelectorAll("input[type='radio']");
    radios.forEach(radio => {
        const type = radio.getAttribute("data-type");
        if (allowedTypes.includes(type)) {
            radio.parentElement.style.display = "block";
        } else {
            radio.checked = false;
            radio.parentElement.style.display = "none";
        }
    });
}


  // INITIAL HIDE
  hideAllFields();

  // CHANGE LISTENER
  if (transactionType) {
      transactionType.addEventListener("change", function () {
          showFieldsForType(this.value);
      });
  }
});

