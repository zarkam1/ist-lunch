# AGENTS.md — IST Lunch Codex Guide (v3)

You are Codex working inside the **IST Lunch** repo. Your job is to run the **unified lunch pipeline**: discover nearby restaurants, extract menus with a **cost‑aware smart router**, and publish clean Swedish dish data for the frontend. This version merges the strengths of `unified_scraper.py` and `smart_lunch_scraper.py`.

---

## Current Reality & Targets

* **Observed:** \~70% end‑to‑end success; **135+ dishes** from **11+ restaurants** (hybrid). Cost ≈ **\$2–3/month** at current scale.
* **Traditional** ≈ 53% success; **Vision** (Playwright + GPT‑4 Vision) ≈ 100% but pricier.
* **Problem sites:** **The Public** (Elementor/WordPress) and **Restaurang S** (Divi) need JavaScript rendering.
* **Goal:** ≥70% success at **< \$3/month**, with automatic fallback only when needed.

---

## Success Criteria (v3)

1. Smart router prefers **cheap** paths; auto‑detects failure (<3 items) and escalates.
2. Known JS‑heavy sites use **requires\_screenshot** direct path unless overridden.
3. URL variation strategy (`/meny`, `/lunch`, `/dagens-lunch`) attempted before fallback.
4. Output files written atomically and schema‑valid on every run:

   * `data/restaurants_verified.json` (discovery + meta)
   * `data/all_menus.json` (per‑restaurant bundle)
   * `data/lunch_dishes_complete.json` (flat list for UI)
5. Weekly automation (Mon 10:00 Europe/Stockholm) green; local run finishes < 6 min with clear logs.

---

## Architecture (authoritative)

```
Google Places discovery (1.0 km, sv-SE) + blacklist/whitelist
      ↓
Smart Router
  ├─ PATH A: Traditional (ScraperAPI render=true) + GPT‑4o‑mini (HTML)
  │     └─ URL variants tried: base, /meny, /lunch, /dagens-lunch
  ├─ PATH B: Vision (Playwright screenshot) + GPT‑4o Vision
  └─ PATH C: (reserved) Site‑specific selectors
      ↓
Normalize → validate → write JSONs → log stats & estimated cost
```

---

## Files & Responsibilities

```
scraper/
  unified_scraper.py      # Main pipeline (keep as entry point)
  smart_lunch_scraper.py  # Source for distance/schedule+config logic (ingest parts)
  requirements.txt
frontend/
  app/api/menus/route.ts  # Reads data/* and serves dish-first API
.github/workflows/
  scrape-menus.yml        # Weekly Mon 10:00 Europe/Stockholm
```

**Rule:** Keep public API stable; only make it more resilient (serve local files when remote fetch fails). Avoid breaking consumers.

---

## Environment & Secrets

```
GOOGLE_PLACES_API_KEY=...
SCRAPERAPI_KEY=...
OPENAI_API_KEY=...
TZ=Europe/Stockholm
```

Install Playwright locally: `playwright install chromium`.

---

## Data Contracts (unchanged from v2, dish‑first)

```ts
// Restaurant discovery
type PriceLevel = 1|2|3|4
interface Restaurant {
  id: string; name: string; website?: string; rating?: number; review_count?: number;
  price_level?: PriceLevel; lat?: number; lon?: number; walk_minutes?: number;
  opening_hours?: any; serves_lunch?: boolean | null; category?: string;
  whitelisted?: boolean;
}

type Category = 'Kött'|'Kyckling'|'Fisk'|'Vegetarisk'|'Vegansk'|'Pizza'|'Pasta'|'Asiatiskt'|'Persiskt'|'Sushi'|'Sallad'|'Soppa'|'Buffé'|'Övrigt'
interface MenuItem {
  name: string; description: string; price: number | null; category: Category;
  restaurant: string; restaurant_id: string; restaurant_type?: string;
  extraction_method: 'traditional'|'screenshot'|'manual';
}
```

### Validation Rules

