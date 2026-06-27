const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `${response.status} ${path}`;
    try {
      const payload = await response.json();
      if (payload?.error?.message) {
        detail = payload.error.message;
      }
    } catch {
      // Keep default detail when body is not JSON.
    }
    throw new Error(`API request failed: ${detail}`);
  }

  return response.json();
}

export async function requestFormData(path, formData, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    ...options,
    body: formData,
  });

  if (!response.ok) {
    let detail = `${response.status} ${path}`;
    try {
      const payload = await response.json();
      if (payload?.error?.message) {
        detail = payload.error.message;
      }
    } catch {
      // Keep default detail when body is not JSON.
    }
    throw new Error(`API request failed: ${detail}`);
  }

  return response.json();
}

export async function requestChatStream(payload, onEvent) {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} /api/chat/stream`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // Normalize line endings: \r\n → \n for SSE parsing (Windows servers)
    const text = decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    buffer += text;
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const dataLine = chunk.split("\n").find((line) => line.startsWith("data:"));
      if (!dataLine) continue;

      const json = dataLine.slice(5).trim();
      if (!json) continue;
      onEvent(JSON.parse(json));
    }
  }
}
