// Category Type Styles
const categoryTypeStyles = {
    income: { color: "#38EB14", icon: "fa-dollar-sign" },
    expense: { color: "#EB1616", icon: "fa-receipt" },
    savings: { color: "#1443EB", icon: "fa-piggy-bank" },
    transfer: { color: "#9CA3AF", icon: "fa-retweet" },
    debt: { color: "#EB8314", icon: "fa-file-invoice-dollar" },
    investment: { color: "#EB14A0", icon: "fa-chart-line" },
    refund: { color: "#8B5CF6", icon: "fa-rotate-left" },
    reimbursement: { color: "#8B5CF6", icon: "fa-rotate-left" },
    retirement: { color: "#FFD700", icon: "fa-sun" },
  };
  
  // Account Type Styles
  const accountTypeStyles = {
    cash: { color: "#16A34A", icon: "fa-money-bill" },
    checkingaccount: { color: "#2563EB", icon: "fa-money-check" },
    savingsaccount: { color: "#1E40AF", icon: "fa-wallet" },
    creditcard: { color: "#F97316", icon: "fa-credit-card" },
    loan: { color: "#D97706", icon: "fa-landmark" },
    investment: { color: "#059669", icon: "fa-coins" },
    retirement: { color: "#4F46E5", icon: "fa-sack-dollar" },
    digitalwallet: { color: "#9333EA", icon: "fa-mobile-alt" },
  };


function applyCategoryStyles(selector, stylesMap) {
  document.querySelectorAll(selector).forEach(card => {
    const badge = card.querySelector(".badge[data-type]");
    let type = badge?.dataset.type?.toLowerCase()?.trim();

    if (!type) {
      const typeEl = card.querySelector("p, h5");
      type = typeEl?.innerText?.toLowerCase()?.trim()?.replace(/\s+/g, "");
    }

    console.log("Detected category:", type);

    const style = stylesMap[type];
    if (style) {
      card.style.setProperty("--accent-color", style.color);
      card.style.setProperty("--accent-color", style.color);
      const rgb = style.color.match(/[A-Fa-f0-9]{2}/g)
        .map(x => parseInt(x, 16))
        .join(", ");
      card.style.setProperty("--accent-rgb", rgb);

      const icon = card.querySelector("i");
      if (icon) icon.style.color = style.color;

    }
  });
}


document.addEventListener("DOMContentLoaded", () => {
  applyCategoryStyles(".category-border", categoryTypeStyles);
  console.log("After applycategorystyles")
});
