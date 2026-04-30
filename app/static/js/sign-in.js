const form = document.querySelector("form");
const emailInput = document.querySelector('input[name="email"]');
const errorMessage = document.getElementById("signin-error");

if (form && emailInput) {
    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        emailInput.value = emailInput.value.trim().toLowerCase();

        if (errorMessage) {
            errorMessage.textContent = "";
            errorMessage.classList.add("is-hidden");
        }

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.success) {
                window.location.href = data.redirect_url;
                return;
            }

            if (errorMessage && data.error) {
                errorMessage.textContent = data.error;
                errorMessage.classList.remove("is-hidden");
            }
        } catch (error) {
            if (errorMessage) {
                errorMessage.textContent = "Unable to sign in right now.";
                errorMessage.classList.remove("is-hidden");
            }
        }
    });
}
