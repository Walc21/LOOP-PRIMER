## 2024-10-24 - Missing ARIA context in SPA navigation
**Learning:** In SPAs, the `active` visual class on navigation tabs isn't enough for screen readers. They need `aria-current="page"` to understand which view is currently loaded.
**Action:** Always dynamically toggle the `aria-current="page"` attribute alongside the active CSS class when building or modifying custom tab/navigation systems.
