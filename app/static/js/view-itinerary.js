// ===== GLOBAL =====
let map;
let activeInfoWindow = null;
const allMapMarkers = [];

let itinerary = null;
let mapInitialized = false;
let googleMapsReady = false;

window.onGoogleMapsReady = function () {
    googleMapsReady = true;
    tryInitMap();
};

function tryInitMap() {
    if (mapInitialized) return;
    if (!itinerary) return;
    if (!googleMapsReady) return;
    if (!window.google || !window.google.maps) return;

    mapInitialized = true;
    initMap();
}


// ===== DOM RENDER =====
document.addEventListener("DOMContentLoaded", () => {
    const itineraryId = window.location.pathname.split("/").pop();

    fetch(`/api/itinerary/${itineraryId}`)
        .then(res => res.json())
        .then(data => {
            itinerary = data;

            renderItineraryHeader();
            renderTimeline();
            setupObserver();
            setupInteractionButtons();

            // fetch 完成后立刻尝试初始化地图
            tryInitMap();
        })
        .catch(err => {
            console.error("Failed to load itinerary:", err);
        });
});

// Google Maps script 加载完成后，再尝试一次
window.addEventListener("load", () => {
    tryInitMap();
});


// ===== HEADER =====
function renderItineraryHeader() {
    const titleEl = document.getElementById("title");
    const authorEl = document.getElementById("author");
    const dateEl = document.getElementById("date");
    const countryEl = document.getElementById("country");
    const overviewEl = document.getElementById("overview");
    const tagsContainer = document.getElementById("tags");
    const coverEl = document.getElementById("cover-photo");

    if (titleEl) titleEl.innerText = itinerary.title;
    if (authorEl) authorEl.innerText = itinerary.author;
    if (dateEl) dateEl.innerText = itinerary.date;
    if (countryEl) countryEl.innerText = itinerary.country;
    if (overviewEl) overviewEl.innerText = itinerary.overview;
    if (coverEl) {
        coverEl.src = itinerary.coverPhoto;
        coverEl.alt = itinerary.title;
    }

    if (tagsContainer) {
        tagsContainer.innerHTML = "";

        const tags = itinerary.tags || [];

        tags.slice(0, 3).forEach((tag) => {
            const el = document.createElement("span");
            el.className =
                "px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium";
            el.innerText = tag;
            tagsContainer.appendChild(el);
        });
    }
}

// ===== TIMELINE =====
function renderTimeline() {
    const timeline = document.getElementById("timeline");
    if (!timeline) return;
    if (!itinerary) return;

    timeline.innerHTML = "";

    const days = itinerary.days || [];

    if (days.length === 0) {
        timeline.innerHTML = `
            <div class="bg-white border border-slate-200 rounded-2xl p-6 text-slate-500">
                No daily itinerary details yet.
            </div>
        `;
        return;
    }

    days.forEach((dayObj) => {
        const transport = dayObj.transport || [];
        const activities = dayObj.activities || [];

        const daySection = document.createElement("section");
        daySection.className = "space-y-5";

        const dayHeader = document.createElement("div");
        dayHeader.className = "day-header-card";
        dayHeader.innerHTML = `
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <h2 class="text-2xl font-bold">Day ${dayObj.day || ""}</h2>
              <p class="text-gray-600 mt-1">${dayObj.state || ""} · ${dayObj.city || ""}</p>
            </div>
            <div class="text-sm text-gray-600">
              <span class="font-semibold">Transport:</span> ${transport.length ? transport.join(", ") : "Not specified"}
            </div>
          </div>
        `;
        daySection.appendChild(dayHeader);

        activities.forEach((act, i) => {
            const wrapper = document.createElement("div");
            wrapper.className = "timeline-item";

            const left = document.createElement("div");
            left.className = "timeline-left";

            const dot = document.createElement("div");
            dot.className = "timeline-dot";

            const line = document.createElement("div");
            line.className = "timeline-line";

            if (i === activities.length - 1) {
                line.classList.add("short-line");
            }

            left.appendChild(dot);
            left.appendChild(line);

            const content = createLocationCard({
                label: `Activity ${i + 1}`,
                title: act.title || "Untitled activity",
                image: act.image || "",
                description: act.description || "",
                place: act.place || "",
                time: act.time || "",
                state: dayObj.state || "",
                city: dayObj.city || "",
                lat: act.lat,
                lng: act.lng,
                day: dayObj.day || "",
                index: i + 1,
                type: "activity"
            });

            wrapper.appendChild(left);
            wrapper.appendChild(content);
            daySection.appendChild(wrapper);
        });

        const extras = document.createElement("div");
        extras.className = "day-extra-card space-y-4";

        const transportBlock = document.createElement("div");
        transportBlock.className = "info-chip-group";

        transportBlock.innerHTML = `
          <h3 class="font-semibold text-lg">Transport on this day</h3>
          <div class="flex flex-wrap gap-2 mt-2">
            ${
                transport.length
                    ? transport.map((item) => `
                        <div class="transport-card">
                            ${item}
                        </div>
                    `).join("")
                    : `<div class="text-sm text-slate-500">Not specified</div>`
            }
          </div>
        `;

        extras.appendChild(transportBlock);

        const stayFoodGrid = document.createElement("div");
        stayFoodGrid.className = "stay-food-grid";

        const accommodations = dayObj.accommodations || [];
        const restaurants = dayObj.restaurants || [];

        const accommodationText =
            dayObj.accommodation_specific ||
            (accommodations.length ? accommodations.join(", ") : "");

        const restaurantText =
            dayObj.restaurant_specific ||
            (restaurants.length ? restaurants.join(", ") : "");

        if (accommodationText) {
            const accommodationCard = createLocationCard({
                label: "Accommodation",
                title: accommodationText,
                image: "",
                description: "",
                place: accommodationText,
                time: "",
                state: dayObj.state || "",
                city: dayObj.city || "",
                lat: "",
                lng: "",
                day: dayObj.day || "",
                index: "A",
                type: "accommodation"
            });

            stayFoodGrid.appendChild(accommodationCard);
        }

        if (restaurantText) {
            const restaurantCard = createLocationCard({
                label: "Restaurant",
                title: restaurantText,
                image: "",
                description: "",
                place: restaurantText,
                time: "",
                state: dayObj.state || "",
                city: dayObj.city || "",
                lat: "",
                lng: "",
                day: dayObj.day || "",
                index: "R",
                type: "restaurant"
            });

            stayFoodGrid.appendChild(restaurantCard);
        }

        if (stayFoodGrid.children.length > 0) {
            extras.appendChild(stayFoodGrid);
        }

        daySection.appendChild(extras);
        timeline.appendChild(daySection);
    });
}

