```javascript
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const logoutBtn = document.getElementById("logoutBtn");

    if (!logoutBtn) {
        console.warn("Logout button la hetan iha HTML.");
        return;
    }

    logoutBtn.addEventListener("click", async () => {
        const confirmed = window.confirm(
            "Ita hakarak sai hosi sistema?"
        );

        if (!confirmed) return;

        logoutBtn.disabled = true;
        logoutBtn.querySelector("span:last-child").textContent =
            "Logging out...";

        try {
            const response = await fetch("/api/v1/auth/logout", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            });

            if (!response.ok) {
                throw new Error("Logout la konsege.");
            }

            window.location.replace("/login.html");
        } catch (error) {
            console.error("Logout error:", error);

            alert(
                "La konsege sai hosi sistema. " +
                "Favor koko fali."
            );

            logoutBtn.disabled = false;
            logoutBtn.querySelector("span:last-child").textContent =
                "Logout";
        }
    });
});
```