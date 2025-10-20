function timeoutPromise(ms, promise) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Request timed out')), ms);
    promise.then(
      res => { clearTimeout(timer); resolve(res); },
      err => { clearTimeout(timer); reject(err); }
    );
  });
}

async function fetchWithAuth(url, options = {}) {
  if (!options.headers) options.headers = {};
  options = Object.assign({}, options);
  options.credentials = "include";

  try {
    let res = await timeoutPromise(15000, fetch(url, options));

    if (res.status === 401) {
      const refreshRes = await timeoutPromise(15000, fetch("http://127.0.0.1:5000/refresh", {
        method: "POST",
        credentials: "include",
      }));
    }

    return res;
  } catch (err) {
    throw err;
  }
}