function createLocationCard({
    label,
    title,
    image,
    description,
    place,
    time,
    state,
    city,
    lat,
    lng,
    day,
    index,
    type
}) {
    const content = document.createElement("article");

    // 这行非常重要：map marker 靠 .map-item 找卡片
    content.className = `timeline-content map-item ${type}`;

    content.dataset.day = day;
    content.dataset.index = index;
    content.dataset.type = type;
    content.dataset.title = title || "";
    content.dataset.place = place || "";
    content.dataset.time = time || "";
    content.dataset.state = state || "";
    content.dataset.city = city || "";
    content.dataset.country = itinerary?.country || "";

    if (lat !== undefined && lat !== null && lat !== "") {
        content.dataset.lat = lat;
    }

    if (lng !== undefined && lng !== null && lng !== "") {
        content.dataset.lng = lng;
    }

    const typeBadgeClass = getBadgeClass(type);

    content.innerHTML = `
        ${image ? `<img src="${image}" class="card-image">` : ""}

        <div class="card-body">
            <div class="flex justify-between items-center">
                <span class="${typeBadgeClass}">${label}</span>
                ${time ? `<span class="text-sm text-gray-500">${time}</span>` : ""}
            </div>

            <h3 class="card-title">${title || "Untitled"}</h3>

            ${description ? `<p class="card-desc">${description}</p>` : ""}

            ${place ? `<p class="card-meta"><b>Place:</b> ${place}</p>` : ""}
            <p class="card-meta"><b>State + City:</b> ${state || ""}, ${city || ""}</p>
        </div>
    `;

    return content;
}

function getBadgeClass(type) {
    if (type === "restaurant") {
        return "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-700";
    }
    if (type === "accommodation") {
        return "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-700";
    }
    return "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700";
}

// ===== MAP =====
// 初始化地图（在 Google Maps API 加载完成后）,要加保护
function initMap() {
    if (!itinerary) return;

    const mapEl = document.getElementById("map");
    if (!mapEl) return;

    const defaultCenter = { lat: -31.9523, lng: 115.8613 };

    map = new google.maps.Map(mapEl, {
        center: defaultCenter,
        zoom: 10,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true
    });

    renderMapMarkers();
}

function geocodeAddress(geocoder, address) {
    return new Promise((resolve, reject) => {
        geocoder.geocode({ address }, (results, status) => {
            if (status === "OK" && results && results.length > 0) {
                resolve(results[0].geometry.location);
            } else if (status === "ZERO_RESULTS") {
                resolve(null);
            } else {
                reject(status);
            }
        });
    });
}

