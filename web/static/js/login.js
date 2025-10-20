function sha256(str) {
  return CryptoJS.SHA256(str).toString(CryptoJS.enc.Hex);
}
let captcha = false;
let captcha_answer = "";
let answer = "";
let tries = 0;
(function () {
  let ab = false;
  let score = 0;

  window.check = {
    get: () => ab,
    set: (value) => {
      if (!window.__MY_APP_READY__) {
        ab = true;
        return;
      }
      if (!ab) {
        ab = value;
      }
    },
    score: () => score,
    addScore: (points) => {
      score += points;
      if (score >= 70) {
        ab = true;
      }
    },
  };
})();
const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await login();
  });
}

const captchaForm = document.getElementById("captchaForm");
if (captchaForm) {
  captchaForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await login();
  });
}

const resetText = document.getElementById("reset-text");
resetText.addEventListener("click", async function () {
  const emailInput = document.getElementById("loginEmail");
  if (emailInput.value.length < 1) {
    alertbox.render({
      alertIcon: "error",
      title: "No email",
      message: "You have to enter your email.",
      btnTitle: "Ok",
      themeColor: "#ff0000ff",
      btnColor: "#007bff",
      border: true,
    });
  setTimeout(() => window.location.reload(), 2000);
  }

  try {
    const response = await fetch("/request-reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailInput.value }),
    });
    const data = await response.json();
    if (response?.ok) {
      alertbox.render({
        alertIcon: "success",
        title: "Reset link sent!",
        message: "Check your email",
        btnTitle: "Ok",
        themeColor: "#00ff1aff",
        btnColor: "#007bff",
        border: true,
      });
    } else {
      alertbox.render({
        alertIcon: "error",
        title: "Error",
        message: data?.msg,
        btnTitle: "Ok",
        themeColor: "#ff0000ff",
        btnColor: "#007bff",
        border: true,
      });
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

document
  .getElementById("captchaSubmitBtn")
  ?.addEventListener("click", async () => {
    captcha = true;
  });

async function login() {
  const emailInput = document.getElementById("loginEmail");
  const passwordInput = document.getElementById("loginPassword");
  const captchaInput = document.getElementById("captchaInput");
  if (!emailInput || !passwordInput) return;
  ver();
  const email = emailInput.value;
  const password = sha256(passwordInput.value);
  const score = check.score();
  if (captcha && captchaInput) {
    answer = captchaInput.value;
  }
  try {
    const res = await fetch("http://127.0.0.1:5000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        score,
        hash: sha256(email + password + String(score)),
        answer,
        captcha_answer,
      }),
      credentials: "include",
    });
    if (res?.status === 429) {
      alertbox.render({
        alertIcon: "error",
        title: "Too Many Requests",
        message: "Try again later",
        btnTitle: "Ok",
        themeColor: "#ff0000ff",
        btnColor: "#007bff",
        border: true,
      });

      const overlay = document.getElementById("captchaOverlay");
      if (overlay) overlay.style.display = "none";
      return;
    } else if(res?.status === 401){
      passwordInput.value = "";
    }
    const data = await res.json();
    if (data?.captcha_required) {
      const overlay = document.getElementById("captchaOverlay");
      const img = document.getElementById("captchaImage");
      if (overlay && img) {
        img.src = data.captcha_img;
        overlay.style.display = "flex";
      }
      captcha_answer = data.captcha_answer;
      return;
    } else {
      const overlay = document.getElementById("captchaOverlay");
      if (overlay) overlay.style.display = "none";
    }
    if (data?.mfa_required) {
      sessionStorage.setItem("temp_token", data.temp_token);
      window.location.href = "mfa";
    } else if (res.status === 200) {
      window.location.href = "dashboard";
    } else {
      tries++;
      if (tries > 2) {
        const resetText = document.getElementById("reset-text");
        resetText.style.display = "flex";
      }
      alertbox.render({
        alertIcon: "error",
        title: "Login Failed",
        message: data?.msg,
        btnTitle: "Ok",
        themeColor: "#ff0000ff",
        btnColor: "#007bff",
        border: true,
      });
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
}

const registerForm = document.getElementById("registerForm");
if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await register();
  });
}

