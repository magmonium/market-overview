# Where it lives

Type: grilling
Status: resolved

## Question

The Market Brief and the Song Reel share one repository, one `src/`, one data root and one render toolchain;
`song-video` is a **nested uv project** with its own environment, its own tests and its own ADRs.

1. **A third nested product**, `src/books-brief/`, beside `song-video/` — reusing `remotion/`, the vendored fonts,
   the bundled ffmpeg and the `deploy/` units. *(recommended)*
2. **A new repository**, with the render layer copied or vendored — clean ownership, duplicated toolchain.
3. **A product inside `market_overview/`** — rejected on the evidence: the brief's `paths.py` is explicit that the
   brief must not know about a sibling product, and that one-import-away is the coupling it refuses.

Also to settle: the data-root namespace (`resource/books/`, `output/books/`), the `store/` layout, and which ADRs
this product needs to write for itself.

⚠️ **Arrived from ticket 08:** books-brief depends on **`market_overview` as a library** — an editable path source,
inheriting its dependency tree (`curl_cffi`), exactly as `song-video` documents. It must **not** read the brief's run
artefacts (`store/<date>/facts.json`); depending on a *library* is the sanctioned sibling direction, depending on
another product's *output* is not. Decide here whether that holds.

## Answer

### A third nested product — `src/books-brief/`, following `song-video` exactly

Option 2 (a new repository) would duplicate the render toolchain. Option 3 (inside `market_overview/`) is refused by
the brief's own `paths.py`. And the nested pattern is **not a guess** — `song-video`'s `paths.py` documents every seam.

```
src/
├── market_overview/          the brief — the repository's own package
└── books-brief/              ← the new product, a self-contained project
    ├── pyproject.toml        deps: ["market-overview"], editable path source
    ├── uv.lock               its own environment
    ├── package.json          its own Remotion
    ├── tsconfig.json
    ├── books_brief/          ⚠️ the package sits *directly* in the project — no inner `src/`
    ├── remotion/             its own components (the reel has its own; it does NOT import the root `theme.ts`)
    ├── public/               render staging, gitignored
    ├── store/                ⚠️ the weekly snapshots — IN the project, and COMMITTED
    ├── tests/                its own suite, its own `testpaths`
    └── docs/adr/             its own decision records
```

### The five seams, copied deliberately

`song-video/paths.py` already solved this, and each solution carries a warning worth inheriting:

| Seam | Rule | Why |
|---|---|---|
| `project_root()` | `parents[1]` | ⚠️ the package sits in the project, so a `src/`-inside-`src/` would be for no gain |
| `repo_root()` | **`store.root()`** — asked for, not assumed | ⚠️ *"one level up" stopped being true* once the reel moved under `src/` |
| `data_root()` | `brief_paths.data_root()` | ⚠️ **one env var** (`MARKET_OVERVIEW_DATA`) for every product — *"there is deliberately only one copy"* of the default |
| `shared_remotion()` | `repo_root()/remotion` | the vendored fonts and the seeded PRNG, reused |
| `mark_dir()` | the brief's `resource/brief/` | ⚠️ **one licensed mark serves every product**, read through the brief's own loader |

### The namespaces

**Data** — under the shared root, namespaced, so products can render concurrently without a lock:

- `resource/books/` — including the **cover cache** from ticket 05: `resource/books/covers/<isbn13>.jpg`
- `output/books/<week>/<chart>/` — mirroring the brief's `output/brief/<date>/<lang>/` shape

**Not data** — in the project, **committed**: `store/<week>/raw/*.json` and `store/<week>/facts.json`.

⚠️ `store/` is committed on purpose — it *is* the rebuild evidence, the same reason the brief's per-date snapshot is
deliberately not gitignored.

### Three repo-wide consequences that must not be missed

1. ⚠️ **The README becomes wrong the moment this lands.** It says *"Two products are built from here"* and *"This is
   the repository's only README, and it is the whole document."* A third product changes the product table, the
   install section and the data-layout section.
2. ⚠️ **`./build` is "the front door over both products"** — it must learn the third.
3. ⚠️ **`testpaths` must be declared.** The brief's `pyproject.toml` already records why: a bare `pytest` at the root
   walked into the nested project's tests and died importing a package its environment did not have.

### The ADRs this product writes for itself

Following the reel's six, the decisions here that are *hard to reverse, surprising, and a real trade-off* are:

1. The four charts are India-market, and **all-language is a superset** (tickets 12, 14).
2. **Corroboration is the admission gate** — a title enters only when sources agree (ticket 17).
3. **"Best price" means Amazon + Flipkart**, labelled with the retailer, never claiming more (ticket 04).
4. The **cover cache is keyed by ISBN in the data root**, with the source URL in the snapshot (ticket 05).
5. **Depend on the library, not on another product's artefact** (ticket 08).
6. **The chart logic is versioned** (`chart_logic: 1`) so an old week re-renders as it was (ticket 03).
