## 2026-10-28 - Manage aria-current in SPAs dynamically via JS
**Learning:** In Single Page Applications (SPAs) where navigation doesn't trigger a full page reload, the `aria-current` attribute needs to be managed dynamically using JavaScript. A hardcoded `aria-current` in the HTML might become stale or incorrect after navigation.
**Action:** When working on SPAs or dynamically loaded views without page reloads, always update the JS logic handling the view changes to appropriately add/remove the `aria-current="page"` attribute to the correct active navigation links.
