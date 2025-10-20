document.getElementById("logoutBtn")?.addEventListener("click", async () => {
  await logout();
});

async function logout() {
    try {
      await fetchWithAuth("http://127.0.0.1:5000/logout", {
        method: "POST",
      });
    } catch {}

    window.location.href = "/";
}

async function logout_all() {
    try {
      await fetchWithAuth("http://127.0.0.1:5000/logout_all", {
        method: "POST",
      });
    } catch {}

    window.location.href = "/";
}