async function renderMapMarkers() {
    const items = document.querySelectorAll(".map-item");
    const bounds = new google.maps.LatLngBounds();
    const geocoder = new google.maps.Geocoder();

    let markerCount = 0;

    for (const el of items) {
        const type = el.dataset.type;

        // 只给 activity 做地图 marker
        if (type !== "activity") {
            continue;
        }

        const title = el.dataset.title || "Location";
        const place = el.dataset.place || "";
        const city = el.dataset.city || "";
        const state = el.dataset.state || "";
        const country = el.dataset.country || "";

        let lat = parseFloat(el.dataset.lat);
        let lng = parseFloat(el.dataset.lng);

        // 如果数据库/API 没有 lat/lng，就用地址文字 geocode
        if (Number.isNaN(lat) || Number.isNaN(lng)) {
            const address = [place, city, state, country]
                .filter(Boolean)
                .join(", ");

            console.log("Geocoding address:", address);

            if (!address) {
                continue;
            }

            try {
                const location = await geocodeAddress(geocoder, address);

                if (!location) {
                    console.warn("No geocode result for:", address);
                    continue;
                }

                lat = location.lat();
                lng = location.lng();

                el.dataset.lat = lat;
                el.dataset.lng = lng;
            } catch (err) {
                console.warn("Geocoding failed:", address, err);
                continue;
            }
        }

        const marker = new google.maps.Marker({
            position: { lat, lng },
            map,
            title,
            icon: getMarkerIcon(type),
            animation: google.maps.Animation.DROP
        });

        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div style="min-width:180px;">
                    <div style="font-weight:700; margin-bottom:6px;">${title}</div>
                    <div style="font-size:13px; color:#555; text-transform:capitalize;">${type}</div>
                    ${place ? `<div style="margin-top:6px; font-size:13px;">${place}</div>` : ""}
                    ${el.dataset.time ? `<div style="margin-top:4px; font-size:13px;"><b>Time:</b> ${el.dataset.time}</div>` : ""}
                </div>
            `
        });

        marker.addListener("click", () => {
            highlightCard(el);
            focusMapLocation(lat, lng, marker, infoWindow);
            scrollCardIntoView(el);
        });

        el.addEventListener("click", () => {
            focusMapLocation(lat, lng, marker, infoWindow);
            highlightCard(el);
        });

        allMapMarkers.push({ marker, card: el, infoWindow });
        bounds.extend({ lat, lng });
        markerCount += 1;
    }

    if (markerCount > 0) {
        map.fitBounds(bounds);
    }
}

function getMarkerIcon(type) {
    if (type === "restaurant") {
        return "http://maps.google.com/mapfiles/ms/icons/red-dot.png";
    }
    if (type === "accommodation") {
        return "http://maps.google.com/mapfiles/ms/icons/blue-dot.png";
    }
    return "http://maps.google.com/mapfiles/ms/icons/green-dot.png";
}

function focusMapLocation(lat, lng, marker, infoWindow) {
    if (!map) return;

    map.panTo({ lat, lng });
    map.setZoom(13);

    if (activeInfoWindow) {
        activeInfoWindow.close();
    }

    infoWindow.open({
        anchor: marker,
        map
    });

    activeInfoWindow = infoWindow;
}

function scrollCardIntoView(el) {
    el.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}

// ===== OBSERVER =====
function setupObserver() {
    const indicator = document.getElementById("current-indicator");
    const observedItems = document.querySelectorAll(".map-item");

    if (!indicator || observedItems.length === 0) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;

                const el = entry.target;
                const type = el.dataset.type || "item";
                const title = el.dataset.title || "";
                const day = el.dataset.day || "";
                const index = el.dataset.index || "";

                highlightCard(el);

                if (type === "activity") {
                    indicator.innerText = `Day ${day} - Activity ${index}: ${title}`;
                } else if (type === "accommodation") {
                    indicator.innerText = `Day ${day} - Accommodation: ${title}`;
                } else if (type === "restaurant") {
                    indicator.innerText = `Day ${day} - Restaurant: ${title}`;
                }

                const lat = parseFloat(el.dataset.lat);
                const lng = parseFloat(el.dataset.lng);

                if (map && !Number.isNaN(lat) && !Number.isNaN(lng)) {
                    map.panTo({ lat, lng });
                }
            });
        },
        {
            threshold: 0.5
        }
    );

    observedItems.forEach((el) => observer.observe(el));
}

function highlightCard(el) {
    document.querySelectorAll(".timeline-content").forEach((item) => {
        item.classList.remove("active");
    });
    el.classList.add("active");
}

// ===== LIKE / FAVORITE / COMMENT =====
function setupInteractionButtons() {
    const likeBtn = document.getElementById("like-btn");
    const favBtn = document.getElementById("fav-btn");
    const commentBtn = document.getElementById("comment-btn");
    const commentBox = document.getElementById("comment-box");

    let liked = false;
    let favorited = false;

    if (likeBtn) {
        likeBtn.addEventListener("click", () => {
            liked = !liked;
            likeBtn.classList.toggle("bg-blue-500", liked);
            likeBtn.classList.toggle("text-white", liked);
            likeBtn.classList.toggle("bg-gray-200", !liked);
            likeBtn.innerText = liked ? "👍 Liked" : "👍 Like";
        });
    }

    if (favBtn) {
        favBtn.addEventListener("click", () => {
            favorited = !favorited;
            favBtn.classList.toggle("bg-yellow-400", favorited);
            favBtn.classList.toggle("text-white", favorited);
            favBtn.classList.toggle("bg-gray-200", !favorited);
            favBtn.innerText = favorited ? "⭐ Favorited" : "⭐ Favorite";
        });
    }

    if (commentBtn && commentBox) {
        commentBtn.addEventListener("click", () => {
            const value = commentBox.value.trim();
            if (!value) {
                alert("Please enter a comment before posting.");
                return;
            }

            alert(`Comment posted:\n${value}`);
            commentBox.value = "";
        });
    }
}