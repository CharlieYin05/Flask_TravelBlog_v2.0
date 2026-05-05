document.addEventListener("DOMContentLoaded", () => {
  const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";

  // Add login check for Post button
  const postLink = document.getElementById("post-link");
  if (postLink) {
    postLink.addEventListener("click", (e) => {
      if (!isLoggedIn) {
        e.preventDefault();
        alert("Please sign in to create a post.");
        window.location.href = "../pages/sign-in.html";
      }
    });
  }

  // Live search functionality
  const searchInput = document.getElementById("search-input");
  const resultsContainer = document.getElementById("search-results");
  let searchTimeout;

  if (searchInput && resultsContainer) {
    searchInput.addEventListener("input", (e) => {
      const query = e.target.value.trim();

      // Clear timeout if it exists
      clearTimeout(searchTimeout);

      // Clear results if query is empty
      if (!query) {
        resultsContainer.innerHTML = '';
        return;
      }

      // Debounce search requests
      searchTimeout = setTimeout(() => {
        performSearch(query);
      }, 300);
    });
  }

  /**
   * Perform AJAX search
   */
  async function performSearch(query) {
    try {
      const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error('Search failed');
      }

      const results = await response.json();
      renderResults(results, query);
    } catch (error) {
      console.error('Search error:', error);
      resultsContainer.innerHTML = '<p class="error-message">Search failed. Please try again.</p>';
    }
  }

  /**
   * Render search results
   */
  function renderResults(results, query) {
    if (results.length === 0) {
      resultsContainer.innerHTML = `<p class="no-results">No itineraries found matching "${query}"</p>`;
      return;
    }

    const html = results.map(result => createResultBox(result)).join('');
    resultsContainer.innerHTML = html;
  }

  /**
   * Create HTML for a single result box
   */
  function createResultBox(itinerary) {
    const coverImage = itinerary.cover_image_url
      ? `/static/${itinerary.cover_image_url}`
      : '/static/images/placeholder.jpg';

    return `
      <div class="result-box">
        <div class="result-image">
          <img src="${coverImage}" alt="${escapeHtml(itinerary.title)}" />
        </div>
        <div class="result-content">
          <h3 class="result-title">${escapeHtml(itinerary.title)}</h3>
          <p class="result-country">${escapeHtml(itinerary.country)}</p>
          <p class="result-duration">${itinerary.total_days} days</p>
          <a href="/itinerary/${itinerary.id}" class="result-link">View Itinerary</a>
        </div>
      </div>
    `;
  }

  /**
   * Escape HTML to prevent XSS
   */
  function escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }
});
