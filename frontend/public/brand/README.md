# Brand assets — drop your Figma exports here

Every file below is **optional**: the app renders a CSS/flag fallback when a
file is missing, and automatically uses the real asset once you add it. So you
can ship now and drop these in whenever they're exported.

| File (in this folder)        | Used by                          | Fallback if missing                     |
|------------------------------|----------------------------------|------------------------------------------|
| `fwc2026.ttf`                | All display headings & scores    | Archivo (bundled Google font)            |
| `background.png`             | App background (geometric board) | royal-blue radial gradient               |
| `logo.svg` / `logo.png`      | Nav + hero "26" lockup           | CSS "26" badge                           |
| `logo-white.png`             | Hero on dark/blue sections       | `logo.png`, then CSS badge               |
| `trophy.png`                 | Hero + bracket centre            | gold "26" badge                          |
| `jerseys/<iso>.png`          | Teams page shirt grid            | white flag-card                          |

### Jerseys
Export one PNG per nation named by its **lowercase ISO-2 code**, e.g.
`jerseys/fr.png`, `jerseys/br.png`, `jerseys/ar.png`. The ISO code for each team
comes from the API (`flag_iso`); transparent background, ~400px tall works well.

### Font
`fwc2026.woff2` is wired via `@font-face` in `app/globals.css`. Drop the file in
and reload — no code change needed. (A `.woff` alongside it is used as a fallback
for older browsers.)
