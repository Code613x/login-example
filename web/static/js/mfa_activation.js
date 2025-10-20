async function fetchMfaSetup() {
  try {
    const res = await fetchWithAuth("/init_mfa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await res.json();
    if (data?.mfa) {
      if (document.referrer) {
        window.location.href = document.referrer;
      } else {
        window.location.href = "/";
      }
    } else if (data?.qr_code_data) {
      const qrEl = document.getElementById("qr");
      if (qrEl) qrEl.src = data.qr_code_data;
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
}

document.getElementById("activate-btn")?.addEventListener("click", async (e) => {
  e.preventDefault();
  const codeEl = document.getElementById("mfa-code");
  const passEl = document.getElementById("mfa-password");
  const code = codeEl?.value.trim() || "";
  const passwordRaw = passEl?.value || "";

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
    const res = await fetchWithAuth("/activate_mfa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: code, password: sha256(passwordRaw) }),
    });
    let data;
    try { data = await res.json(); } catch { data = {}; }
    if (res?.ok) {
      alertbox.render({
        alertIcon: "success",
        title: "MFA successfully enabled",
        message: "You will be redirected to the dashboard",
        btnTitle: "Ok",
        themeColor: "#00ff1aff",
        btnColor: "#007bff",
        border: true,
        hideBtn: true
      });
      await delay(4000);
      if (document.referrer) {
        window.location.href = document.referrer;
      } else {
        window.location.href = "/";
      }
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

window.onload = function () {
  fetchMfaSetup();
};

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function sha256(str) {
  return CryptoJS.SHA256(str).toString(CryptoJS.enc.Hex);
}

document.getElementById("cancelBtn")?.addEventListener("click", () => {
  if (document.referrer) {
    window.location.href = document.referrer;
  } else {
    window.location.href = "/";
  }
});