* Prices accepted **40–200** else `null`; strip currency symbols.
* Categories strictly mapped to the set above; unknown → `'Övrigt'`.
* Deduplicate by `(restaurant_id + normalized name + price)`.
* Max **10 items/restaurant** per run.
* Preserve å/ä/ö (UTF‑8).

---

## Smart Router — Policy & Config

**Thresholds**

* **Success** when `items_found ≥ 3` after traditional path.
* **Auto‑escalate** to Vision when `< 3` or HTML is empty/JS‑shell.
* **Hard‑route** to Vision when `id ∈ requires_screenshot`.

**Config objects** (co‑located near top of `unified_scraper.py`):

```py
REQUIRES_SCREENSHOT = {
  'the-public': 'JS heavy (Elementor, dynamic injection)',
  'restaurang-s': 'JS heavy (Divi theme)'
}

RESTAURANT_CONFIG = {
  'restaurang-s': {'update_frequency': 'daily', 'priority': 1},
  'the-public':   {'update_frequency': 'daily', 'priority': 1},
  'burgers-beer': {'update_frequency': 'static', 'priority': 3},
  # default weekly Monday for others
}

BLACKLIST = ['delibruket-flatbread','piatti','parma']  # dinner/no lunch
WHITELIST = ['restaurang-s','tre-broder','bra-mat']
```

**Routing Steps**

1. If `id in REQUIRES_SCREENSHOT` → **Vision** directly.
2. Else try **Traditional** with URL variants (base, `/meny`, `/lunch`, `/dagens-lunch`).
3. If `< 3` items → **Vision fallback**.
4. Record `extraction_method` used in each `MenuItem`.

**Cost Guardrails**

* Limit Vision uses per run (flag `--max-vision 6`).
* Respect polite delay (≥1s) between site visits.
* Log estimated cost: `traditional≈$0.002` vs `vision≈$0.10` per restaurant.

---

## Discovery & Scheduling

* Use Google Places (sv‑SE) radius 1.5 km centered on Sundbyberg office.
* Compute `walk_minutes` and sort by **priority → distance**.
* **should\_update\_today(id)** implements: daily | weekly(monday) | static(weekly check).
* Always include whitelisted; always exclude blacklisted.

---

## Implementation Tasks for You (Codex‑ready)

1. **Merge smart config & scheduling**

   * Move/port: `RESTAURANT_CONFIG`, blacklist/whitelist, distance sort, `should_update_today()` from `smart_lunch_scraper.py`.
   * Add `walk_minutes` to discovery output.
2. **Add smart router**

   * Add `REQUIRES_SCREENSHOT` and routing thresholds.
   * Implement URL variant tries; detect empty JS shells.
3. **Tighten extractors**

   * Traditional: trim boilerplate, pass pruned HTML to GPT‑4o‑mini, Swedish output only.
   * Vision: Playwright navigate → click `Meny/Lunch/Dagens` if present → full‑page screenshot → GPT‑4 Vision prompt (Swedish descriptions mandatory for ethnic menus).
4. **Validation + outputs**

   * Enforce schema & price/category coercion; deduplicate; cap items per restaurant.
   * Write three JSONs atomically; include per‑restaurant timing, method, and short error.
5. **Observability**

   * Print final summary (restaurants scraped, total dishes, success %, estimated cost).
   * Emit counts of traditional vs vision.
6. **Automation**

   * Add/verify `.github/workflows/scrape-menus.yml` for Mondays 10:00 Europe/Stockholm; upload artifacts.

---

## CLI & Flags (suggested)

```
python scraper/unified_scraper.py \
  --radius 1500 --concurrency 6 --max-vision 6 --debug false
```

Defaults: success threshold = 3 items; timeouts 30s/request; overall < 6 min.

---

## Acceptance Tests (PR checklist)

* [ ] Router escalates only when `<3` items (or known JS site) and records method.
* [ ] The Public + Restaurang S succeed via Vision path.
* [ ] Traditional path succeeds for at least half of non‑JS sites.
* [ ] 3 JSON outputs valid; UTF‑8 Swedish preserved; categories from set only.
* [ ] Success ≥70%, total dishes ≥120 on sample run; monthly cost projected < \$3.

— End of AGENTS.md (v3) —
