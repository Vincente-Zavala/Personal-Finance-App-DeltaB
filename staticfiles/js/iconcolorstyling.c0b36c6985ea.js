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
  

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".category-border").forEach(card => {
      // Find category type text from <p> or <h5>
      const typeEl = card.querySelector("p, h5");
      const type = typeEl?.innerText.toLowerCase().trim();
  
      const style = categoryTypeStyles[type];
      if (style) {
        // Apply accent color to CSS var
        card.style.setProperty("--accent-color", style.color);
  
        // Apply color to icon (if exists)
        const icon = card.querySelector("i");
        if (icon) icon.style.color = style.color;
  
        // Apply color to heading text (your <h5>)
        if (typeEl) typeEl.style.color = style.color;
      }
    });
  });

  if (style) {
    card.style.setProperty("--accent-color", style.color);
  
    // Convert HEX to RGB for transparent use
    const rgb = style.color.match(/[A-Fa-f0-9]{2}/g)
      .map(x => parseInt(x, 16))
      .join(", ");
    card.style.setProperty("--accent-rgb", rgb);
  }
  
  