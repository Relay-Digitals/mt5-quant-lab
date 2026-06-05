# Anonymouse Mobile — Kotlin Multiplatform (Compose)

Implementasi desain **Anonymouse Mobile** (handoff Claude Design) sebagai app **Kotlin Multiplatform + Compose Multiplatform**, tersambung ke **Claude Code bridge** (`claude_api.py`) di CT108 untuk backtest / forward-test / chat.

## Status — Fase A (fondasi)
✅ Design-system (token warna dark/light + accent, tipografi, dimensi) — `theme/Theme.kt`
✅ Komponen inti (Card, Stat, Chip, Toggle, Slider, TopBar, BottomNav, FAB, Badge, Btn, Avatar) — `ui/Components.kt`
✅ Chart Canvas (Area, Donut, Spark, Candle) — `ui/Charts.kt`
✅ Ikon Canvas — `ui/Icons.kt`
✅ Shell navigasi 5 tab + overlay — `App.kt`
✅ **Home** (penuh), **Backtest** (config+run+hasil+trade-log), **Forward** (market crypto/forex/IDX, posisi, notif, equity)
✅ **Signals**, **Studio** (marketplace/payout)
✅ **Claude Code chat** wired ke bridge (SSE streaming, role research/deploy/live) — `screens/ClaudeChatScreen.kt`
✅ API client bridge (Ktor REST + SSE) — `data/BridgeApi.kt`
🟡 Data masih `data/MockData.kt` (dummy) — diganti data quant asli di Fase berikut.

## TODO Fase berikut
- [ ] Ganti `DB.runBacktest` & data Forward → panggilan **BridgeApi** ke skrip quant CT108 (idx_*, regime_scan, fx_report) + parsing artifact (equity PNG/CSV).
- [ ] `BridgeConfig` (host Tailscale CT108 + device token) → simpan di DataStore + layar Settings.
- [ ] Font asli: drop `Manrope`, `Space Grotesk`, `JetBrains Mono` (.ttf) ke `composeApp/src/commonMain/composeResources/font/`, lalu set di `theme/Theme.kt` (`Fonts`).
- [ ] Push notif FCM ("backtest selesai", "ignition exit") + register ke `/v1/push/register`.
- [ ] Pull-to-refresh, bottom-sheet, swipe-row (parity penuh m-ui.jsx).
- [ ] Bisa diperluas ke iOS/Desktop (struktur KMP sudah siap; tambah target di `composeApp/build.gradle.kts`).

## Build & jalankan
Butuh JDK 17 + Android SDK (atau Android Studio Ladybug+).
```bash
cd anonymouse-mobile
gradle wrapper            # sekali: generate gradlew (atau buka di Android Studio)
./gradlew :composeApp:assembleDebug
# APK → composeApp/build/outputs/apk/debug/composeApp-debug.apk
```
Tes di **redroid CT160**:
```bash
adb connect 192.168.0.160:5555
adb -s 192.168.0.160:5555 install -r composeApp-debug.apk
```
> Disarankan buka folder ini di **Android Studio** → Sync → Run; AS otomatis bikin gradle-wrapper.jar & SDK.

## Sambungkan ke bridge
1. Deploy `claude_api.py` (folder `../wa-claude-bridge`) ke CT108 (port 8090) + isi `DEVICE_TOKENS`.
2. Pasang Tailscale di CT108 + HP → catat hostname tailnet CT108.
3. Set `BridgeConfig.baseUrl` (mis. `http://ct108-ts:8090`) + `token` (di `ClaudeChatScreen.kt`, nanti pindah ke Settings/DataStore).

## Peta desain → kode
| Desain (jsx) | Kode (Kotlin) |
|---|---|
| `m-ui.jsx` | `ui/Components.kt`, `ui/Charts.kt`, `ui/Icons.kt` |
| `m-app.jsx` | `App.kt` |
| `m-home.jsx` | `screens/HomeScreen.kt` |
| `m-trade.jsx` (Backtest/Forward) | `screens/BacktestScreen.kt`, `screens/ForwardScreen.kt` |
| `m-signals.jsx` | `screens/SignalsScreen.kt` |
| `m-studio.jsx` | `screens/StudioScreen.kt` |
| `data.js` (DB) | `data/MockData.kt`, `data/Models.kt` |
| (baru) Claude chat | `screens/ClaudeChatScreen.kt` + `data/BridgeApi.kt` |
