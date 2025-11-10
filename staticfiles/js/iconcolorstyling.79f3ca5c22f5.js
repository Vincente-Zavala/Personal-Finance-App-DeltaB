// Category Type Styles
const categoryTypeStyles = {
    income: { color: "#22C55E", icon: "fa-arrow-trend-up" },
    expense: { color: "#EF4444", icon: "fa-arrow-trend-down" },
    savings: { color: "#3B82F6", icon: "fa-piggy-bank" },
    transfer: { color: "#9CA3AF", icon: "fa-right-left" },
    debt: { color: "#F59E0B", icon: "fa-file-invoice-dollar" },
    investment: { color: "#10B981", icon: "fa-chart-line" },
    refund: { color: "#8B5CF6", icon: "fa-rotate-left" },
    retirement: { color: "#6366F1", icon: "fa-umbrella-beach" },
  };
  
  // Account Type Styles
  const accountTypeStyles = {
    cash: { color: "#16A34A", icon: "fa-money-bill-wave" },
    checking: { color: "#2563EB", icon: "fa-building-columns" },
    savings: { color: "#1E40AF", icon: "fa-piggy-bank" },
    creditcard: { color: "#F97316", icon: "fa-credit-card" },
    loan: { color: "#D97706", icon: "fa-hand-holding-dollar" },
    investment: { color: "#059669", icon: "fa-chart-line" },
    retirement: { color: "#4F46E5", icon: "fa-umbrella-beach" },
    digitalwallet: { color: "#9333EA", icon: "fa-wallet" },
  };
  

  function applyTypeStyles(selector, stylesMap) {
    document.querySelectorAll(selector).forEach(card => {
      const typeEl = card.querySelector("p, h5, .account-type");
      const type = typeEl?.innerText.toLowerCase().trim().replace(/\s+/g, "");
  
      const style = stylesMap[type];
      if (style) {
        // Set main accent color
        card.style.setProperty("--accent-color", style.color);
  
        // Convert HEX → RGB
        const rgb = style.color.match(/[A-Fa-f0-9]{2}/g).map(x => parseInt(x, 16)).join(", ");
        card.style.setProperty("--accent-rgb", rgb);
  
        // Apply color to icon & heading
        const icon = card.querySelector("i");
        if (icon) icon.style.color = style.color;
        if (typeEl) typeEl.style.color = style.color;
      }
    });
  }
  
  document.addEventListener("DOMContentLoaded", () => {
    applyTypeStyles(".category-border", categoryTypeStyles);
    applyTypeStyles(".account-border", accountTypeStyles);
  });
  
    
  
  
  