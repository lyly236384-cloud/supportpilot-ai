export const DEFAULT_PAGE_SIZE = 15;

export function previousPageOffset(offset, pageSize = DEFAULT_PAGE_SIZE) {
  return Math.max(0, offset - pageSize);
}

export function shouldReloadPreviousPage(page) {
  return page.items.length === 0 && page.offset > 0 && page.total > 0;
}
