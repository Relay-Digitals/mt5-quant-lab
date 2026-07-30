# Pantau IDX — StockPick (Kotlin Multiplatform)

Compose Multiplatform (Android + iOS) implementation of the **Pantau IDX / StockPick**
design, wired to the **Stockbit exodus** API — with the *screener ("screens")* endpoints
as the primary data source, per spec.

## Screens (from `Pantau IDX.dc.html`)

| Screen | Compose | Stockbit endpoint |
|---|---|---|
| Splash | `ui/screens/SplashScreen.kt` | — |
| Watchlist | `WatchlistScreen.kt` | `GET screener/universe` → fallback `emitten/trending` |
| Market + **Screens** | `MarketScreen.kt` | `GET screener/preset` (list), `GET screener/templates/{id}` (run), `emitten/trending` |
| Insider Activity | `InsiderScreen.kt` | `GET insider/company/majorholder?symbols=` |
| Portfolio | `PortfolioScreen.kt` | (holdings demo; wire `securities/order/v1/list`) |
| Detail (Stream/Keystats/Orderbook/Analysis) | `DetailScreen.kt` | `charts/{sym}/daily`, `research/company/{sym}`, `company-price-feed/*`, `order-trade/broker/distribution` |

## Screener integration (the "screens")

`data/StockbitApi.kt`:
- `screenerPresets()` → `GET /screener/preset` → guru/preset screens shown in **Market › Screens**
- `runScreen(id)` → `GET /screener/templates/{id}?type=guru` → the matching universe
- `screenerUniverse()` → `GET /screener/universe` → full screenable universe (Watchlist source)

All requests carry the mandatory headers (mirrors `stockbit-quant/stockbit_client.py`):
`User-Agent: okhttp/4.12.0` (required — Cloudflare 1010 without it), `Authorization: Bearer <token>`,
`X-AppVersion: 3.21.0`, `X-Platform: android`, `Accept-Language: id`.

## Auth

Full in-app login flow (`data/StockbitAuth.kt`, wired to `ui/screens/AuthScreen.kt`):

```
login/v6/username  { username, password, device_id, player_id }
   → Success(access[,refresh])           → token saved, app goes live
   → NeedsOtp(session)  (new device)     → OTP step
login/v6/new-device/verify  { otp, session, ... }  → Success(access)
```

- The obtained access token is persisted via `TokenStore` (Android SharedPreferences / iOS
  NSUserDefaults) and reloaded on launch — no hardcoding.
- **Guest mode**: "Lewati" on the auth screen browses every screen with `SampleData`.
- Status bar reflects reality: **LIVE · IDX** with a valid token, **SIM · IDX** on sample data.

State of the repo tokens (`stockbit-docs/stockbit_token.env`): access **expired 2026-05-31**
and the refresh token (7-day validity) is **also expired** — verified: `login/refresh` returns
`UNAUTHORIZED`. A fresh login therefore triggers a **new-device OTP** to the account owner.
The request-body field names for `login/v6/*` are best-effort (docs expose only the DataParam
type name) — confirm against a real login capture and adjust in `StockbitAuth`.

## Portfolio (trading)

`portfolio/v2/*` and `securities/order/v1/list` live on **carina.stockbit.com** and need a
**separate securities token** (`Authorization-Carina: Bearer …`, PIN-gated) — the exodus data
token does not authorize them. `StockbitApi.portfolioSummary(carinaToken)` is wired for when
that token is available; until then `PortfolioScreen` shows a holdings demo.

## Build / run

No JDK/Gradle was available in the authoring environment, so this was **not compiled here**.
To build:

```bash
# generates the wrapper jar if missing, then builds
gradle wrapper --gradle-version 8.11.1
./gradlew :composeApp:assembleDebug        # Android APK
# or open the folder in Android Studio (Koala+) and Run.
```

Requires: Android SDK 36, JDK 17, Kotlin 2.1.20 (via the version catalog). iOS target builds via
the `ComposeApp` framework from Xcode.

## Design fidelity

Palette + type are lifted verbatim from the design (`theme/Theme.kt`): bg `#0B0E13`, brand green
`#2FD07A`, amber `#FFB020`, red `#FF5A6E`.

**Fonts (bundled):** IBM Plex Sans (400/500/600/700) + IBM Plex Mono (400/500/600) TTFs live in
`composeApp/src/commonMain/composeResources/font/` (SIL OFL, Latin subset). They are loaded via
`theme/AppFonts.kt` and provided through `LocalPlexSans` / `LocalPlexMono` CompositionLocals +
the Material typography, so all screens render exact IBM Plex. No platform-font fallback.
