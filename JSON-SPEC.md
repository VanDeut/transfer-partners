# Remote Data JSON Spec

The app fetches two JSON files from `https://raw.githubusercontent.com/VanDeut/transfer-partners/main/`
and falls back to the copies bundled in `TR Wallet/Data/` if the fetch fails.
The remote is the source of truth for installed apps — the bundled files are only a fallback.

Both files are decoded with Swift `Codable` (`TransferPartner.swift`, `PointValuation.swift`).
**Unknown keys are ignored; missing required keys make the whole file fail to decode**
(the app silently falls back to the bundled copy), so follow the schemas exactly.

---

## 1. `transfer-partners.json`

Used by the Transfer Partners screen to show which of a member's flexible-currency
balances can be moved to which airline/hotel program, and at what ratio.

### Top-level

```json
{
  "schema_version": "1.0.0",
  "last_generated": "2026-09-13T21:35:00Z",
  "transfers": [ ... ]
}
```

| Key | Required | Type | Notes |
|---|---|---|---|
| `schema_version` | yes | string | Keep `"1.0.0"` unless the row shape changes. |
| `last_generated` | yes | ISO-8601 date string | Decoded as a `Date`. See **Dates** below. |
| `transfers` | yes | array | One row per (source → destination) pair. |

Any other top-level keys (`last_data_source`, `data_as_of`, …) are ignored — fine to include.

### Row

```json
{
  "from_program": "Chase Ultimate Rewards",
  "to_program": "World of Hyatt",
  "ratio": 1.0,
  "category": "hotel",
  "last_updated": "2026-09-13T21:35:00Z"
}
```

| Key | Required | Type | Rules |
|---|---|---|---|
| `from_program` | yes | string | The credit-card currency. **Must start with the app's flexible-reward name** (see matching). |
| `to_program` | yes | string | The airline/hotel loyalty program. **Must contain the brand word** of the app's airline/hotel name (see matching). |
| `ratio` | yes | number | Destination points **per 1 source point**. `1.0` = 1:1. See below — this is the field most often written backwards. |
| `category` | yes | string | Exactly `"airline"` or `"hotel"` (lowercase). Any other value is never shown. |
| `last_updated` | yes | ISO-8601 date string | The newest value across all rows is shown as "Updated Sep 13, 2026" in the UI. |
| `promo_bonus_pct` | no | number | Omit. (Decoded if present, but promos are intentionally not maintained.) |
| `promo_expires` | no | date string | Omit. |

#### `ratio` direction

```
destination_points = source_points × ratio
```

| Published transfer rate | Meaning | `ratio` |
|---|---|---|
| 1:1 | 1,000 UR → 1,000 Hyatt | `1.0` |
| 5:4 (Amex → Emirates) | 1,000 MR → 800 Skywards | `0.8` |
| 250:200 (Amex → JetBlue) | 1,000 MR → 800 TrueBlue | `0.8` |
| 5:3 (Capital One → JetBlue) | 1,000 → 600 | `0.6` |
| 2:1 (Citi → Accor) | 1,000 TYP → 500 ALL | `0.5` |
| 1:1.5 (Amex → Choice, if applicable) | 1,000 → 1,500 | `1.5` |

Sanity check: a ratio **greater than 1.0** means the user ends up with *more* points than they
transferred. That is rare (Choice, some hotel promos); if you see 1.25 / 1.67 / 2.0 on an
airline row it is almost certainly inverted.

#### How `from_program` is matched

The app compares `from_program` to the member's flexible-reward program name, case-insensitively,
and accepts a match if either string is a **prefix** of the other. The app's built-in names are:

```
American Express   Chase   Capital One   Citi   Bank of America   Wells Fargo   Bilt   …
```

So use these exact names, or these names followed by the currency:

| Good | Why |
|---|---|
| `"Chase Ultimate Rewards"` | starts with "Chase" |
| `"American Express Membership Rewards"` | starts with "American Express" |
| `"Citi ThankYou Rewards"` | starts with "Citi" |
| `"Capital One Rewards"` / `"Capital One Miles"` | starts with "Capital One" |
| `"Bilt Rewards"` | starts with "Bilt" |

| Bad | Why |
|---|---|
| `"Amex MR"` | doesn't start with "American Express" |
| `"Ultimate Rewards"` | doesn't start with "Chase" |
| `"Citibank ThankYou"` | "Citibank" is not a prefix of "Citi" and vice-versa is false too ("citi" IS a prefix of "citibank" — this one actually works, but don't rely on it) |

Use **one spelling per issuer** across the whole file. The app de-duplicates sources by matched
name, so mixed spellings just create noise.

#### How `to_program` is matched

The app takes the member's airline/hotel account name (from its built-in list, e.g.
`"Delta Air Lines"`, `"Hyatt Hotels Corporation"`, `"InterContinental Hotels Group (IHG)"`),
strips filler words, and checks that every remaining word appears in `to_program`.

