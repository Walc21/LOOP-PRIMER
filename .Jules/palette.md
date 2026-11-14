## 2026-10-26 - Dynamic Accessibility on Custom Navigation
**Learning:** When building custom tab interfaces, relying solely on CSS classes (like `.active`) for visual feedback leaves screen reader users behind. Bridging the visual state with the accessibility tree using `aria-current="page"` ensures equitable navigation.
**Action:** Always dynamically sync the `aria-current` attribute alongside visual `.active` classes in JavaScript event listeners for custom navigation elements.
