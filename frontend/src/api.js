export async function api(path, body, method = "POST") {
  const r = await fetch(`/api${path}`, {
    method: body === undefined ? "GET" : method,
    credentials: "same-origin",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let data;
  try {
    data = await r.json();
  } catch {
    throw new Error(
      "The local service is unavailable. Check that Savor is running.",
    );
  }
  if (!r.ok) {
    const msg = Array.isArray(data.detail)
      ? data.detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join("; ")
      : data.detail;
    throw Object.assign(
      new Error(msg || "Something went wrong. Please try again."),
      { status: r.status },
    );
  }
  return data;
}