Filler words that are ignored on both sides:
`air airlines airline airways lines hotels hotel group international corporation worldwide resorts
rewards club plus one world of the and by mileage miles frequent flyer program bank honors hospitality inc`

Text inside parentheses in the account name is also tried on its own (so `(IHG)` → `ihg`).

| App account name | Brand words | `to_program` that matches | Doesn't match |
|---|---|---|---|
| Delta Air Lines | `delta` | `Delta SkyMiles` | — |
| Hyatt Hotels Corporation | `hyatt` | `World of Hyatt` | — |
| InterContinental Hotels Group (IHG) | `intercontinental` or `ihg` | `IHG One Rewards` | — |
| British Airways | `british` | `British Airways Club`, `British Airways Avios` | `Avios` ✗ |
| Iberia | `iberia` | `Iberia Plus`, `Iberia Avios` | `Avios` ✗ |
| Aer Lingus | `aer lingus` | `Aer Lingus AerClub` | `Avios` ✗ |
| Air France / KLM Royal Dutch Airlines | `france` / `klm royal dutch` | `Air France-KLM Flying Blue` | `Flying Blue` ✗ |
| All Nippon Airways (ANA) | `all nippon` or `ana` | `ANA Mileage Club` | — |
| Japan Airlines | `japan` | `Japan Airlines Mileage Bank`, `JAL Mileage Bank` ✗ | use "Japan Airlines" |
| Cathay Pacific | `cathay pacific` | `Cathay Pacific Asia Miles` | `Cathay Asia Miles` ✗ |
| Singapore Airlines | `singapore` | `Singapore KrisFlyer` | — |
| Turkish Airlines | `turkish` | `Turkish Airlines Miles&Smiles` | — |
| Marriott International | `marriott` | `Marriott Bonvoy` | — |
| Choice Hotels International | `choice` | `Choice Privileges` | — |
| Accor Hotels | `accor` | `Accor Live Limitless` | `ALL` ✗ |

Rule of thumb: **`to_program` must contain the airline/hotel's brand name, not just the
currency name.** Shared-currency programs (Avios, Flying Blue) need one row per airline:

```json
{ "from_program": "Chase Ultimate Rewards", "to_program": "British Airways Avios", "ratio": 1.0, "category": "airline", "last_updated": "..." },
{ "from_program": "Chase Ultimate Rewards", "to_program": "Iberia Avios",          "ratio": 1.0, "category": "airline", "last_updated": "..." },
{ "from_program": "Chase Ultimate Rewards", "to_program": "Aer Lingus Avios",      "ratio": 1.0, "category": "airline", "last_updated": "..." }
```

Rows are grouped by exact `to_program` string in the UI, so spell each destination identically
on every issuer's row (`"World of Hyatt"` everywhere, not `"Hyatt"` on one and `"World of Hyatt"` on another).

---

## 2. `point-valuations.json`

Used everywhere the app turns a balance into dollars: dashboard totals, member totals, and the
Redemption Log (auto-fills the ¢/pt valuation when a program is selected).

### Top-level

```json
{
  "schema_version": "1.0",
  "last_generated": "2026-09-13T21:30:00Z",
  "default_cents_per_point": 1.0,
  "valuations": [ ... ]
}
```

| Key | Required | Type | Notes |
|---|---|---|---|
| `schema_version` | yes | string | `"1.0"`. |
| `last_generated` | yes | string | Kept as a plain string; any format. |
| `default_cents_per_point` | yes | number | Decoded but **not currently used** — the code hard-codes `1.0` as the fallback. Keep it `1.0`. |
| `valuations` | yes | array | |

### Row

```json
{
  "program": "World of Hyatt",
  "category": "hotel",
  "cents_per_point": 1.7,
  "aliases": ["Hyatt", "Hyatt Hotels Corporation"],
  "last_updated": "2026-09-13T21:30:00Z"
}
```

| Key | Required | Type | Rules |
|---|---|---|---|
| `program` | yes | string | Display/canonical name. Matched exactly (case-insensitive). |
| `category` | yes | string | `"airline"`, `"hotel"`, `"car"`, or `"flexible"`. Informational only; not used for matching. |
| `cents_per_point` | yes | number | Cents. `1.7` = 1.7¢ = $0.017 per point. **Not** dollars. |
| `aliases` | yes | array of strings | May be `[]` but the key must exist. Matched exactly (case-insensitive). |
| `last_updated` | yes | string | ISO-8601. If unparseable the app substitutes "now" — it does not fail. |

