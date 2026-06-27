export function formatRate(value, fallback = "—") {
  const number = Number(value);
  if (Number.isNaN(number)) return fallback;
  return `${Math.round(number * 100)}%`;
}

export function formatDurationMs(value, fallback = "—") {
  const number = Number(value);
  if (Number.isNaN(number)) return fallback;
  if (number < 1000) return `${Math.round(number)}ms`;
  return `${(number / 1000).toFixed(1)}s`;
}

export function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("zh-CN");
}

export function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatWaitMinutes(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000));
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h`;
}

export function formatNumber(value, fallback = "—") {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return fallback;
  return Number(value).toLocaleString("zh-CN");
}

export function displayMetric(value, loading = false, fallback = "—") {
  if (loading) return "—";
  if (value === undefined || value === null || Number.isNaN(Number(value))) return fallback;
  return formatNumber(value);
}
