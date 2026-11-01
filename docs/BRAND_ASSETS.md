# Savor brand artwork

The app uses the original transparent logo from the cover of the team's [Savor slide deck](https://docs.google.com/presentation/d/1N6y2OpoZMCtfjQK8p1R13SdhUtmzxv_8-VMkZ6Y31qM/edit?usp=drivesdk).

- `frontend/src/assets/savor-logo.png`: the unchanged 2048 × 768 image from cover slide `p`, image element `h7f8fb2bf086fe67_2_16`. Used in the app header, sidebar, footer and loading screens.
- `frontend/src/assets/savor-icon.png`: a square Mac/browser icon using the leaf/person emblem selected from the same logo, on the deck's cream background. The original logo's crop rectangle is `(78, 50, 537, 715)` in pixels; its proportions and colors are preserved.
- `desktop/icon.icns`: the native Mac icon converted from `savor-icon.png`.

The desktop build copies the canonical wordmark into its packaged splash page. Development startup creates an ignored copy beside that page. Keep the wordmark's aspect ratio and transparent background. The green gradients and orange circle belong to the source artwork; do not replace them with a generic leaf or recreate the lettering with a font.
