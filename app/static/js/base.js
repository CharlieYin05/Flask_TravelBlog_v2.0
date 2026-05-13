// ─────────────────────────────
// Base JS (global for all pages)
// ─────────────────────────────

// Get CSRF token from meta tag
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
}

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

