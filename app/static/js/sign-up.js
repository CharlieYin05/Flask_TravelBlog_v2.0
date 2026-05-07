const form = document.querySelector("form");
const username = document.querySelector('input[name="username"]');
const email = document.querySelector('input[name="email"]');
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirm-password");
const errorMessage = document.getElementById("signup-error");
const USERNAME_PATTERN = /^[A-Za-z0-9_]+$/;
const USERNAME_MIN_LENGTH = 3;
const USERNAME_MAX_LENGTH = 20;
const PASSWORD_MIN_LENGTH = 8;

// Keep the main signup rules in one place for quick client-side feedback.
function validatePassword() {
    if (password.value && password.value.length < PASSWORD_MIN_LENGTH) {
        password.setCustomValidity("Password must be at least 8 characters long");
    } else {
        password.setCustomValidity("");
    }

    if (confirmPassword.value && password.value !== confirmPassword.value) {
        confirmPassword.setCustomValidity("Passwords do not match");
    } else {
        confirmPassword.setCustomValidity("");
    }
}

function validateUsername() {
    const trimmedUsername = username.value.trim();

    if (!trimmedUsername) {
        username.setCustomValidity("Username is required");
        return;
    }

    if (trimmedUsername.length < USERNAME_MIN_LENGTH || trimmedUsername.length > USERNAME_MAX_LENGTH) {
        username.setCustomValidity("Username must be between 3 and 20 characters");
        return;
    }

    if (!USERNAME_PATTERN.test(trimmedUsername)) {
        username.setCustomValidity("Username can only contain letters, numbers, and underscores");
        return;
    }

    username.setCustomValidity("");
}

if (form && username && password && confirmPassword) {
    username.addEventListener("input", validateUsername);
    password.addEventListener("input", validatePassword);
    confirmPassword.addEventListener("input", validatePassword);

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        if (username) {
            username.value = username.value.trim();
        }

        if (email) {
            email.value = email.value.trim().toLowerCase();
        }

        if (errorMessage) {
            errorMessage.textContent = "";
            errorMessage.classList.add("is-hidden");
        }

        validateUsername();
        validatePassword();

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
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
                errorMessage.textContent = "Unable to sign up right now.";
                errorMessage.classList.remove("is-hidden");
            }
        }
    });
}
