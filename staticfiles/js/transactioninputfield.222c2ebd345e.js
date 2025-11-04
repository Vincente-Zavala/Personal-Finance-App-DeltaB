document.addEventListener("DOMContentLoaded", function () {

  // TRANSACTION TYPE TO FIELDS
  const typeToFields = {
      income: ["datefields", "categoryfields", "initialaccountfields", "amountfields", "notefields"],
      expense: ["datefields", "categoryfields", "initialaccountfields", "amountfields", "notefields",],
      savings: ["datefields", "categoryfields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      investment: ["datefields", "categoryfields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      retirement: ["datefields", "categoryfields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      debt: ["datefields", "categoryfields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      transfer: ["datefields", "initialaccountfields", "finalaccountfields", "amountfields", "notefields"],
      refund: ["datefields", "categoryfields", "initialaccountfields", "amountfields", "notefields"]
  };

  // TRANSACTION TYPE TO ACCOUNTS
  const typeToInitialAccounts = {
      income: ["Cash", "Checking Account", "Savings Account", "Digital Wallet"],
      expense: ["Cash", "Checking Account", "Savings Account", "Credit Card", "Digital Wallet", "Investment"],
      savings: ["Cash", "Checking Account", "Credit Card", "Digital Wallet", "Loan", "Investment", "Retirement"],
      investment: ["Cash", "Checking Account", "Savings Account", "Credit Card", "Digital Wallet"],
      retirement: ["Cash", "Checking Account", "Savings Account", "Credit Card", "Digital Wallet"],
      debt: ["Cash", "Checking Account", "Savings Account", "Credit Card", "Digital Wallet"],
      transfer: ["Cash", "Checking Account", "Savings Account", "Credit Card", "Investment", "Loan", "Retirement", "Digital Wallet"],
      refund: ["Cash", "Checking Account", "Savings Account", "Credit Card", "Investment", "Digital Wallet"]
  };

  // INPUTS WITH FINAL ACCOUNTS
  const typeToFinalAccounts = {
      income: [],
      expense: [],
      savings: ["Savings Account"],
      investment: ["Investment"],
      retirement: ["Retirement"],
      debt: ["Loan", "Credit Card"],
      transfer: ["Cash", "Checking Account", "Digital Wallet"],
      refund: [],
  };

  const allFieldIds = [
      "datefields",
      "categoryfields",
      "initialaccountfields",
      "finalaccountfields",
      "amountfields",
      "notefields",
  ];

  const transactionType = document.getElementById("inputtransaction");

  // HIDE ALL FIELDS
  function hideAllFields() {
    allFieldIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.classList.add("hidefield");
    });
  }

  // FILTER BY CATEGORY
  function filterCategoryOptions(type) {
    const container = document.getElementById("categoryfields");
    if (!container) return;

    const categories = container.querySelectorAll(".radio-card");

    // For refunds, show expense categories
    const effectiveType = (type === "refund") ? "expense" : type;

    categories.forEach(cat => {
        const catType = cat.getAttribute("data-type")?.toLowerCase();
        if (catType === effectiveType.toLowerCase()) {
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
          if (el) el.classList.remove("hidefield");
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

