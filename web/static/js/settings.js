function sha256(str) {
    return CryptoJS.SHA256(str).toString(CryptoJS.enc.Hex);
}
let passwordVerified = false;


const passwordChangeForm = document.getElementById("passwordChangeForm");
if (passwordChangeForm) {
    passwordChangeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        let res;
        if(!(document.getElementById("newPassword")?.value == document.getElementById("confirmPassword")?.value)){
                        alertbox.render({
                alertIcon: "error",
                title: "Error",
                message: "Passwords do not match",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        }
        try {
            res = await fetchWithAuth("http://127.0.0.1:5000/change_password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    password: sha256(document.getElementById("currentPassword")?.value || ""),
                    new_password: sha256(document.getElementById("newPassword")?.value || ""),
                }),
            });
        } catch (err) {
            res = null;
        }
        if (!res) {
            alertbox.render({
                alertIcon: "error",
                title: "Error",
                message: "Unexpected error, no response from server",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        }
        if (res.status === 429) {
            alertbox.render({
                alertIcon: "error",
                title: "Too Many Requests",
                message: "Try again later",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        } 
        const data = await res.json();
        if (res.status === 200){
            alertbox.render({
                alertIcon: "success",
                title: "Password Changed",
                message: "Your password has been successfully changed. You will now be logged out.",
                btnTitle: "Ok",
                themeColor: "#00ff1aff",
                btnColor: "#007bff",
                border: true,
                hideBtn: true
            });
            await delay(3000);
            await logout_all();
            return;
        } 
        alertbox.render({
            alertIcon: "error",
            title: "Error",
            message: data?.msg || "Something went wrong",
            btnTitle: "Ok",
            themeColor: "#ff0000ff",
            btnColor: "#007bff",
            border: true,
        });  
    });
}

const usernameForm = document.getElementById("usernameForm");
if (usernameForm) {
    usernameForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        let res;
        try {
            res = await fetchWithAuth("http://127.0.0.1:5000/change_username", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    new_username: document.getElementById("newUsername")?.value || "",
                }),
            });
        } catch (err) {
            res = null;
        }
        if (!res) {
            alertbox.render({
                alertIcon: "error",
                title: "Error",
                message: "Unexpected error, no response from server",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        }
        const data = await res.json();
        if (res.status === 429) {
            alertbox.render({
                alertIcon: "error",
                title: "Too Many Requests",
                message: "Try again later",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        } else if (res.status === 200){
            alertbox.render({
                alertIcon: "success",
                title: "Username Changed",
                message: "Your username has been successfully updated",
                btnTitle: "Ok",
                themeColor: "#00ff1aff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        } 
        alertbox.render({
            alertIcon: "error",
            title: "Error",
            message: data?.msg || "Something went wrong",
            btnTitle: "Ok",
            themeColor: "#ff0000ff",
            btnColor: "#007bff",
            border: true,
        });  
    });
}

const mfaForm = document.getElementById("2faForm");
if (mfaForm) {
    mfaForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const selectedOption = document.querySelector('input[name="2faOption"]:checked')?.value;
        if (!selectedOption) {
            alertbox.render({
                alertIcon: "error",
                title: "Error",
                message: "You have to select an option",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        }
        if (selectedOption === "disable") {
            deactivate_mfa();
        } else if (selectedOption === "mfa") {
            window.location.href = "/mfa_activation";
        }
    });
}

async function deactivate_mfa() {
        if (!passwordVerified) {
            const overlay = document.getElementById("passwordOverlay");
            if (overlay) {
                const pwField = document.getElementById("password");
                if (pwField) pwField.value = "";
                overlay.style.display = "flex";
            }
            return; 
        }
        const passwordValue = document.getElementById("password")?.value || "";
        let res;
        try {
            res = await fetchWithAuth("http://127.0.0.1:5000/deactivate_mfa", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    password: sha256(passwordValue),
                }),
            });
        } catch (err) {
            res = null;
        }
        
        if (!res) {
            passwordVerified = false;
            alertbox.render({
                alertIcon: "error",
                title: "Error",
                message: "Unexpected error, no response from server",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        }
        if (res.status === 429) {
            passwordVerified = false;
            alertbox.render({
                alertIcon: "error",
                title: "Too Many Requests",
                message: "Try again later",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
            return;
        }
        const data = await res.json();
        if (res.ok) {
            alertbox.render({
                alertIcon: "success",
                title: "Success",
                message: "Your 2FA settings were updated successfully",
                btnTitle: "Ok",
                themeColor: "#28a745",
                btnColor: "#007bff",
                border: true,
            });
        } else {
            passwordVerified = false;
            alertbox.render({
                alertIcon: "error",
                title: "Failed",
                message: data?.msg || "Something went wrong",
                btnTitle: "Ok",
                themeColor: "#ff0000ff",
                btnColor: "#007bff",
                border: true,
            });
        }
}

const passwordForm = document.getElementById("passwordForm");
if (passwordForm) {
    passwordForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        passwordVerified = true;
        const overlay = document.getElementById("passwordOverlay");
        if (overlay) overlay.style.display = "none";
        await deactivate_mfa();
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    let res;
    try {
        res = await fetchWithAuth("http://127.0.0.1:5000/get_mfa", {
                    method: "POST",
                });
    } catch (err) {
        res = null;
    }
    if (!res) {
        alertbox.render({
            alertIcon: "error",
            title: "Error",
            message: "Unexpected error, no response from server",
            btnTitle: "Ok",
            themeColor: "#ff0000ff",
            btnColor: "#007bff",
            border: true,
        });
        return;
    }
    if (res.status === 429) {
        passwordVerified = false;
        alertbox.render({
            alertIcon: "error",
            title: "Too Many Requests",
            message: "Try again later",
            btnTitle: "Ok",
            themeColor: "#ff0000ff",
            btnColor: "#007bff",
            border: true,
        });
        return;
    }
    if(res?.ok){
        const data = await res.json();
        const radios = document.querySelectorAll('input[name="2faOption"]');
        if (data?.mfa) {
            if (radios && radios.length >= 2) {
                radios[0].checked = false;
                radios[1].checked = true;
            }
        } else {
            if (radios && radios.length >= 2) {
                radios[0].checked = true;
                radios[1].checked = false;
            }
        }
    } else {
        alertbox.render({
            alertIcon: "error",
            title: "Error",
            message: "Unexpected error, no response from server",
            btnTitle: "Ok",
            themeColor: "#ff0000ff",
            btnColor: "#007bff",
            border: true,
        });
        return;
    }
});

document.getElementById("homeBtn")?.addEventListener("click", () => {
    window.location.href = "/"; 
});

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
