function sha256(str) {
  return CryptoJS.SHA256(str).toString(CryptoJS.enc.Hex);
}
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("resetForm");
    const tokenInput = document.getElementById("token");
    const newPasswordInput = document.getElementById("new_password");
    const confirmPasswordInput = document.getElementById("confirm_password");

    form.addEventListener("submit", async function(event) {
        event.preventDefault();

        const token = tokenInput.value;
        const password = newPasswordInput.value;
        const confirm = confirmPasswordInput.value;

        let errors = [];
        if (password.length < 4) errors.push("Password must be at least 4 characters long.");
        if (password !== confirm) errors.push("Passwords do not match.");

        if (errors.length > 0) {
            alertbox.render({
                alertIcon: "error",
                title: "Error",
                message: errors.join("\n"),
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        }

        try {
            const response = await fetch("/reset-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    token: token,
                    new_password: sha256(password),
                    confirm_password: sha256(confirm)
                })
            });

            const text = await response.text();

            if (!response.ok) {
                alertbox.render({
                    alertIcon: "error",
                    title: "Error",
                    message: text,
                    btnTitle: "Ok",
                    themeColor: "#ff0000ff",
                    btnColor: "#007bff",
                    border: true,
                });
            } else {
                alertbox.render({
                    alertIcon: "success",
                    title: "Success",
                    message: "Password has been reset successfully!",
                    btnTitle: "Ok",
                    themeColor: "#00c853ff",
                    btnColor: "#007bff",
                    border: true,
                    hideBtn: true
                });
                setTimeout(() => window.location.href = "/", 2000);
            }
        } catch (err) {
            alertbox.render({
                alertIcon: "error",
                title: "Error",
                message: err?.message || String(err),
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
        }
    });
});
