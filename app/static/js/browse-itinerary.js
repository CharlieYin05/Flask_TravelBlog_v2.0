document.addEventListener("DOMContentLoaded", () => {

  const container = document.getElementById("card-container");

  // 从 Flask API get itineraries data and render cards
  fetch("/api/itineraries")
    .then(res => res.json())
    .then(data => {

      container.innerHTML = "";

      data.forEach(item => {

        const card = document.createElement("div");
        card.className = "itinerary-card";

        card.innerHTML = `
          <img src="/static/${item.cover || 'default.jpg'}" class="card-image">
          <div class="card-content">
            <div class="card-title">${item.title}</div>
            <div class="card-meta">
              ${item.country} • ${item.days} days
            </div>
          </div>
        `;

        //关键：跳 Flask route（不是 html）
        card.addEventListener("click", () => {
          window.location.href = `/itinerary/${item.id}`;
        });

        container.appendChild(card);
      });

    })
    .catch(err => {
      console.error("Failed to load itineraries:", err);
    });

});