async function register() {
  const emailInput = document.getElementById("regEmail");
  const usernameInput = document.getElementById("regUsername");
  const passwordInput = document.getElementById("regPassword");
  const captchaInput = document.getElementById("captchaInput");
  if (!emailInput || !usernameInput || !passwordInput) return;
  ver();
  const email = emailInput.value;
  const username = usernameInput.value;
  const password = sha256(passwordInput.value);
  const score = check.score();
  if (captcha && captchaInput) {
    answer = captchaInput.value;
  }
  try {
    const res = await fetch("http://127.0.0.1:5000/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        username,
        password,
        score,
        hash: sha256(email + username + password + String(score)),
        answer,
        captcha_answer,
      }),
      credentials: "include",
    });
    if (res?.status === 429) {
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
    if (data?.captcha_required) {
      const overlay = document.getElementById("captchaOverlay");
      const img = document.getElementById("captchaImage");
      if (overlay && img) {
        img.src = data.captcha_img;
        overlay.style.display = "flex";
      }
      captcha_answer = data.captcha_answer;
      return;
    } else {
      const overlay = document.getElementById("captchaOverlay");
      if (overlay) overlay.style.display = "none";
    }

    if (res?.status == 201) {
      window.location.href = "dashboard";
    } else {
      alertbox.render({
        alertIcon: "error",
        title: "Registration Failed",
        message: data?.msg,
        btnTitle: "Ok",
        themeColor: "#ff0000ff",
        btnColor: "#007bff",
        border: true,
      });
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
}
document.addEventListener("DOMContentLoaded", async () => {
  const hps = document.getElementsByName("email");
  Array.from(hps).forEach((hp) => {
    try {
      hp.style.width = "10px";
      hp.style.height = "10px";
      hp.style.position = "absolute";
      hp.style.opacity = "1";
      hp.style.pointerEvents = "none";
      hp.style.border = "none";
      hp.tabIndex = -1;
      hp.value = "";
    } catch {}
  });

  try {
    const res = await fetchWithAuth("http://127.0.0.1:5000/check", {
      check: true,
    });
    if (res?.ok) window.location.href = "dashboard";
  } catch (e) {}

  ts();
});

const startTime = Date.now();
function ver() {
  const timeSpent = (Date.now() - startTime) / 1000;
  if (timeSpent < 9) {
    check.addScore((9 - timeSpent) * 10);
  }
}

let last = null;

document.addEventListener("mousemove", (e) => {
  const x = e.clientX;
  const y = e.clientY;
  if (x < 0 || y < 0 || x > window.innerWidth || y > window.innerHeight) {
    last = null;
    return;
  }
  const now = Date.now();
  const pos = { x, y, t: now };
  if (last) {
    const dx = pos.x - last.x;
    const dy = pos.y - last.y;
    const dist = Math.hypot(dx, dy);
    const dt = (now - last.t) / 1000;
    if (dist >= 50 && dt <= 0.4 && dist <= 200 && dt >= 0.06) {
      console.log(`Wykryto przeskok: ${dist}px w ${dt.toFixed(3)}s`);
      check.addScore(30);
    }
  }
  last = pos;
});

function ts() {
  if (navigator.webdriver) check.addScore(40);
  if (!navigator.plugins || navigator.plugins.length === 0) check.addScore(20);
  if (!navigator.languages || navigator.languages.length === 0)
    check.addScore(20);

  try {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    ctx.textBaseline = "top";
    ctx.font = "16px Arial";
    ctx.fillText("fingerprint-test", 2, 2);
    if (canvas.toDataURL().length < 3000) check.addScore(20);
  } catch {
    check.addScore(20);
  }

  try {
    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    const debugInfo =
      gl && gl.getExtension
        ? gl.getExtension("WEBGL_debug_renderer_info")
        : null;
    const renderer = debugInfo
      ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
      : "";
    if (renderer && renderer.toLowerCase().includes("swiftshader"))
      check.addScore(30);
  } catch {
    check.addScore(20);
  }
}
