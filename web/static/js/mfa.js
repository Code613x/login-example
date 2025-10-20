document.addEventListener("DOMContentLoaded", () => {
  if (!sessionStorage.getItem("temp_token")){
    window.location.href = "/";
  }
  const submitBtn = document.getElementById("submit-btn");
  if (!submitBtn) return;
  submitBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    const code = (document.getElementById("mfaCode")?.value || "").trim();
    if (!/^\d{6}$/.test(code)) {
      alertbox.render({
        alertIcon: "warning",
        title: "Invalid Code",
        btnTitle: "Ok",
        themeColor: "#FF8800ff",
        btnColor: "#007bff",
        border: true,
      });
      await delay(5000);
      return;
    }
    try {
      const token = sessionStorage.getItem("temp_token");
      const res = await fetch("/login_mfa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ temp_token: token, code: code }),
      });
      const data = await res.json();
      if (res.status == 200) {
        sessionStorage.removeItem("temp_token");
        window.location.href = "dashboard";
      } else if (res.status == 400) {
        alertbox.render({
          alertIcon: "error",
          title: "Incorrect Code",
          message: data?.msg,
          btnTitle: "Ok",
          themeColor: "#ff0000ff",
          btnColor: "#007bff",
          border: true,
        });
      } else if (res.status == 403) {
        alertbox.render({
          alertIcon: "warning",
          title: "Session Expired",
          message: "This session has expired. Please log in again.",
          themeColor: "#FF8800ff",
          btnColor: "#007bff",
          border: true,
          hideBtn: true
        });
        await delay(3000);
        sessionStorage.removeItem("temp_token");
        window.location.href = "/";
      } else {
        alertbox.render({
          alertIcon: "error",
          title: "Error",
          message: data?.msg || "Unknown error",
          btnTitle: "Ok",
          themeColor: "#ff0000ff",
          btnColor: "#007bff",
          border: true,
        });
      }
    } catch (err) {
      alertbox.render({
        alertIcon: "error",
        title: "MFA Error",
        message: err?.message || String(err),
        btnTitle: "Ok",
        themeColor: "#ff0000ff",
        btnColor: "#007bff",
        border: true,
      });
    }
  });
});

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

document.getElementById("cancelBtn")?.addEventListener("click", () => {
  sessionStorage.removeItem("temp_token");
  window.location.href = "/"; 
});
