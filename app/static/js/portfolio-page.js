// portfolio-page.js
// JavaScript for the Portfolio Page (your own profile)

// ── DATA — comes from PORTFOLIO_DATA injected by Flask ──

// ── HELPERS ──
function getCsrfToken() {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    return csrfMeta ? csrfMeta.content : "";
}

const COUNTRY_CODES = {
    "Australia": "au", "Canada": "ca", "China": "cn", "France": "fr",
    "Germany": "de", "Indonesia": "id", "Italy": "it", "Japan": "jp",
    "Malaysia": "my", "New Zealand": "nz", "Singapore": "sg",
    "South Korea": "kr", "Spain": "es", "Switzerland": "ch",
    "Thailand": "th", "United Kingdom": "gb", "United States": "us",
    "Vietnam": "vn"
};

function getInitials(n) { if (!n) return "?"; return n.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2); }

// ── UPLOAD VALIDATION ──
const VALID_IMAGE_TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"];
const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB

function validateImageFile(file) {
    if (!VALID_IMAGE_TYPES.includes(file.type)) {
        return "Only PNG, JPG, GIF, or WEBP images are allowed. Videos are not permitted.";
    }
    if (file.size > MAX_IMAGE_SIZE) {
        return "File must be smaller than 10MB.";
    }
    return null;
}

// ── AVATAR UPLOAD (saves to server) ──
document.getElementById("avatar-display").addEventListener("click", () => document.getElementById("avatar-upload").click());
document.getElementById("avatar-overlay-btn").addEventListener("click", () => document.getElementById("avatar-upload").click());
document.getElementById("avatar-upload").addEventListener("change", e => {
    const file = e.target.files[0]; if (!file) return;

    const error = validateImageFile(file);
    if (error) {
        alert(error);
        e.target.value = "";
        return;
    }

    const formData = new FormData();
    formData.append("avatar", file);
    
    fetch("/api/upload-avatar", {
    method: "POST",
    headers: {
        "X-CSRFToken": getCsrfToken()
    },
    body: formData
    })
    
        .then(r => r.json())
        .then(data => {
            if (!data.success) { alert("Upload failed: " + data.error); return; }
            const d = document.getElementById("avatar-display");
            document.getElementById("avatar-initials").style.display = "none";
            let img = d.querySelector("img");
            if (!img) { img = document.createElement("img"); img.className = "w-full h-full object-cover"; d.appendChild(img); }
            img.src = data.url;
            const nav = document.getElementById("nav-avatar-display");
            if (nav) nav.innerHTML = `<img src="${data.url}" class="w-full h-full object-cover rounded-full">`;
        });
});

// ── BANNER UPLOAD (saves to server) ──
document.getElementById("banner-edit-btn").addEventListener("click", () => document.getElementById("banner-upload").click());
document.getElementById("banner-upload").addEventListener("change", e => {
    const file = e.target.files[0]; if (!file) return;

    const error = validateImageFile(file);
    if (error) {
        alert(error);
        e.target.value = "";
        return;
    }

    const formData = new FormData();
    formData.append("banner", file);
    
    fetch("/api/upload-banner", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken()
        },
        body: formData
    })

        .then(r => r.json())
        .then(data => {
            if (!data.success) { alert("Upload failed: " + data.error); return; }
            const banner = document.getElementById("banner");
            banner.style.background = "none";
            banner.style.backgroundImage = `url(${data.url})`;
            banner.style.backgroundSize = "cover";
            banner.style.backgroundPosition = "center";
        });
});

// ── COUNTRY FILTER ──
let activeCountries = new Set();

function filterByCountry(country, tagEl) {
    if (activeCountries.has(country)) {
        // unselect if already active
        activeCountries.delete(country);
        tagEl.classList.remove("active");
    } else {
        // add to selection
        activeCountries.add(country);
        tagEl.classList.add("active");
    }

    if (activeCountries.size === 0) {
        clearFilter();
        return;
    }

    // update filter notice
    document.getElementById("filter-country-name").textContent = [...activeCountries].join(", ");
    document.getElementById("filter-notice").classList.remove("hidden");
    document.getElementById("filter-notice").classList.add("flex");

    // show/hide cards
    document.querySelectorAll(".itinerary-card").forEach(card => {
        card.closest("li").style.display = activeCountries.has(card.dataset.country) ? "" : "none";
    });
}

