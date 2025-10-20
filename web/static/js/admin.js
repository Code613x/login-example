// ===== UTILITY =====
async function fetchWithAuth(url, options = {}) {
  let token = localStorage.getItem("access_token");

  if (!options.headers) options.headers = {};
  if (token) options.headers["Authorization"] = "Bearer " + token;

  options.credentials = "include";

  let res = await fetch(url, options);

  if (res.status === 401) {
    const refreshRes = await fetch("/refresh", {
      method: "POST",
      credentials: "include",
    });
    const refreshData = await refreshRes.json();

    if (refreshRes.ok && refreshData.access_token) {
      localStorage.setItem("access_token", refreshData.access_token);
      options.headers["Authorization"] = "Bearer " + refreshData.access_token;
      res = await fetch(url, options);
    } else {
      localStorage.removeItem("access_token");
      alert("Session expired. Please login again.");
      window.location.href = "/";
      return;
    }
  }

  return res;
}

// ===== ADD PERMISSION =====
const addBtn = document.getElementById("addPermissionBtn");
addBtn.addEventListener("click", async () => {
  const identifier = document.getElementById("userIdentifier").value.trim();
  const permission = document.getElementById("newPermission").value.trim();
  const msgEl = document.getElementById("addPermissionMsg");

  if (!identifier || !permission) {
    msgEl.textContent = "Both fields are required!";
    msgEl.className = "error";
    return;
  }

  try {
    const res = await fetchWithAuth("/add_permission", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, permission }),
    });

    const data = await res.json();
    if (res.ok) {
      msgEl.textContent = data.msg || "Permission added!";
      msgEl.className = "success";
    } else {
      msgEl.textContent = data.msg || "Error";
      msgEl.className = "error";
    }
  } catch (err) {
    msgEl.textContent = "Connection error: " + err;
    msgEl.className = "error";
  }
});

// ===== DELETE USER =====
const deleteBtn = document.getElementById("deleteUserBtn");
deleteBtn.addEventListener("click", async () => {
  const identifier = document.getElementById("deleteIdentifier").value.trim();
  const msgEl = document.getElementById("deleteUserMsg");

  if (!identifier) {
    msgEl.textContent = "Required field!";
    msgEl.className = "error";
    return;
  }

  try {
    const res = await fetchWithAuth("/delete_user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier }),
    });

    const data = await res.json();
    if (res.ok) {
      msgEl.textContent = data.msg || "User deleted!";
      msgEl.className = "success";
    } else {
      msgEl.textContent = data.msg || "Error";
      msgEl.className = "error";
    }
  } catch (err) {
    msgEl.textContent = "Connection error: " + err;
    msgEl.className = "error";
  }
});

// ===== LOGOUT =====
const logoutBtn = document.getElementById("logoutBtn");
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("access_token");
  alert("Logged out!");
  window.location.href = "/";
});