#### How lookups work (this is the important part)

```
1. lowercase + trim the app's program name
2. return the first row whose `program` equals it
3. else return the first row where any `aliases` entry equals it
4. else return 1.0
```

**There is no fuzzy matching.** "Delta" does not match "Delta Air Lines". The name the app
passes in is whatever the user's account is called, which for most users is one of the app's
built-in names. So every row must list the app's built-in name in `program` or `aliases`, or the
program silently values at 1.0¢.

The app's built-in names that need to resolve (put these in `aliases`):

**Flexible currencies**
`American Express` · `Chase` · `Capital One` · `Citi` · `Bank of America` · `Wells Fargo` · `Bilt` · `Barclays` · `US Bank` · `Discover`

**Airlines**
`American Airlines` · `Delta Air Lines` · `United Airlines` · `Southwest Airlines` · `Alaska Airlines` · `JetBlue Airways` · `Spirit Airlines` · `Frontier Airlines` · `Allegiant Air` · `Hawaiian Airlines` · `British Airways` · `Air France` · `KLM Royal Dutch Airlines` · `Lufthansa` · `Emirates` · `Qatar Airways` · `Etihad Airways` · `Singapore Airlines` · `Cathay Pacific` · `Japan Airlines` · `All Nippon Airways (ANA)` · `Korean Air` · `Air Canada` · `Aeromexico` · `Avianca` · `Turkish Airlines` · `Iberia` · `Aer Lingus` · `Virgin Atlantic` · `Qantas` · `Finnair` · `LATAM Airlines`

**Hotels**
`Marriott International` · `Hilton Worldwide` · `Hyatt Hotels Corporation` · `InterContinental Hotels Group (IHG)` · `Wyndham Hotels & Resorts` · `Choice Hotels International` · `Best Western Hotels & Resorts` · `Accor Hotels` · `Radisson Hotels`

**Car rental**
`Hertz` · `Avis` · `Budget` · `Enterprise` · `National` · `Alamo` · `Dollar` · `Thrifty` · `Sixt` — plus long forms `Enterprise Rent-A-Car`, `Avis Budget Group`, `National Car Rental`, `Alamo Rent A Car`, `Budget Car Rental`

Also include the loyalty-program spelling (`Delta SkyMiles`, `Marriott Bonvoy`, `Hilton Honors`)
and common shorthand (`Delta`, `Hyatt`, `Amex`, `Chase UR`) since users can type custom names.

Example — a complete, app-compatible row:

```json
{
  "program": "Delta SkyMiles",
  "category": "airline",
  "cents_per_point": 1.2,
  "aliases": ["Delta", "Delta Air Lines", "Delta Airlines", "SkyMiles"],
  "last_updated": "2026-09-13T21:30:00Z"
}
```

If a program has several rows (e.g. `"Chase"` and `"Chase Ultimate Rewards"`), the first exact
`program` hit wins over any alias hit; keep one row per program and put the variants in `aliases`.

---

## Dates

Use UTC ISO-8601: `2026-09-13T21:35:00Z`. Fractional seconds (`…:00.000000Z`) currently decode
on iOS 17+/macOS 14+ but are rejected by `ISO8601DateFormatter` in the valuation decoder (it
falls back to "now"). Drop the fractional part to be safe.

## Encoding

UTF-8, no BOM. Watch for mojibake from scrapers (`â€“`, `Â®`, `Ã©`) — `"Miles&Smiles"` is fine,
`"Swissôtel"` is fine, `"SwissÃ´tel"` is not.

## Pre-publish checklist

- [ ] Valid JSON; both files parse.
- [ ] Every row has every required key.
- [ ] `category` is exactly `airline`/`hotel` (transfers) or `airline`/`hotel`/`car`/`flexible` (valuations).
- [ ] No transfer `ratio` > 1.0 unless you've confirmed the program really gives a bonus.
- [ ] Every `from_program` starts with one of: American Express, Chase, Capital One, Citi, Bilt, Wells Fargo, Bank of America.
- [ ] Every `to_program` contains the airline/hotel brand name (not just "Avios", "Flying Blue", "ALL").
- [ ] Same `to_program` spelling on every issuer's row.
- [ ] Every app built-in name listed above appears in some valuation row's `program` or `aliases`.
- [ ] No program names longer than ~40 chars, no `?`, no sentences — those are scraper junk.
- [ ] Row counts are in the expected range (transfers ≈ 55–75, valuations ≈ 30–60). A big drop means a scraper broke.
