document.getElementById('settings')?.addEventListener("click", async () => {
  window.location.href = "settings";
});

document.getElementById("experience").textContent = (new Date().getFullYear() - 2022) + " years";