function clearFilter() {
    activeCountries.clear();
    document.querySelectorAll(".country-tag").forEach(t => t.classList.remove("active"));
    document.getElementById("filter-notice").classList.add("hidden");
    document.getElementById("filter-notice").classList.remove("flex");
    document.querySelectorAll("#itineraries-grid li").forEach(li => li.style.display = "");
}


// ── RENDER ──
function renderProfile(user) {
    const initials = getInitials(user.username);
    document.getElementById("avatar-initials").textContent = initials;
    const navAvatar = document.getElementById("nav-avatar-display");
    if (navAvatar) navAvatar.textContent = initials;
    document.getElementById("username").textContent = user.username || "—";
    document.getElementById("uid").textContent = "UID: " + (user.uid || "—");
    document.title = (user.username || "My Profile") + " – Travel Blog";

    // Stats
    document.getElementById("stat-countries").textContent = Object.keys(user.countries).length;
    document.getElementById("stat-posts").textContent = user.itineraries.length;

}

function renderCountries(countries) {
    const list = document.getElementById("countries-list");
    list.innerHTML = "";
    const entries = Object.entries(countries);
    if (!entries.length) return;
    entries.forEach(([country, data]) => {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.className = "country-tag";
        btn.style.setProperty("--expanded-width", (52 + 8 + (country.length * 8.5) + 14) + "px");
        const code = COUNTRY_CODES[country] || "un";
        btn.innerHTML = `<span class="flag-circle"><img src="https://flagcdn.com/w40/${code}.png" alt="${country}" class="w-7 h-5 object-cover rounded-sm"></span><span class="country-name">${country}</span>`;
        btn.addEventListener("click", () => filterByCountry(country, btn));
        li.appendChild(btn);
        list.appendChild(li);
    });
}

function renderItineraries(itineraries) {
    const grid = document.getElementById("itineraries-grid");
    grid.innerHTML = "";
    if (!itineraries.length) {
        grid.innerHTML = '<li class="col-span-4 text-center py-10 text-gray-500 text-sm">No itineraries posted yet.</li>';
        return;
    }
    const colors = ["#DBEAFE", "#FEF3C7", "#D1FAE5", "#FCE7F3"];
    itineraries.forEach((it, i) => {
        const li = document.createElement("li");
        const link = document.createElement("a");
        link.href = `/itinerary/${it.id}`;
        link.className = "itinerary-card block bg-white border border-gray-200 rounded-xl overflow-hidden no-underline text-inherit flex flex-col shadow-sm hover:-translate-y-1 hover:shadow-lg transition-all duration-200";
        link.dataset.country = it.location;
        link.innerHTML = `
            <div class="h-24 overflow-hidden" style="background:${colors[i % colors.length]}">
                ${it.cover_image_url 
                    ? `<img src="${it.cover_image_url}" class="w-full h-full object-cover">` 
                    : `<div class="w-full h-full flex items-center justify-center text-4xl">✈️</div>`}
            </div>
            <div class="p-3 flex-1">
                <h3 class="text-xs font-bold text-blue-900 mb-1 leading-snug">${it.title}</h3>
                <div class="text-xs text-gray-500">📍 ${it.location}</div>
            </div>
            <div class="px-3 pb-3 pt-2 border-t border-gray-200 flex items-center gap-2 text-xs text-gray-500">
                <span>❤️ ${it.likes}</span>
                <span>🔖 ${it.saves}</span>
            </div>`;
        li.appendChild(link);
        grid.appendChild(li);
    });
}

// Restore saved avatar and banner on page load
if (PORTFOLIO_DATA.avatar_url) {
    const d = document.getElementById("avatar-display");
    document.getElementById("avatar-initials").style.display = "none";
    let img = d.querySelector("img");
    if (!img) { img = document.createElement("img"); img.className = "w-full h-full object-cover"; d.appendChild(img); }
    img.src = PORTFOLIO_DATA.avatar_url;
    const nav = document.getElementById("nav-avatar-display");
    if (nav) nav.innerHTML = `<img src="${PORTFOLIO_DATA.avatar_url}" class="w-full h-full object-cover rounded-full">`;
}
if (PORTFOLIO_DATA.banner_url) {
    const banner = document.getElementById("banner");
    banner.style.background = "none";
    banner.style.backgroundImage = `url(${PORTFOLIO_DATA.banner_url})`;
    banner.style.backgroundSize = "cover";
    banner.style.backgroundPosition = "center";
}

renderProfile(PORTFOLIO_DATA);
renderCountries(PORTFOLIO_DATA.countries);
renderItineraries(PORTFOLIO_DATA.itineraries);