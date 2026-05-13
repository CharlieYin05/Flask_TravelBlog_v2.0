// ─────────────────────────────
// Base JS (global for all pages)
// ─────────────────────────────

// Get CSRF token from meta tag
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
}

// ─────────────────────────────
// MOBILE MENU TOGGLE
// ─────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("mobile-menu-btn");
  const menu = document.getElementById("mobile-menu");
  const lines = btn ? btn.querySelectorAll(".hamburger-line") : [];

  if (btn && menu) {
    btn.addEventListener("click", () => {
      const isOpen = !menu.classList.contains("hidden");

      if (isOpen) {
        menu.classList.add("hidden");
        lines[0].style.transform = "";
        lines[1].style.opacity = "";
        lines[2].style.transform = "";
      } else {
        menu.classList.remove("hidden");
        lines[0].style.transform = "translateY(8px) rotate(45deg)";
        lines[1].style.opacity = "0";
        lines[2].style.transform = "translateY(-8px) rotate(-45deg)";
      }
    });

    document.addEventListener("click", (e) => {
      if (!btn.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.add("hidden");
        lines[0].style.transform = "";
        lines[1].style.opacity = "";
        lines[2].style.transform = "";
      }
    });
  }
});

// Optional: fallback if image fails to load
document.addEventListener("DOMContentLoaded", () => {
    const avatar = document.getElementById("avatar-img");

    if (avatar) {
        avatar.addEventListener("error", () => {
            // Replace broken image with default fallback
            avatar.src = "/static/images/default-avatar.png";
        });
    }
});

