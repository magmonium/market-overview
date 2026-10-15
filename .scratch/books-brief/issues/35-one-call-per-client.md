# One call per client — the registry is keyed by vendor, and the fetch is not

Type: task
Status: resolved
Found by: 34

## Question

Widening the comics chart to eight storefronts should have added eight requests to a run. Instead the gather was visibly
slow, and the store's own evidence showed a page being written **twice, fifty-two seconds apart**:

```
19:38:16  raw/amazon-us-comics.html
19:38:36  raw/amazon-uk-comics.html
...
19:39:08  raw/amazon-us-comics.html   ← the same store, fetched again
19:39:10  raw/amazon-uk-comics.html
```

So: **why does one chart fetch the same store more than once — and does the repetition change the chart?**

## Answer

### ⚠️ The conductor called the client once per *vendor*, and the client reads every list

`cli.gather` walks the chart's declared vendors and calls `CLIENTS[vendor].fetch(chart, week=…)` for each:

```python
cliented = [vendor for vendor in chart.vendors if vendor in CLIENTS]
for vendor in cliented:
    for page in CLIENTS[vendor].fetch(chart, week=week):
```

⚠️ **But `CLIENTS` maps eight Amazon storefronts to one module**, and `amazon.fetch` iterates **every list the chart
declares for it** (`for entry in chart.lists: if not owns(entry.slug): continue`). ⚠️ So an eight-store chart called the
`amazon` module **eight times**, and each call fetched **all eight stores**:

| Chart | Stores declared | Requests made | Requests intended |
|---|---|---|---|
| `english` | 4 | **16** | 4 |
| `comics` | 8 | **64** | 8 |
| `bengali` | 2 bookshops (`woocommerce`) | **4** | 2 |
| **W41, whole week** | — | **81** | **13** |

### ⚠️ And the duplicates were not harmless — the ranking was wrong

⚠️ Every page was parsed and `rows.extend(...)`ed, so **every row arrived N times** (eight, for a comics storefront).

⚠️ `_weekly` *looks* like it absorbs that: it collapses a work's rows **per list** to its best position, so the summed
score is unchanged. ⚠️ **But it also sizes each list by counting its rows** —

```python
sizes[row.list] = sizes.get(row.list, 0) + 1
```

— and `rank.weight` scales a list by its depth:

```python
return weights.get(vendor, 1.0) * min(1.0, entry.size / N_REF)     # N_REF = 100
```

⚠️ **A thirty-card storefront was therefore sized 240**, which lifts it from a **0.3** weight to a full **1.0** — and
`points` is computed from the same inflated size, so the tail of the list is lifted too. ⚠️ The chart ranked that vendor
far above the weight ticket 03 gives it, and **the error grew with every store added**: 4× on the English chart, 8× on
comics.

⚠️ **The defect is older than the eight stores.** It arrived with the English chart's four Amazon stores (2026-10-15) and
was invisible until a chart declared **two vendors sharing one client**. ⚠️ It had one symptom nobody read: the suite's
own comic stub scores `0.02` where a single one-row list should score `0.01` — **the duplicate row, visible in an
assertion message.**

### ✅ The fix, and the test that would have caught it

⚠️ **One call per *client*, not per vendor** — the client is what reads a chart's lists, and the vendor is only the key
the registry happens to use:

```python
clients: dict[object, str] = {}
for vendor in cliented:
    clients.setdefault(CLIENTS[vendor], vendor)
```

⚠️ The complaint a failure prints still names a **vendor** — the first this client serves for this chart — because the
failure is the *client's*, and naming one of its stores names the module that failed.

⚠️ ⚠️ **And the reason this was invisible for so long is the test double**: `test_cli._client` builds a **fresh `Mock`
per vendor**, so a registry of distinct stubs *cannot* show a shared client being asked twice. The new test
(`test_a_client_shared_by_several_vendors_is_asked_once_per_chart`) hands **one client to two vendors on purpose** and
asserts the call count is **one per chart** — which is what the real registry does for Amazon.

⚠️ **This is the same shape of mistake the tickets keep finding**: not a wrong rule, but a **second place** the same fact
lived — `CLIENTS` keyed one way and `fetch` written the other — with nothing connecting them. ⚠️ 349 tests pass.
