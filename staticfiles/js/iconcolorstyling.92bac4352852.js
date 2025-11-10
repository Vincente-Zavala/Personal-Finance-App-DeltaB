// Category Type Styles
const categoryTypeStyles = {
    income: { color: "#38EB14", icon: "fa-arrow-trend-up" },
    expense: { color: "#EB1616", icon: "fa-arrow-trend-down" },
    savings: { color: "#1443EB", icon: "fa-piggy-bank" },
    transfer: { color: "#9CA3AF", icon: "fa-right-left" },
    debt: { color: "#EB8314", icon: "fa-file-invoice-dollar" },
    investment: { color: "#EB14A0", icon: "fa-chart-line" },
    refund: { color: "#8B5CF6", icon: "fa-rotate-left" },
    retirement: { color: "#FFD700", icon: "fa-umbrella-beach" },
  };
  
  // Account Type Styles
  const accountTypeStyles = {
    cash: { color: "#16A34A", icon: "fa-money-bill-wave" },
    checkingaccount: { color: "#2563EB", icon: "fa-building-columns" },
    savingsaccount: { color: "#1E40AF", icon: "fa-piggy-bank" },
    creditcard: { color: "#F97316", icon: "fa-credit-card" },
    loan: { color: "#D97706", icon: "fa-hand-holding-dollar" },
    investment: { color: "#059669", icon: "fa-chart-line" },
    retirement: { color: "#4F46E5", icon: "fa-umbrella-beach" },
    digitalwallet: { color: "#9333EA", icon: "fa-wallet" },
  };
  

  function applyCategoryStyles(selector, stylesMap) {
    document.querySelectorAll(selector).forEach(card => {
      const typeEl = card.querySelector("p, h5, .badge");
      const type = typeEl?.innerText.toLowerCase().trim().replace(/\s+/g, "");
      const style = stylesMap[type];
      
      if (style) {
        // Set accent color variables
        card.style.setProperty("--accent-color", style.color);
        const rgb = style.color.match(/[A-Fa-f0-9]{2}/g)
          .map(x => parseInt(x, 16))
          .join(", ");
        card.style.setProperty("--accent-rgb", rgb);
  
        // Apply color to icon & heading
        const icon = card.querySelector("i");
        if (icon) icon.style.color = style.color;

        const badge = card.querySelector(".badge");
        if (badge) {
          badge.style.backgroundColor = style.color;
          badge.style.color = "#fff";
        }
      }
    });
  }
  
  // Run on page load
  document.addEventListener("DOMContentLoaded", () => {
    applyCategoryStyles(".category-border", categoryTypeStyles);
  });