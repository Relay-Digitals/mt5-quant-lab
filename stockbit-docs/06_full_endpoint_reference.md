# Stockbit Android — Complete API Endpoint Reference (REST / gRPC / GraphQL)

> Source: JADX decompile `StockbitData/stockbit/sources` · Generated dari analisis statis (interceptor + Koin DI + Retrofit interfaces).  
> **827 REST endpoints** di **111 interface**, di-scan rekursif sampai paket ter-nested.

## 0. Ringkasan Transport — gRPC & GraphQL

| Transport | Dipakai? | Bukti |
|---|---|---|
| **REST** (Retrofit2 + OkHttp3) | ✅ Ya | 827 endpoint, 110 interface `retrofit2.http` (anotasi ter-obfuscate: `@f`=GET, `@o`=POST, `@n`=PATCH, `@p`=PUT, `@b`=DELETE) |
| **gRPC** | ❌ Tidak | Tidak ada `io.grpc`, `MethodDescriptor`, `AbstractStub`, atau `StreamObserver` di seluruh tree |
| **GraphQL** | ❌ Tidak | Tidak ada Apollo runtime / `GraphQLRequest`. Satu-satunya string `graphql` hanya konstanta internal Sentry SDK (`auto.graphql.graphql`) |
| **Protobuf-over-WebSocket** (Tinder Scarlet) | ✅ Ya | Pengganti gRPC untuk real-time: `wss://wss-trading.stockbit.com/ws` (`WebSocketProtobufService`, qualifier `WS_PROTOBUF_BASE`). Lihat `docs/03_websocket_endpoints.md` |

**Kesimpulan:** Stockbit **tidak memakai gRPC maupun GraphQL**. Komunikasi = REST (request/response) + Protobuf-over-WebSocket (streaming real-time).

## 1. Base URL (terverifikasi dari Koin DI `T4.d2()` / `T4.e2()`)

Setiap interface dibuat dari Retrofit ber-qualifier tertentu; qualifier → host:

| Qualifier (Koin) | Base URL | Alias |
|---|---|---|
| `CLIENT_BASE_EXODUS` | `https://exodus.stockbit.com` | EXODUS |
| `CLIENT_BASE_LEGACY` | `https://api.stockbit.com/v2.4` | LEGACY v2.4 |
| `CLIENT_BASE_V25` | `https://api.stockbit.com/v2.5` | LEGACY v2.5 |
| `SECURITIES_NEW_CORE_BASE` | `https://carina.stockbit.com` | CARINA (securities new core) |
| `SECURITIES_ACCOUNT_CORE_BASE` | `https://carina.stockbit.com` | CARINA (securities account core) |
| `SECURITIES_BASE_EXODUS` | `https://api-sekuritas.stockbit.com` | SEKURITAS |
| `SECURITIES_BASE_NON_TRADING` | `https://api.masonline.id` | MAS ONLINE (non-trading) |
| `EIPO_BASE` | `https://api-sekuritas.stockbit.com` | SEKURITAS (e-IPO) |
| `EIPO_AUTH_BASE` | `https://api-sekuritas.stockbit.com` | SEKURITAS (e-IPO auth) |
| `CLIENT_FLIPT` | `https://flipt.stockbit.com` | FLIPT |
| `GIPHY_BASE` | `https://api.giphy.com` | GIPHY (vendor) |
| `YOUTUBE_BASE` | `https://www.youtube.com` | YOUTUBE (vendor) |
| `GOOGLE_CLOUD_BASE` | `https://api.stockbit.com/v2.4` | LEGACY proxy (google-cloud) |
| `AWS_STOCKBIT_BASE` | `https://stockbit.s3.amazonaws.com` | AWS S3 |
| `AWS_EXODUS_STOCKBIT_BASE` | `https://sb-stream-asset.s3.ap-southeast-1.amazonaws.com` | AWS S3 stream-asset |
| `WS_PROTOBUF_BASE` | `wss://wss-trading.stockbit.com/ws` | WS PROTOBUF (Scarlet) |

## 2. Header & Autentikasi global

Di-inject oleh OkHttp Interceptor (`com.stockbit.remote.di.*`), bukan di tiap method:

> ⚠️ **WAJIB `User-Agent: okhttp/4.12.0`** (atau UA app). Tanpa header ini Cloudflare menolak dengan `HTTP 403 / error code: 1010`. Diverifikasi live — lihat Appendix B.

```http
User-Agent: okhttp/4.12.0                  # WAJIB — kalau tidak, Cloudflare 1010
Authorization: Bearer {access_token}      # token social app
X-AppVersion: 3.21.0                       # string literal hardcoded di interceptor
X-Platform: android
X-DeviceType: {device_type}
Accept-Language: id                        # atau 'en'
Content-Type: application/json
Authorization-Carina: Bearer {carina_tkn} # khusus host carina.stockbit.com
```

Tier auth per host: **exodus / api.stockbit.com** = Bearer social · **api-sekuritas / carina** = token securities (PIN-gated) · **masonline** = securities non-trading.

## 3. Legenda dependency tiap endpoint

`Path`=segmen `{...}` di URL · `Query`=query string · `Body`=JSON body (`@Body`) · `Field`=form-urlencoded · `Part`=multipart · `Header`=header per-request · `→` = response DTO.

📌 Endpoint yang butuh ID/kode dari endpoint lain (chained, mis. `insider`, `{code}` broker, `room_id`, `emiten_code`): lihat **Appendix D — Peta Ketergantungan Antar-Endpoint**. Query param dari source + re-test: **Appendix C**.

**Kolom `Live test`** (hasil hit nyata 2026-05-30, token social, read-only): ✅`200` sukses · 🟡`400` perlu param valid · 🔑`401` butuh token securities · 🚫`403` akses ditolak · ⚪`404` no-data/dinamis · 🔴`500` server · ⏳`429` rate-limit · `⊘ not tested (write)` = POST/PUT/PATCH/DELETE sengaja tidak dieksekusi · `— (vendor/skip)` = host non-Stockbit. Ringkasan: Appendix B.

---

# ━━ HOST: CARINA (securities account core) — `https://carina.stockbit.com` ━━

**Auth:** Bearer (social) + `Authorization-Carina` + trading PIN context

## 1. `TradingProfileApi`  (3 endpoint)
<sub>com/stockbit/remote/api/securities/TradingProfileApi.java · qualifier `SECURITIES_ACCOUNT_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `v1/oa-file-utility/file/presign-download` | Query:`file_url` | `c<SuccessResponse<SecuritiesAccountPresignedUrlDTO>>` | 🟡 400 |
| 2 | POST | `v1/oa-file-utility/personal-amend-requests/documents` | Body:`map` | `c<SuccessResponse<PersonalAmendUploadDocumentDTO>>` | ⊘ not tested (write) |
| 3 | GET | `v1/oa-user-mgmt/public/personal-amend-requests/status` | — | `c<SuccessResponse<PersonalAmendRequestStatusDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getPublicDocumentUrl  [GET v1/oa-file-utility/file/presign-download]
curl -X GET "https://carina.stockbit.com/v1/oa-file-utility/file/presign-download?file_url=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getPersonalAmendUploadDocument  [POST v1/oa-file-utility/personal-amend-requests/documents]
curl -X POST "https://carina.stockbit.com/v1/oa-file-utility/personal-amend-requests/documents" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getPersonalAmendRequestStatus  [GET v1/oa-user-mgmt/public/personal-amend-requests/status]
curl -X GET "https://carina.stockbit.com/v1/oa-user-mgmt/public/personal-amend-requests/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 2. `LivenessApi`  (2 endpoint)
<sub>com/stockbit/remote/api/liveness/LivenessApi.java · qualifier `SECURITIES_ACCOUNT_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `v1/registration/liveness/eligibility` | — | `c<SuccessResponse<LivenessEligibilityDTO>>` | ✅ 200 |
| 2 | POST | `v1/registration/liveness/submit` | Body:`map` | `c<SuccessResponse<LivenessSubmitDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getLivenessEligibility  [GET v1/registration/liveness/eligibility]
curl -X GET "https://carina.stockbit.com/v1/registration/liveness/eligibility" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# submitLiveness  [POST v1/registration/liveness/submit]
curl -X POST "https://carina.stockbit.com/v1/registration/liveness/submit" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

```
</details>

## 3. `SecuritiesOpeningAccountApi`  (2 endpoint)
<sub>com/stockbit/remote/api/securities/SecuritiesOpeningAccountApi.java · qualifier `SECURITIES_ACCOUNT_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `v1/registration/page/next/{current_page}` | Path:`current_page` · QueryMap:`map` | `c<SuccessResponse<SecuritiesOANextPageDTO>>` | ✅ 200 |
| 2 | GET | `{url}/{desired_type}` | Path:`url` · Path:`desired_type` · QueryMap:`map` | `c<SuccessResponse<SecuritiesOADynamicOptionListDTO>>` | ⚪ 404 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getOANextPage  [GET v1/registration/page/next/{current_page}]
curl -X GET "https://carina.stockbit.com/v1/registration/page/next/{current_page}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getDynamicOptions  [GET {url}/{desired_type}]
curl -X GET "https://carina.stockbit.com/{url}/{desired_type}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

# ━━ HOST: CARINA (securities new core) — `https://carina.stockbit.com` ━━

**Auth:** Bearer (social) + `Authorization-Carina` + trading PIN context

## 4. `CarinaApi`  (38 endpoint)
<sub>com/stockbit/remote/api/securities/CarinaApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `balance/cash` | — | `c<SuccessResponse<BalanceCashDTO>>` | 🔑 401 |
| 2 | GET | `balance/cash/info` | QueryMap:`map` | `c<SuccessResponse<CashInfoDTO>>` | 🔑 401 |
| 3 | GET | `exercise/exercisable` | QueryMap:`map` | `c<SuccessResponse<ExercisableStockDTO>>` | 🔑 401 |
| 4 | GET | `exercise/tradable` | — | `c<SuccessResponse<TradableStatusDTO>>` | 🔑 401 |
| 5 | GET | `formula/v2` | — | `c<SuccessResponse<TradingFormulaDTO>>` | 🔑 401 |
| 6 | GET | `history` | QueryMap:`map` | `c<SuccessResponse<HistoryDTO>>` | 🔑 401 |
| 7 | GET | `history/realized` | QueryMap:`map` · Query:`transaction_types` | `c<SuccessResponse<HistoryRealizedDTO>>` | 🔑 401 |
| 8 | GET | `history/realized/detail` | QueryMap:`map` | `c<SuccessResponse<HistoryRealizedDetailDTO>>` | 🔑 401 |
| 9 | POST | `nego-engine/v1/order` | Body:`requestBody` | `c<SuccessResponse<OrderNegoDTO>>` | ⊘ not tested (write) |
| 10 | GET | `nego-engine/v1/order-book/{symbol}` | Path:`symbol` | `c<SuccessResponse<OrderBookNegoDTO>>` | 🔑 401 |
| 11 | GET | `nego-engine/v1/order-queue` | QueryMap:`map` | `c<SuccessResponse<OrderNegoQueueDTO>>` | 🔑 401 |
| 12 | POST | `nego-engine/v1/order/preview` | Body:`requestBody` | `c<SuccessResponse<OrderNegoPreviewDTO>>` | ⊘ not tested (write) |
| 13 | DELETE | `nego-engine/v1/order/{order_id}` | Path:`order_id` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 14 | PATCH | `nego-engine/v1/order/{order_id}/abort-cancel` | Path:`order_id` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 15 | PATCH | `nego-engine/v1/order/{order_id}/confirm-cancel` | Path:`order_id` · Body:`requestBody` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 16 | POST | `nego-engine/v1/order/{order_id}/confirm-matching` | Path:`order_id` · Body:`requestBody` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 17 | GET | `oms/auth/maintenance/status` | — | `c<SuccessResponse<MaintenanceStatusDTO>>` | ✅ 200 |
| 18 | POST | `order/day-trade/v1/buy` | Body:`requestBody` | `c<SuccessResponse<OrderDayTradeBuyDTO>>` | ⊘ not tested (write) |
| 19 | POST | `order/day-trade/v1/cancel` | Body:`orderDetailCancelDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 20 | POST | `order/day-trade/v1/sell` | Body:`requestBody` | `c<SuccessResponse<OrderDayTradeSellDTO>>` | ⊘ not tested (write) |
| 21 | POST | `order/v2/amend/bulk` | Body:`postOrderAmendBulkDataParam` | `c<SuccessResponse<OrderBuyDTO.OrderLimitInfoDTO>>` | ⊘ not tested (write) |
| 22 | POST | `order/v2/bulk-cancel` | Body:`postOrderBulkCancelDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 23 | POST | `order/v2/buy` | Body:`requestBody` | `c<SuccessResponse<OrderBuyDTO>>` | ⊘ not tested (write) |
| 24 | POST | `order/v2/cancel` | Body:`orderDetailCancelDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 25 | GET | `order/v2/detail` | QueryMap:`map` | `c<SuccessResponse<OrderDetailDTO>>` | 🔑 401 |
| 26 | GET | `order/v2/list` | — | `c<SuccessResponse<List<OrderDetailDTO>>>` | 🔑 401 |
| 27 | POST | `order/v2/sell` | Body:`requestBody` | `c<SuccessResponse<OrderSellDTO>>` | ⊘ not tested (write) |
| 28 | GET | `portfolio/v2/detail` | QueryMap:`map` | `c<SuccessResponse<PortfolioDetailDTO>>` | 🔑 401 |
| 29 | GET | `portfolio/v2/list` | QueryMap:`map` | `c<SuccessResponse<PortfolioDTO>>` | 🔑 401 |
| 30 | GET | `portfolio/v2/summary` | — | `c<SuccessResponse<PortfolioSummaryDTO>>` | 🔑 401 |
| 31 | GET | `portfolio/v2/transferable-stocks` | QueryMap:`map` | `c<SuccessResponse<TransferableStocksDTO>>` | 🔑 401 |
| 32 | GET | `securities/order/v1/list` | QueryMap:`map` | `c<SuccessResponse<List<OrderListDTO>>>` | 🔑 401 |
| 33 | GET | `smart-order` | QueryMap:`map` | `c<SuccessResponse<List<SmartOrderDTO>>>` | 🔑 401 |
| 34 | POST | `smart-order/trailing-stop/v1/order` | Body:`requestBody` | `c<SuccessResponse<OrderSellDTO>>` | ⊘ not tested (write) |
| 35 | DELETE | `smart-order/trailing-stop/v1/order/{order_id}` | Path:`order_id` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 36 | PATCH | `smart-order/trailing-stop/v1/order/{order_id}` | Path:`order_id` · Body:`requestBody` | `c<SuccessResponse<OrderSellDTO>>` | ⊘ not tested (write) |
| 37 | GET | `trading/info` | Query:`features` | `c<SuccessResponse<TradingInfoDTO>>` | 🔑 401 |
| 38 | POST | `verification/v1/initialize` | Body:`requestBody` | `c<SuccessResponse<InitializeVerificationDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getBalanceCash  [GET balance/cash]
curl -X GET "https://carina.stockbit.com/balance/cash" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getCashInfo  [GET balance/cash/info]
curl -X GET "https://carina.stockbit.com/balance/cash/info?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getExercisableStock  [GET exercise/exercisable]
curl -X GET "https://carina.stockbit.com/exercise/exercisable?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getExerciseTradableStatus  [GET exercise/tradable]
curl -X GET "https://carina.stockbit.com/exercise/tradable" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getTradingFormula  [GET formula/v2]
curl -X GET "https://carina.stockbit.com/formula/v2" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getTradingHistory  [GET history]
curl -X GET "https://carina.stockbit.com/history?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getRealizedTradingHistory  [GET history/realized]
curl -X GET "https://carina.stockbit.com/history/realized?<map>=<Map<String, String>>&transaction_types=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getRealizedTradingHistoryDetail  [GET history/realized/detail]
curl -X GET "https://carina.stockbit.com/history/realized/detail?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# createOrderNego  [POST nego-engine/v1/order]
curl -X POST "https://carina.stockbit.com/nego-engine/v1/order" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getOrderBookNego  [GET nego-engine/v1/order-book/{symbol}]
curl -X GET "https://carina.stockbit.com/nego-engine/v1/order-book/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getNegoOrderQueue  [GET nego-engine/v1/order-queue]
curl -X GET "https://carina.stockbit.com/nego-engine/v1/order-queue?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getOrderNegoPreview  [POST nego-engine/v1/order/preview]
curl -X POST "https://carina.stockbit.com/nego-engine/v1/order/preview" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# requestCancelNego  [DELETE nego-engine/v1/order/{order_id}]
curl -X DELETE "https://carina.stockbit.com/nego-engine/v1/order/{order_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# abortCancelNego  [PATCH nego-engine/v1/order/{order_id}/abort-cancel]
curl -X PATCH "https://carina.stockbit.com/nego-engine/v1/order/{order_id}/abort-cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# respondCancelNego  [PATCH nego-engine/v1/order/{order_id}/confirm-cancel]
curl -X PATCH "https://carina.stockbit.com/nego-engine/v1/order/{order_id}/confirm-cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# respondMatchingPendingNego  [POST nego-engine/v1/order/{order_id}/confirm-matching]
curl -X POST "https://carina.stockbit.com/nego-engine/v1/order/{order_id}/confirm-matching" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getMaintenanceStatus  [GET oms/auth/maintenance/status]
curl -X GET "https://carina.stockbit.com/oms/auth/maintenance/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# buyDayTradeOrder  [POST order/day-trade/v1/buy]
curl -X POST "https://carina.stockbit.com/order/day-trade/v1/buy" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# cancelDayTradeOrder  [POST order/day-trade/v1/cancel]
curl -X POST "https://carina.stockbit.com/order/day-trade/v1/cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<OrderDetailCancelDataParam>'   # JSON body

# postOrderDayTradeSell  [POST order/day-trade/v1/sell]
curl -X POST "https://carina.stockbit.com/order/day-trade/v1/sell" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# postOrderAmendBulk  [POST order/v2/amend/bulk]
curl -X POST "https://carina.stockbit.com/order/v2/amend/bulk" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<PostOrderAmendBulkDataParam>'   # JSON body

# postOrderBulkCancel  [POST order/v2/bulk-cancel]
curl -X POST "https://carina.stockbit.com/order/v2/bulk-cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<PostOrderBulkCancelDataParam>'   # JSON body

# buyOrder  [POST order/v2/buy]
curl -X POST "https://carina.stockbit.com/order/v2/buy" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# cancelRegularOrder  [POST order/v2/cancel]
curl -X POST "https://carina.stockbit.com/order/v2/cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<OrderDetailCancelDataParam>'   # JSON body

# getOrderDetail  [GET order/v2/detail]
curl -X GET "https://carina.stockbit.com/order/v2/detail?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getOrderList  [GET order/v2/list]
curl -X GET "https://carina.stockbit.com/order/v2/list" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# postOrderSell  [POST order/v2/sell]
curl -X POST "https://carina.stockbit.com/order/v2/sell" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getPortfolioDetail  [GET portfolio/v2/detail]
curl -X GET "https://carina.stockbit.com/portfolio/v2/detail?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getPortfolio  [GET portfolio/v2/list]
curl -X GET "https://carina.stockbit.com/portfolio/v2/list?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getPortfolioSummary  [GET portfolio/v2/summary]
curl -X GET "https://carina.stockbit.com/portfolio/v2/summary" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getPortfolioTransferableStock  [GET portfolio/v2/transferable-stocks]
curl -X GET "https://carina.stockbit.com/portfolio/v2/transferable-stocks?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getOrderList  [GET securities/order/v1/list]
curl -X GET "https://carina.stockbit.com/securities/order/v1/list?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getSmartOrder  [GET smart-order]
curl -X GET "https://carina.stockbit.com/smart-order?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# postSellTrailingStop  [POST smart-order/trailing-stop/v1/order]
curl -X POST "https://carina.stockbit.com/smart-order/trailing-stop/v1/order" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# cancelTrailingStop  [DELETE smart-order/trailing-stop/v1/order/{order_id}]
curl -X DELETE "https://carina.stockbit.com/smart-order/trailing-stop/v1/order/{order_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# postAmendTrailingStop  [PATCH smart-order/trailing-stop/v1/order/{order_id}]
curl -X PATCH "https://carina.stockbit.com/smart-order/trailing-stop/v1/order/{order_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getTradingInfo  [GET trading/info]
curl -X GET "https://carina.stockbit.com/trading/info?features=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# initSecuritiesVerification  [POST verification/v1/initialize]
curl -X POST "https://carina.stockbit.com/verification/v1/initialize" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

```
</details>

## 5. `BalanceService`  (13 endpoint)
<sub>com/stockbit/remote/api/securities/BalanceService.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `account` | — | `c<SuccessResponse<TradingAccountDataDTO>>` | ⚪ 404 |
| 2 | GET | `account/bank` | — | `A<TradingStockbitAccountBankDetailResponse>` | 🔑 401 |
| 3 | GET | `balance/cash` | — | `A<CashOnHandResponse>` | 🔑 401 |
| 4 | GET | `balance/cash/info` | QueryMap:`map` | `A<CashInfoResponse>` | 🔑 401 |
| 5 | GET | `balance/withdrawable` | — | `A<TradingStockbitWithdrawalBalanceResponse>` | 🔑 401 |
| 6 | GET | `deposit/guide` | — | `A<TradingStockbitDepositGuideResponse>` | 🔑 401 |
| 7 | GET | `history/deposit` | QueryMap:`map` | `A<Object>` | 🔑 401 |
| 8 | GET | `history/withdraw` | QueryMap:`map` | `A<Object>` | 🔑 401 |
| 9 | GET | `withdrawal/v1/foreign-rules` | — | `A<TradingStockbitWithdrawalForeignBankRulesResponse>` | 🔑 401 |
| 10 | GET | `withdrawal/v1/option/{bank}` | Path:`bank` · QueryMap:`map` | `A<TransferMethodResponse>` | 🔑 401 |
| 11 | GET | `withdrawal/v1/option/{bank}/confirmation/{method}` | Path:`bank` · Path:`str2` | `A<WdOperationalTimeResponse>` | 🔑 401 |
| 12 | POST | `withdrawal/v1/withdraw` | Body:`requestBody` | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 13 | POST | `withdrawal/v1/withdraw/multi-account` | Body:`withdrawMultipleRequest` | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getAccount  [GET account]
curl -X GET "https://carina.stockbit.com/account" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getAccountBankDetail  [GET account/bank]
curl -X GET "https://carina.stockbit.com/account/bank" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getCashOnHand  [GET balance/cash]
curl -X GET "https://carina.stockbit.com/balance/cash" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getCashInfo  [GET balance/cash/info]
curl -X GET "https://carina.stockbit.com/balance/cash/info?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# withdrawBalance  [GET balance/withdrawable]
curl -X GET "https://carina.stockbit.com/balance/withdrawable" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# depositGuide  [GET deposit/guide]
curl -X GET "https://carina.stockbit.com/deposit/guide" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# depositHistory  [GET history/deposit]
curl -X GET "https://carina.stockbit.com/history/deposit?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# withdrawHistory  [GET history/withdraw]
curl -X GET "https://carina.stockbit.com/history/withdraw?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getForeignBankRules  [GET withdrawal/v1/foreign-rules]
curl -X GET "https://carina.stockbit.com/withdrawal/v1/foreign-rules" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# withdrawalTransferMethod  [GET withdrawal/v1/option/{bank}]
curl -X GET "https://carina.stockbit.com/withdrawal/v1/option/{bank}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# wdOperationalTime  [GET withdrawal/v1/option/{bank}/confirmation/{method}]
curl -X GET "https://carina.stockbit.com/withdrawal/v1/option/{bank}/confirmation/{method}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# withdraw  [POST withdrawal/v1/withdraw]
curl -X POST "https://carina.stockbit.com/withdrawal/v1/withdraw" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# withdrawMultipleAccount  [POST withdrawal/v1/withdraw/multi-account]
curl -X POST "https://carina.stockbit.com/withdrawal/v1/withdraw/multi-account" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<WithdrawMultipleRequest>'   # JSON body

```
</details>

## 6. `AuthSecuritiesApi`  (10 endpoint)
<sub>com/stockbit/remote/api/securities/AuthSecuritiesApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `auth/biometric/register` | Body:`requestBody` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | POST | `auth/biometric/remove` | — | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 3 | POST | `auth/pin/validate` | Body:`requestBody` | `c<SuccessResponse<SecuritiesAuthValidatePinDTO>>` | ⊘ not tested (write) |
| 4 | POST | `auth/v2/login/biometric` | Body:`requestBody` | `c<SuccessResponse<SecuritiesAuthLoginDTO>>` | ⊘ not tested (write) |
| 5 | POST | `auth/v2/pin/change/otp/send` | Body:`requestBody` | `c<SuccessResponse<ChangePinSendOtpDTO>>` | ⊘ not tested (write) |
| 6 | POST | `auth/v2/pin/change/otp/verify` | Body:`requestBody` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 7 | POST | `auth/v2/pin/reset/confirm` | Body:`requestBody` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 8 | POST | `auth/v2/pin/reset/new` | Body:`requestBody` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 9 | POST | `auth/v2/pin/reset/otp/send` | Body:`requestBody` | `c<SuccessResponse<ResetPinSendOtpDTO>>` | ⊘ not tested (write) |
| 10 | POST | `auth/v2/pin/reset/otp/verify` | Body:`requestBody` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# biometricAdd  [POST auth/biometric/register]
curl -X POST "https://carina.stockbit.com/auth/biometric/register" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# biometricRemove  [POST auth/biometric/remove]
curl -X POST "https://carina.stockbit.com/auth/biometric/remove" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# validatePin  [POST auth/pin/validate]
curl -X POST "https://carina.stockbit.com/auth/pin/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# loginBiometric  [POST auth/v2/login/biometric]
curl -X POST "https://carina.stockbit.com/auth/v2/login/biometric" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# changePinSendOtp  [POST auth/v2/pin/change/otp/send]
curl -X POST "https://carina.stockbit.com/auth/v2/pin/change/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# changePinVerifyOtp  [POST auth/v2/pin/change/otp/verify]
curl -X POST "https://carina.stockbit.com/auth/v2/pin/change/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# confirmResetPin  [POST auth/v2/pin/reset/confirm]
curl -X POST "https://carina.stockbit.com/auth/v2/pin/reset/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# resetPin  [POST auth/v2/pin/reset/new]
curl -X POST "https://carina.stockbit.com/auth/v2/pin/reset/new" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# resetPinSendOtp  [POST auth/v2/pin/reset/otp/send]
curl -X POST "https://carina.stockbit.com/auth/v2/pin/reset/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# resetPinVerifyOtp  [POST auth/v2/pin/reset/otp/verify]
curl -X POST "https://carina.stockbit.com/auth/v2/pin/reset/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

```
</details>

## 7. `AuthSecuritiesService`  (9 endpoint)
<sub>com/stockbit/remote/api/securities/AuthSecuritiesService.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `auth/biometric/register` | Body:`requestBody` | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 2 | POST | `auth/biometric/remove` | — | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 3 | POST | `auth/logout` | — | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 4 | POST | `auth/pin/change` | Body:`requestBody` | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 5 | POST | `auth/pin/validate` | Body:`requestBody` | `A<TradingStockbitVerifyPinResponse>` | ⊘ not tested (write) |
| 6 | POST | `auth/refresh` | HeaderMap:`map` | `A<TradingStockbitRefreshTokenResponse>` | ⊘ not tested (write) |
| 7 | POST | `auth/requestotp` | FieldMap:`map` | `A<Object>` | ⊘ not tested (write) |
| 8 | POST | `auth/v2/login` | Body:`requestBody` | `A<TradingStockbitEnterPinResponse>` | ⊘ not tested (write) |
| 9 | POST | `auth/v2/login/biometric` | Body:`requestBody` | `A<TradingStockbitEnterPinResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# biometricAdd  [POST auth/biometric/register]
curl -X POST "https://carina.stockbit.com/auth/biometric/register" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# biometricRemove  [POST auth/biometric/remove]
curl -X POST "https://carina.stockbit.com/auth/biometric/remove" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# logoutSecurities  [POST auth/logout]
curl -X POST "https://carina.stockbit.com/auth/logout" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# changePin  [POST auth/pin/change]
curl -X POST "https://carina.stockbit.com/auth/pin/change" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# validatePin  [POST auth/pin/validate]
curl -X POST "https://carina.stockbit.com/auth/pin/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getRefreshTokenSecurities  [POST auth/refresh]
curl -X POST "https://carina.stockbit.com/auth/refresh" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "X-Custom-Header: ..."   # @HeaderMap

# requestOtp  [POST auth/requestotp]
curl -X POST "https://carina.stockbit.com/auth/requestotp" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "<map>=<Map<String, String>>"

# loginPin  [POST auth/v2/login]
curl -X POST "https://carina.stockbit.com/auth/v2/login" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# loginBiometric  [POST auth/v2/login/biometric]
curl -X POST "https://carina.stockbit.com/auth/v2/login/biometric" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

```
</details>

## 8. `CashSweepApi`  (8 endpoint)
<sub>com/stockbit/remote/api/cashsweep/CashSweepApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `intraservice/cash-sweep/v1/activation` | Body:`activateCashSweepRequest` | `c<SuccessResponse<CashSweepActivationDTO>>` | ⊘ not tested (write) |
| 2 | GET | `intraservice/cash-sweep/v1/fund-documents` | — | `c<SuccessResponse<CashSweepDocsDTO>>` | 🔑 401 |
| 3 | GET | `intraservice/cash-sweep/v1/info` | — | `c<SuccessResponse<CashSweepDTO>>` | 🔑 401 |
| 4 | POST | `intraservice/cash-sweep/v1/redemption` | Body:`redemptionCashSweepRequest` | `c<SuccessResponse<CashSweepRedemptionDTO>>` | ⊘ not tested (write) |
| 5 | POST | `intraservice/cash-sweep/v1/reserved-cash` | Body:`editReservedCashRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 6 | GET | `intraservice/cash-sweep/v1/stats` | — | `c<SuccessResponse<CashSweepStatsDTO>>` | 🔑 401 |
| 7 | POST | `intraservice/cash-sweep/v1/toggle` | Body:`toggleCashSweepRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 8 | GET | `intraservice/cash-sweep/v1/withdraw/preview` | QueryMap:`map` | `c<SuccessResponse<CashSweepWithdrawPreviewDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# activateCashSweep  [POST intraservice/cash-sweep/v1/activation]
curl -X POST "https://carina.stockbit.com/intraservice/cash-sweep/v1/activation" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<ActivateCashSweepRequest>'   # JSON body

# getCashSweepDocs  [GET intraservice/cash-sweep/v1/fund-documents]
curl -X GET "https://carina.stockbit.com/intraservice/cash-sweep/v1/fund-documents" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getCashSweepInfo  [GET intraservice/cash-sweep/v1/info]
curl -X GET "https://carina.stockbit.com/intraservice/cash-sweep/v1/info" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# redemptionCashSweep  [POST intraservice/cash-sweep/v1/redemption]
curl -X POST "https://carina.stockbit.com/intraservice/cash-sweep/v1/redemption" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RedemptionCashSweepRequest>'   # JSON body

# editReservedCash  [POST intraservice/cash-sweep/v1/reserved-cash]
curl -X POST "https://carina.stockbit.com/intraservice/cash-sweep/v1/reserved-cash" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<EditReservedCashRequest>'   # JSON body

# getCashSweepStats  [GET intraservice/cash-sweep/v1/stats]
curl -X GET "https://carina.stockbit.com/intraservice/cash-sweep/v1/stats" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# toggleCashSweep  [POST intraservice/cash-sweep/v1/toggle]
curl -X POST "https://carina.stockbit.com/intraservice/cash-sweep/v1/toggle" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<ToggleCashSweepRequest>'   # JSON body

# getCashSweepWithdrawPreview  [GET intraservice/cash-sweep/v1/withdraw/preview]
curl -X GET "https://carina.stockbit.com/intraservice/cash-sweep/v1/withdraw/preview?<map>=<Map<String, Double>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 9. `TransactionService`  (8 endpoint)
<sub>com/stockbit/remote/api/securities/TransactionService.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `order/day-trade/v1/amend` | Body:`requestBody` | `A<StockbitAmendOrderResponse>` | ⊘ not tested (write) |
| 2 | POST | `order/day-trade/v1/cancel` | Body:`requestBody` | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 3 | POST | `order/v2/amend/bulk` | Body:`amendBulkRequestData` | `A<StockbitAmendOrderResponse>` | ⊘ not tested (write) |
| 4 | POST | `order/v2/bulk-cancel` | Body:`requestBody` | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 5 | POST | `order/v2/cancel` | Body:`requestBody` | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 6 | GET | `order/v2/list` | QueryMap:`map` | `A<TradingOrderListResponse>` | 🔑 401 |
| 7 | DELETE | `smart-order` | Body:`map` | `A<SetSmartOrderResponse>` | ⊘ not tested (write) |
| 8 | POST | `smart-order/tnc` | Body:`map` | `A<SetSmartOrderResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# amendDayTrade  [POST order/day-trade/v1/amend]
curl -X POST "https://carina.stockbit.com/order/day-trade/v1/amend" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# cancelDayTradeOrder  [POST order/day-trade/v1/cancel]
curl -X POST "https://carina.stockbit.com/order/day-trade/v1/cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# amendBulk  [POST order/v2/amend/bulk]
curl -X POST "https://carina.stockbit.com/order/v2/amend/bulk" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<AmendBulkRequestData>'   # JSON body

# bulkCancelOrder  [POST order/v2/bulk-cancel]
curl -X POST "https://carina.stockbit.com/order/v2/bulk-cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# cancelOrder  [POST order/v2/cancel]
curl -X POST "https://carina.stockbit.com/order/v2/cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getOrderList  [GET order/v2/list]
curl -X GET "https://carina.stockbit.com/order/v2/list?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# deleteSmartOrder  [DELETE smart-order]
curl -X DELETE "https://carina.stockbit.com/smart-order" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, Integer>>'   # JSON body

# setTnQSmartOrder  [POST smart-order/tnc]
curl -X POST "https://carina.stockbit.com/smart-order/tnc" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

```
</details>

## 10. `BondsApi`  (7 endpoint)
<sub>com/stockbit/remote/api/BondsApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `bond/v1/buy` | Body:`bondBuyRequest` | `c<SuccessResponse<BondBuyDTO>>` | ⊘ not tested (write) |
| 2 | GET | `bond/v1/buy/preview` | QueryMap:`map` | `c<SuccessResponse<BondBuyPreviewDTO>>` | 🔑 401 |
| 3 | GET | `bond/v1/orders/{id}` | Path:`str` | `c<SuccessResponse<BondOrderDetailDTO>>` | 🔑 401 |
| 4 | GET | `bond/v1/portfolio` | — | `c<SuccessResponse<BondsPortfolioListDTO>>` | 🔑 401 |
| 5 | GET | `bond/v1/portfolio/{symbol}` | Path:`symbol` · QueryMap:`map` | `c<SuccessResponse<BondsPortfolioDetailDTO>>` | 🔑 401 |
| 6 | POST | `bond/v1/sell` | Body:`bondSellRequest` | `c<SuccessResponse<BondSellDTO>>` | ⊘ not tested (write) |
| 7 | GET | `bond/v1/sell/preview` | QueryMap:`map` | `c<SuccessResponse<BondSellPreviewDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# postBondBuy  [POST bond/v1/buy]
curl -X POST "https://carina.stockbit.com/bond/v1/buy" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<BondBuyRequest>'   # JSON body

# getBondBuyPreview  [GET bond/v1/buy/preview]
curl -X GET "https://carina.stockbit.com/bond/v1/buy/preview?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getBondOrderDetail  [GET bond/v1/orders/{id}]
curl -X GET "https://carina.stockbit.com/bond/v1/orders/{id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getBondPortfolioList  [GET bond/v1/portfolio]
curl -X GET "https://carina.stockbit.com/bond/v1/portfolio" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getBondPortfolioDetail  [GET bond/v1/portfolio/{symbol}]
curl -X GET "https://carina.stockbit.com/bond/v1/portfolio/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# postBondSell  [POST bond/v1/sell]
curl -X POST "https://carina.stockbit.com/bond/v1/sell" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<BondSellRequest>'   # JSON body

# getBondPreviewSell  [GET bond/v1/sell/preview]
curl -X GET "https://carina.stockbit.com/bond/v1/sell/preview?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 11. `SmartOrderApi`  (7 endpoint)
<sub>com/stockbit/remote/api/SmartOrderApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `smart-order/bracket-order/v1/order` | Body:`postBracketOrderOrderDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | PATCH | `smart-order/bracket-order/v1/order/{order_id}` | Path:`order_id` · Body:`amendBracketOrderParentRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 3 | POST | `smart-order/stop-order/v1/order` | Body:`postStopOrderParentDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 4 | PATCH | `smart-order/stop-order/v1/order/{order_id}` | Path:`order_id` · Body:`map` · _Multipart_ | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 5 | PATCH | `smart-order/stop-order/v1/order/{order_id}` | Path:`order_id` · Body:`patchStopOrderDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 6 | POST | `smart-order/volume-trigger-order/v1/order` | Body:`sellVolumeTriggerOrderDataParam` | `c<SuccessResponse<OrderBuyDTO>>` | ⊘ not tested (write) |
| 7 | PATCH | `smart-order/volume-trigger-order/v1/order/{order_id}` | Path:`order_id` · Body:`amendVolumeTriggerOrderDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# postBracketOrderOrder  [POST smart-order/bracket-order/v1/order]
curl -X POST "https://carina.stockbit.com/smart-order/bracket-order/v1/order" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<PostBracketOrderOrderDataParam>'   # JSON body

# amendBracketOrderParent  [PATCH smart-order/bracket-order/v1/order/{order_id}]
curl -X PATCH "https://carina.stockbit.com/smart-order/bracket-order/v1/order/{order_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<AmendBracketOrderParentRequest>'   # JSON body

# postStopOrderParent  [POST smart-order/stop-order/v1/order]
curl -X POST "https://carina.stockbit.com/smart-order/stop-order/v1/order" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<PostStopOrderParentDataParam>'   # JSON body

# amendBracketOrderChild  [PATCH smart-order/stop-order/v1/order/{order_id}]
curl -X PATCH "https://carina.stockbit.com/smart-order/stop-order/v1/order/{order_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# amendStopOrder  [PATCH smart-order/stop-order/v1/order/{order_id}]
curl -X PATCH "https://carina.stockbit.com/smart-order/stop-order/v1/order/{order_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<PatchStopOrderDataParam>'   # JSON body

# sellVolumeTriggerOrder  [POST smart-order/volume-trigger-order/v1/order]
curl -X POST "https://carina.stockbit.com/smart-order/volume-trigger-order/v1/order" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<SellVolumeTriggerOrderDataParam>'   # JSON body

# amendVolumeTriggerOrder  [PATCH smart-order/volume-trigger-order/v1/order/{order_id}]
curl -X PATCH "https://carina.stockbit.com/smart-order/volume-trigger-order/v1/order/{order_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<AmendVolumeTriggerOrderDataParam>'   # JSON body

```
</details>

## 12. `TradingPinApi`  (7 endpoint)
<sub>com/stockbit/remote/api/pin/v3/TradingPinApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `/auth/v3/pin/change/current-pin/verify` | Body:`map` | `c<SuccessResponse<ChangePinDTO>>` | ⊘ not tested (write) |
| 2 | POST | `/auth/v3/pin/change/face-matching/verify` | Body:`map` | `c<SuccessResponse<ChangePinDTO>>` | ⊘ not tested (write) |
| 3 | POST | `/auth/v3/pin/change/init` | — | `c<SuccessResponse<ChangePinDTO>>` | ⊘ not tested (write) |
| 4 | POST | `/auth/v3/pin/change/new-pin/confirm` | Body:`map` | `c<SuccessResponse<ChangePinDTO>>` | ⊘ not tested (write) |
| 5 | POST | `/auth/v3/pin/change/new-pin/create` | Body:`map` | `c<SuccessResponse<ChangePinDTO>>` | ⊘ not tested (write) |
| 6 | POST | `/auth/v3/pin/change/otp/send` | Body:`map` | `c<SuccessResponse<ChangePinRequestOtpDTO>>` | ⊘ not tested (write) |
| 7 | POST | `/auth/v3/pin/change/otp/verify` | Body:`map` | `c<SuccessResponse<ChangePinDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# postVerifyCurrentPin  [POST /auth/v3/pin/change/current-pin/verify]
curl -X POST "https://carina.stockbit.com/auth/v3/pin/change/current-pin/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postVerifyFaceMatching  [POST /auth/v3/pin/change/face-matching/verify]
curl -X POST "https://carina.stockbit.com/auth/v3/pin/change/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postInitChangePin  [POST /auth/v3/pin/change/init]
curl -X POST "https://carina.stockbit.com/auth/v3/pin/change/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# postConfirmNewPin  [POST /auth/v3/pin/change/new-pin/confirm]
curl -X POST "https://carina.stockbit.com/auth/v3/pin/change/new-pin/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postCreateNewPin  [POST /auth/v3/pin/change/new-pin/create]
curl -X POST "https://carina.stockbit.com/auth/v3/pin/change/new-pin/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postRequestOtp  [POST /auth/v3/pin/change/otp/send]
curl -X POST "https://carina.stockbit.com/auth/v3/pin/change/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postVerifyOtp  [POST /auth/v3/pin/change/otp/verify]
curl -X POST "https://carina.stockbit.com/auth/v3/pin/change/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

```
</details>

## 13. `SubAccountApi`  (5 endpoint)
<sub>com/stockbit/remote/api/securities/SubAccountApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `/v2/sub-account/list` | — | `c<SuccessResponse<SubAccountDTO>>` | 🔑 401 |
| 2 | POST | `auth/account/switch` | Body:`switchAccountRequest` | `c<SuccessResponse<SwitchAccountDTO>>` | ⊘ not tested (write) |
| 3 | POST | `sub-account/create` | Body:`createNewPortfolioRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 4 | GET | `sub-account/purposes` | — | `c<SuccessResponse<PortfolioPurposeDTO>>` | 🔑 401 |
| 5 | POST | `sub-account/rename` | Body:`renamePortfolioRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getSubAccountList  [GET /v2/sub-account/list]
curl -X GET "https://carina.stockbit.com/v2/sub-account/list" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# switchAccount  [POST auth/account/switch]
curl -X POST "https://carina.stockbit.com/auth/account/switch" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<SwitchAccountRequest>'   # JSON body

# createNewPortfolio  [POST sub-account/create]
curl -X POST "https://carina.stockbit.com/sub-account/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<CreateNewPortfolioRequest>'   # JSON body

# getPortfolioPurposeList  [GET sub-account/purposes]
curl -X GET "https://carina.stockbit.com/sub-account/purposes" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# renamePortfolio  [POST sub-account/rename]
curl -X POST "https://carina.stockbit.com/sub-account/rename" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RenamePortfolioRequest>'   # JSON body

```
</details>

## 14. `TradingPerformanceApi`  (5 endpoint)
<sub>com/stockbit/remote/api/TradingPerformanceApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `history/performance/portfolio/cumulative-return` | QueryMap:`map` | `c<SuccessResponse<CumulativeReturnDTO>>` | 🔑 401 |
| 2 | GET | `history/performance/portfolio/stock-allocation` | — | `c<SuccessResponse<PortfolioAllocationDTO>>` | 🔑 401 |
| 3 | GET | `history/performance/portfolio/total-equity` | QueryMap:`map` | `c<SuccessResponse<PortfolioTotalEquityDTO>>` | 🔑 401 |
| 4 | GET | `history/performance/portfolio/total-equity-return` | QueryMap:`map` | `c<SuccessResponse<List<PortfolioTotalEquityReturnDTO>>>` | 🔑 401 |
| 5 | GET | `history/performance/trade` | QueryMap:`map` | `c<SuccessResponse<TradePerformanceDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCumulativeReturn  [GET history/performance/portfolio/cumulative-return]
curl -X GET "https://carina.stockbit.com/history/performance/portfolio/cumulative-return?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getPortfolioAllocation  [GET history/performance/portfolio/stock-allocation]
curl -X GET "https://carina.stockbit.com/history/performance/portfolio/stock-allocation" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getPortfolioTotalEquity  [GET history/performance/portfolio/total-equity]
curl -X GET "https://carina.stockbit.com/history/performance/portfolio/total-equity?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getPortfolioTotalEquityReturn  [GET history/performance/portfolio/total-equity-return]
curl -X GET "https://carina.stockbit.com/history/performance/portfolio/total-equity-return?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getTradePerformance  [GET history/performance/trade]
curl -X GET "https://carina.stockbit.com/history/performance/trade?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 15. `ExerciseService`  (4 endpoint)
<sub>com/stockbit/remote/api/securities/ExerciseService.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `exercise` | — | `A<ExerciseListResponse>` | 🔑 401 |
| 2 | POST | `exercise` | Body:`requestBody` | `A<StockbitSecuritiesBaseResponseImpl>` | ⊘ not tested (write) |
| 3 | GET | `exercise/exercisable` | QueryMap:`map` | `A<TradingExerciseableStockResponse>` | 🔑 401 |
| 4 | GET | `exercise/tradable` | — | `A<TradingExerciseTradeableResponse>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# exerciseList  [GET exercise]
curl -X GET "https://carina.stockbit.com/exercise" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# exerciseOrder  [POST exercise]
curl -X POST "https://carina.stockbit.com/exercise" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# exercisableList  [GET exercise/exercisable]
curl -X GET "https://carina.stockbit.com/exercise/exercisable?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# exerciseTradable  [GET exercise/tradable]
curl -X GET "https://carina.stockbit.com/exercise/tradable" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 16. `BalanceApi`  (3 endpoint)
<sub>com/stockbit/remote/api/securities/BalanceApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `balance/withdrawable` | QueryMap:`map` | `c<SuccessResponse<BalanceWithdrawableDTO>>` | 🔑 401 |
| 2 | GET | `history/deposit` | QueryMap:`map` | `c<SuccessResponse<DepositHistoryDTO>>` | 🔑 401 |
| 3 | GET | `history/withdraw` | QueryMap:`map` | `c<SuccessResponse<WithdrawalHistoryDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getWithdrawalBalance  [GET balance/withdrawable]
curl -X GET "https://carina.stockbit.com/balance/withdrawable?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getDepositHistory  [GET history/deposit]
curl -X GET "https://carina.stockbit.com/history/deposit?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getWithdrawalHistory  [GET history/withdraw]
curl -X GET "https://carina.stockbit.com/history/withdraw?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 17. `MarginTradingApi`  (3 endpoint)
<sub>com/stockbit/remote/api/margintrading/MarginTradingApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `/sub-account/margin-activation-page-info` | — | `c<SuccessResponse<MarginTradingActivationDTO>>` | 🔑 401 |
| 2 | POST | `position/margin-oa/collaterals/me` | Body:`collateralRequestDataParam` | `c<SuccessResponse<MarginTradingCollateralSubmissionDTO>>` | ⊘ not tested (write) |
| 3 | POST | `v2/account/sub-account/margin` | Body:`postMarginCreationRequest` | `c<SuccessResponse<UploadMarginCreationDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getMarginTradingActivation  [GET /sub-account/margin-activation-page-info]
curl -X GET "https://carina.stockbit.com/sub-account/margin-activation-page-info" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# postMarginTradingCollaterals  [POST position/margin-oa/collaterals/me]
curl -X POST "https://carina.stockbit.com/position/margin-oa/collaterals/me" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<CollateralRequestDataParam>'   # JSON body

# postMarginTradingCreationRequest  [POST v2/account/sub-account/margin]
curl -X POST "https://carina.stockbit.com/v2/account/sub-account/margin" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<PostMarginCreationRequest>'   # JSON body

```
</details>

## 18. `AccountCarinaApi`  (2 endpoint)
<sub>com/stockbit/remote/api/AccountCarinaApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `account/personal` | — | `c<SuccessResponse<TradingAccountDataDTO>>` | 🔑 401 |
| 2 | GET | `v2/account/bank` | — | `A<BankAccountInformationResponse>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getAccount  [GET account/personal]
curl -X GET "https://carina.stockbit.com/account/personal" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# getListUserBank  [GET v2/account/bank]
curl -X GET "https://carina.stockbit.com/v2/account/bank" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 19. `AmendBankApi`  (2 endpoint)
<sub>com/stockbit/remote/api/amendbank/AmendBankApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `/v3/account/amend/bank` | Body:`submitAmendBankRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | GET | `v1/account/suspension/list` | — | `c<SuccessResponse<AmendBankSuspensionListDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# submitAmendBank  [POST /v3/account/amend/bank]
curl -X POST "https://carina.stockbit.com/v3/account/amend/bank" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<SubmitAmendBankRequest>'   # JSON body

# getAmendBankSuspensionList  [GET v1/account/suspension/list]
curl -X GET "https://carina.stockbit.com/v1/account/suspension/list" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 20. `IntraserviceApi`  (2 endpoint)
<sub>com/stockbit/remote/api/IntraserviceApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `intraservice/multi-portfolio/v1/move-cash` | Body:`moveCashRequest` | `c<SuccessResponse<MoveCashDTO>>` | ⊘ not tested (write) |
| 2 | POST | `intraservice/multi-portfolio/v1/move-stock` | Body:`moveStockRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# moveCash  [POST intraservice/multi-portfolio/v1/move-cash]
curl -X POST "https://carina.stockbit.com/intraservice/multi-portfolio/v1/move-cash" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<MoveCashRequest>'   # JSON body

# moveStock  [POST intraservice/multi-portfolio/v1/move-stock]
curl -X POST "https://carina.stockbit.com/intraservice/multi-portfolio/v1/move-stock" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<MoveStockRequest>'   # JSON body

```
</details>

## 21. `UserSecuritiesServiceLegacy`  (2 endpoint)
<sub>com/stockbit/remote/api/UserSecuritiesServiceLegacy.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `user/profile/password` | FieldMap:`map` · _Multipart_ | `A<BaseResponseLegacyImpl>` | ⊘ not tested (write) |
| 2 | GET | `user/setting/email/verify` | — | `A<Object>` | ⚪ 404 |

<details><summary>cURL — semua endpoint</summary>

```bash
# editPassword  [POST user/profile/password]
curl -X POST "https://carina.stockbit.com/user/profile/password" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

# verifyEmail  [GET user/setting/email/verify]
curl -X GET "https://carina.stockbit.com/user/setting/email/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 22. `AccountService`  (1 endpoint)
<sub>com/stockbit/remote/api/securities/AccountService.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `account/sub-account/detail` | Query:`type` | `A<SubAccountResponse>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getSubAccountStatus  [GET account/sub-account/detail]
curl -X GET "https://carina.stockbit.com/account/sub-account/detail?type=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 23. `DepositBalanceApi`  (1 endpoint)
<sub>com/stockbit/remote/api/DepositBalanceApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `deposit/guide` | — | `c<SuccessResponse<DepositDetailDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getDepositInfo  [GET deposit/guide]
curl -X GET "https://carina.stockbit.com/deposit/guide" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 24. `KturServiceAPI`  (1 endpoint)
<sub>com/stockbit/remote/api/KturServiceAPI.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `settlement-report/v1/kturs` | QueryMap:`map` | `c<SuccessResponse<KturListDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getKturList  [GET settlement-report/v1/kturs]
curl -X GET "https://carina.stockbit.com/settlement-report/v1/kturs?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 25. `PortfolioService`  (1 endpoint)
<sub>com/stockbit/remote/api/securities/PortfolioService.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `history/v3` | QueryMap:`map` | `A<Object>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getHistoryTransaction  [GET history/v3]
curl -X GET "https://carina.stockbit.com/history/v3?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

## 26. `StockApi`  (1 endpoint)
<sub>com/stockbit/remote/api/securities/StockApi.java · qualifier `SECURITIES_NEW_CORE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `stock/tradable` | Query:`stock_codes` | `c<SuccessResponse<List<StockTradableDTO>>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getStockTradable  [GET stock/tradable]
curl -X GET "https://carina.stockbit.com/stock/tradable?stock_codes=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: Bearer $CARINA_TOKEN"

```
</details>

# ━━ HOST: EXODUS — `https://exodus.stockbit.com` ━━

**Auth:** Bearer (social access token)

## 27. `UserApi`  (82 endpoint)
<sub>com/stockbit/remote/api/UserApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `/user/credential/v1/non-login/phone/forgot/current-phone/verify` | Body:`forgotPhoneRequest` | `c<SuccessResponse<ForgotPhoneDTO>>` | ⊘ not tested (write) |
| 2 | POST | `/user/credential/v1/non-login/phone/forgot/face-matching/verify` | Body:`map` | `c<SuccessResponse<ForgotPhoneDTO>>` | ⊘ not tested (write) |
| 3 | POST | `/user/credential/v1/non-login/phone/forgot/init` | Body:`map` | `c<SuccessResponse<ForgotPhoneDTO>>` | ⊘ not tested (write) |
| 4 | POST | `/user/credential/v1/non-login/phone/forgot/new-phone/create` | Body:`forgotNewPhoneRequest` | `c<SuccessResponse<ForgotPhoneDTO>>` | ⊘ not tested (write) |
| 5 | POST | `/user/credential/v1/non-login/phone/forgot/new-phone/otp/send` | Body:`map` | `c<SuccessResponse<RequestOtpNewPhoneDTO>>` | ⊘ not tested (write) |
| 6 | POST | `/user/credential/v1/non-login/phone/forgot/new-phone/otp/verify` | Body:`map` | `c<SuccessResponse<ForgotPhoneDTO>>` | ⊘ not tested (write) |
| 7 | POST | `/user/credential/v1/phone/change/current-password/verify` | Body:`map` | `c<SuccessResponse<ChangePhoneDTO>>` | ⊘ not tested (write) |
| 8 | POST | `/user/credential/v1/phone/change/face-matching/verify` | Body:`map` | `c<SuccessResponse<ChangePhoneDTO>>` | ⊘ not tested (write) |
| 9 | POST | `/user/credential/v1/phone/change/identity/verify` | Body:`map` | `c<SuccessResponse<ChangePhoneDTO>>` | ⊘ not tested (write) |
| 10 | POST | `/user/credential/v1/phone/change/init` | — | `c<SuccessResponse<ChangePhoneDTO>>` | ⊘ not tested (write) |
| 11 | POST | `/user/credential/v1/phone/change/new-phone/create` | Body:`changePhoneCreateNewPhoneRequest` | `c<SuccessResponse<ChangePhoneDTO>>` | ⊘ not tested (write) |
| 12 | POST | `/user/credential/v1/phone/change/new-phone/otp/send` | Body:`map` | `c<SuccessResponse<ChangePhoneSendOtpDTO>>` | ⊘ not tested (write) |
| 13 | POST | `/user/credential/v1/phone/change/new-phone/otp/verify` | Body:`map` | `c<SuccessResponse<ChangePhoneDTO>>` | ⊘ not tested (write) |
| 14 | POST | `/user/credential/v1/phone/change/otp/send` | Body:`map` | `c<SuccessResponse<ChangePhoneSendOtpDTO>>` | ⊘ not tested (write) |
| 15 | POST | `/user/credential/v1/phone/change/otp/verify` | Body:`map` | `c<SuccessResponse<ChangePhoneDTO>>` | ⊘ not tested (write) |
| 16 | POST | `/user/freeze/v1/init` | — | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 17 | POST | `auth/v2/pin/reset/validate` | Body:`requestBody` | `c<SuccessResponse<ValidateIdentityDTO>>` | ⊘ not tested (write) |
| 18 | POST | `moderation/user/report` | Body:`reportUserRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 19 | POST | `tnc/v2/acceptance` | Body:`tncRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 20 | GET | `tnc/v2/get` | Query:`feature_ids` | `c<SuccessResponse<FeatureTnCDTO>>` | ✅ 200 |
| 21 | POST | `user/credential/v1/email/change/current-password/verify` | Body:`map` | `c<SuccessResponse<ChangeEmailDTO>>` | ⊘ not tested (write) |
| 22 | POST | `user/credential/v1/email/change/face-matching/verify` | Body:`map` | `c<SuccessResponse<ChangeEmailDTO>>` | ⊘ not tested (write) |
| 23 | POST | `user/credential/v1/email/change/identity/verify` | Body:`map` | `c<SuccessResponse<ChangeEmailDTO>>` | ⊘ not tested (write) |
| 24 | POST | `user/credential/v1/email/change/init` | — | `c<SuccessResponse<ChangeEmailDTO>>` | ⊘ not tested (write) |
| 25 | POST | `user/credential/v1/email/change/new-email/create` | Body:`map` | `c<SuccessResponse<ChangeEmailDTO>>` | ⊘ not tested (write) |
| 26 | POST | `user/credential/v1/email/change/new-email/otp/send` | Body:`map` | `c<SuccessResponse<OTPChangeEmailDTO>>` | ⊘ not tested (write) |
| 27 | POST | `user/credential/v1/email/change/new-email/otp/verify` | Body:`map` | `c<SuccessResponse<ChangeEmailDTO>>` | ⊘ not tested (write) |
| 28 | POST | `user/credential/v1/email/change/otp/send` | Body:`map` | `c<SuccessResponse<OTPChangeEmailDTO>>` | ⊘ not tested (write) |
| 29 | POST | `user/credential/v1/email/change/otp/verify` | Body:`map` | `c<SuccessResponse<ChangeEmailDTO>>` | ⊘ not tested (write) |
| 30 | POST | `user/credential/v1/non-login/password/forgot/face-matching/verify` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 31 | POST | `user/credential/v1/non-login/password/forgot/init` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 32 | POST | `user/credential/v1/non-login/password/forgot/new-password/confirm` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 33 | POST | `user/credential/v1/non-login/password/forgot/new-password/create` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 34 | POST | `user/credential/v1/non-login/password/forgot/otp/send` | Body:`map` | `c<SuccessResponse<ForgotPasswordOTPDTO>>` | ⊘ not tested (write) |
| 35 | POST | `user/credential/v1/non-login/password/forgot/otp/verify` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 36 | POST | `user/credential/v1/non-login/phone/forgot/current-pin/verify` | Body:`map` | `c<SuccessResponse<ForgotPhoneDTO>>` | ⊘ not tested (write) |
| 37 | POST | `user/credential/v1/password/change/current-password/verify` | Body:`map` | `c<SuccessResponse<ChangePasswordDTO>>` | ⊘ not tested (write) |
| 38 | POST | `user/credential/v1/password/change/face-matching/verify` | Body:`map` | `c<SuccessResponse<ChangePasswordDTO>>` | ⊘ not tested (write) |
| 39 | POST | `user/credential/v1/password/change/init` | — | `c<SuccessResponse<ChangePasswordDTO>>` | ⊘ not tested (write) |
| 40 | POST | `user/credential/v1/password/change/new-password/confirm` | Body:`map` | `c<SuccessResponse<ChangePasswordDTO>>` | ⊘ not tested (write) |
| 41 | POST | `user/credential/v1/password/change/new-password/create` | Body:`map` | `c<SuccessResponse<ChangePasswordDTO>>` | ⊘ not tested (write) |
| 42 | POST | `user/credential/v1/password/change/otp/send` | Body:`map` | `c<SuccessResponse<OTPChangePasswordUserDTO>>` | ⊘ not tested (write) |
| 43 | POST | `user/credential/v1/password/change/otp/verify` | Body:`map` | `c<SuccessResponse<ChangePasswordDTO>>` | ⊘ not tested (write) |
| 44 | POST | `user/credential/v1/password/forgot/face-matching/verify` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 45 | POST | `user/credential/v1/password/forgot/init` | — | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 46 | POST | `user/credential/v1/password/forgot/new-password/confirm` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 47 | POST | `user/credential/v1/password/forgot/new-password/create` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 48 | POST | `user/credential/v1/password/forgot/otp/send` | Body:`map` | `c<SuccessResponse<ForgotPasswordOTPDTO>>` | ⊘ not tested (write) |
| 49 | POST | `user/credential/v1/password/forgot/otp/verify` | Body:`map` | `c<SuccessResponse<ForgotPasswordDTO>>` | ⊘ not tested (write) |
| 50 | GET | `user/credential/v1/status` | — | `c<SuccessResponse<CredentialStatusDTO>>` | ✅ 200 |
| 51 | POST | `user/non-login/v2/password/forgot/confirm` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 52 | POST | `user/non-login/v2/password/forgot/new` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 53 | POST | `user/non-login/v2/password/forgot/otp` | Body:`map` | `c<SuccessResponse<OTPForgotPasswordNonLoginDTO>>` | ⊘ not tested (write) |
| 54 | POST | `user/non-login/v2/password/forgot/otp/verify` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 55 | GET | `user/profile/{username}` | Path:`username` | `c<SuccessResponse<UserSocialDTO>>` | ✅ 200 |
| 56 | POST | `user/setting/email` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 57 | POST | `user/setting/email/verify` | — | `c<SuccessResponse<VerifyEmailTokenDTO>>` | ⊘ not tested (write) |
| 58 | POST | `user/setting/new-phone/confirm` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 59 | POST | `user/setting/new-phone/submit` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 60 | POST | `user/setting/password` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 61 | POST | `user/setting/phone` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 62 | POST | `user/setting/token` | Body:`map` | `c<SuccessResponse<ChangeTokenDTO>>` | ⊘ not tested (write) |
| 63 | GET | `user/v2/discovery/trending` | QueryMap:`map` | `c<SuccessResponse<TrendingDTO>>` | ✅ 200 |
| 64 | POST | `user/v2/password/change` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 65 | POST | `user/v2/password/change/confirm` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 66 | POST | `user/v2/password/change/otp` | Body:`map` | `c<SuccessResponse<OTPChangePasswordDTO>>` | ⊘ not tested (write) |
| 67 | POST | `user/v2/password/change/otp/verify` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 68 | POST | `user/v2/password/forgot/confirm` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 69 | POST | `user/v2/password/forgot/new` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 70 | POST | `user/v2/password/forgot/otp` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 71 | POST | `user/v2/password/forgot/otp/verify` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 72 | POST | `user/v2/setting/change/confirm` | Body:`confirmDataChangeRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 73 | POST | `user/v2/setting/change/email` | Body:`changeEmailRequest` | `c<SuccessResponse<ChangeDataDTO>>` | ⊘ not tested (write) |
| 74 | POST | `user/v2/setting/change/otp` | Body:`map` | `c<SuccessResponse<OTPChangePasswordDTO>>` | ⊘ not tested (write) |
| 75 | POST | `user/v2/setting/change/phone` | Body:`changePhoneNumberRequest` | `c<SuccessResponse<ChangeDataDTO>>` | ⊘ not tested (write) |
| 76 | GET | `user/v2/setting/change/status` | Query:`type` | `c<SuccessResponse<ChangeDataStatusDTO>>` | ✅ 200 |
| 77 | POST | `user/v2/setting/change/verify/identity` | Body:`verifyChangeDataIdentityRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 78 | POST | `user/v2/setting/change/verify/otp` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 79 | POST | `user/v3/setting/token` | Body:`map` | `c<SuccessResponse<ChangeDataTokenDTO>>` | ⊘ not tested (write) |
| 80 | GET | `user/verification/status` | — | `c<SuccessResponse<VerificationDTO>>` | ✅ 200 |
| 81 | POST | `user/{user_id}/block` | Path:`user_id` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 82 | POST | `user/{user_id}/unblock` | Path:`user_id` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# verifyCurrentPhoneForgotPhone  [POST /user/credential/v1/non-login/phone/forgot/current-phone/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/phone/forgot/current-phone/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ForgotPhoneRequest>'   # JSON body

# verifyFaceMatchingForgotPhone  [POST /user/credential/v1/non-login/phone/forgot/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/phone/forgot/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# initForgotPhoneLostPhone  [POST /user/credential/v1/non-login/phone/forgot/init]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/phone/forgot/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# createNewPhoneForgotPhone  [POST /user/credential/v1/non-login/phone/forgot/new-phone/create]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/phone/forgot/new-phone/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ForgotNewPhoneRequest>'   # JSON body

# requestOtpForgotPhone  [POST /user/credential/v1/non-login/phone/forgot/new-phone/otp/send]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/phone/forgot/new-phone/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyOtpNewPhoneForgotPhone  [POST /user/credential/v1/non-login/phone/forgot/new-phone/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/phone/forgot/new-phone/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postChangePhoneVerifyCurrentPassword  [POST /user/credential/v1/phone/change/current-password/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/current-password/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postChangePhoneFaceMatching  [POST /user/credential/v1/phone/change/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postChangePhoneVerifyIdentity  [POST /user/credential/v1/phone/change/identity/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/identity/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postChangePhoneInit  [POST /user/credential/v1/phone/change/init]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# postChangePhoneCreateNewPhone  [POST /user/credential/v1/phone/change/new-phone/create]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/new-phone/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ChangePhoneCreateNewPhoneRequest>'   # JSON body

# postChangePhoneSendOtpNewPhone  [POST /user/credential/v1/phone/change/new-phone/otp/send]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/new-phone/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postChangePhoneVerifyOtpNewPhone  [POST /user/credential/v1/phone/change/new-phone/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/new-phone/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postChangePhoneSendOtp  [POST /user/credential/v1/phone/change/otp/send]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postChangePhoneVerifyOtp  [POST /user/credential/v1/phone/change/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/phone/change/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# initFreezeAccount  [POST /user/freeze/v1/init]
curl -X POST "https://exodus.stockbit.com/user/freeze/v1/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# validateIdentity  [POST auth/v2/pin/reset/validate]
curl -X POST "https://exodus.stockbit.com/auth/v2/pin/reset/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# reportUser  [POST moderation/user/report]
curl -X POST "https://exodus.stockbit.com/moderation/user/report" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ReportUserRequest>'   # JSON body

# postTnC  [POST tnc/v2/acceptance]
curl -X POST "https://exodus.stockbit.com/tnc/v2/acceptance" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<TncRequest>'   # JSON body

# getTnC  [GET tnc/v2/get]
curl -X GET "https://exodus.stockbit.com/tnc/v2/get?feature_ids=<List<Integer>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# changeEmailVerifyCurrentPassword  [POST user/credential/v1/email/change/current-password/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/current-password/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeEmailVerifyFaceMatching  [POST user/credential/v1/email/change/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeEmailVerifyIdentity  [POST user/credential/v1/email/change/identity/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/identity/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeEmailInitiate  [POST user/credential/v1/email/change/init]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# changeEmailCreate  [POST user/credential/v1/email/change/new-email/create]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/new-email/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeNewEmailSendOTP  [POST user/credential/v1/email/change/new-email/otp/send]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/new-email/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeNewEmailVerifyOTP  [POST user/credential/v1/email/change/new-email/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/new-email/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeEmailSendOTP  [POST user/credential/v1/email/change/otp/send]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeEmailVerifyOTP  [POST user/credential/v1/email/change/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/email/change/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordFaceMatchingNonLogin  [POST user/credential/v1/non-login/password/forgot/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/password/forgot/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPasswordNonLogin  [POST user/credential/v1/non-login/password/forgot/init]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/password/forgot/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordInputConfirmNonLogin  [POST user/credential/v1/non-login/password/forgot/new-password/confirm]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/password/forgot/new-password/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordNewInputNonLogin  [POST user/credential/v1/non-login/password/forgot/new-password/create]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/password/forgot/new-password/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPasswordOTPNonLogin  [POST user/credential/v1/non-login/password/forgot/otp/send]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/password/forgot/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordOTPNonLogin  [POST user/credential/v1/non-login/password/forgot/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/password/forgot/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyCurrentPinForgotPhone  [POST user/credential/v1/non-login/phone/forgot/current-pin/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/phone/forgot/current-pin/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePasswordVerifyCurrent  [POST user/credential/v1/password/change/current-password/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/change/current-password/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePasswordVerifyFaceMatching  [POST user/credential/v1/password/change/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/change/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePasswordInitiate  [POST user/credential/v1/password/change/init]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/change/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# changePasswordConfirm  [POST user/credential/v1/password/change/new-password/confirm]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/change/new-password/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePasswordCreate  [POST user/credential/v1/password/change/new-password/create]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/change/new-password/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePasswordSendOTP  [POST user/credential/v1/password/change/otp/send]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/change/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePasswordVerifyOTP  [POST user/credential/v1/password/change/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/change/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordFaceMatching  [POST user/credential/v1/password/forgot/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/forgot/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPassword  [POST user/credential/v1/password/forgot/init]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/forgot/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyForgotPasswordInputConfirm  [POST user/credential/v1/password/forgot/new-password/confirm]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/forgot/new-password/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordNewInput  [POST user/credential/v1/password/forgot/new-password/create]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/forgot/new-password/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPasswordOTP  [POST user/credential/v1/password/forgot/otp/send]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/forgot/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordOTP  [POST user/credential/v1/password/forgot/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/password/forgot/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getUserCredentialStatus  [GET user/credential/v1/status]
curl -X GET "https://exodus.stockbit.com/user/credential/v1/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyForgotPasswordNonLoginInputConfirm  [POST user/non-login/v2/password/forgot/confirm]
curl -X POST "https://exodus.stockbit.com/user/non-login/v2/password/forgot/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordNonLoginNewInput  [POST user/non-login/v2/password/forgot/new]
curl -X POST "https://exodus.stockbit.com/user/non-login/v2/password/forgot/new" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestOTPForgotPasswordNonLogin  [POST user/non-login/v2/password/forgot/otp]
curl -X POST "https://exodus.stockbit.com/user/non-login/v2/password/forgot/otp" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyOTPForgotPasswordNonLogin  [POST user/non-login/v2/password/forgot/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/non-login/v2/password/forgot/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getUserProfile  [GET user/profile/{username}]
curl -X GET "https://exodus.stockbit.com/user/profile/{username}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# changeEmail  [POST user/setting/email]
curl -X POST "https://exodus.stockbit.com/user/setting/email" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyEmail  [POST user/setting/email/verify]
curl -X POST "https://exodus.stockbit.com/user/setting/email/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verificationPhone  [POST user/setting/new-phone/confirm]
curl -X POST "https://exodus.stockbit.com/user/setting/new-phone/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# registrationPhone  [POST user/setting/new-phone/submit]
curl -X POST "https://exodus.stockbit.com/user/setting/new-phone/submit" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePassword  [POST user/setting/password]
curl -X POST "https://exodus.stockbit.com/user/setting/password" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePhoneNumber  [POST user/setting/phone]
curl -X POST "https://exodus.stockbit.com/user/setting/phone" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeRequest  [POST user/setting/token]
curl -X POST "https://exodus.stockbit.com/user/setting/token" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getTrendingUsers  [GET user/v2/discovery/trending]
curl -X GET "https://exodus.stockbit.com/user/v2/discovery/trending?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyNewPassword  [POST user/v2/password/change]
curl -X POST "https://exodus.stockbit.com/user/v2/password/change" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# confirmNewPassword  [POST user/v2/password/change/confirm]
curl -X POST "https://exodus.stockbit.com/user/v2/password/change/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestOTPChangePassword  [POST user/v2/password/change/otp]
curl -X POST "https://exodus.stockbit.com/user/v2/password/change/otp" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyOTPChangePassword  [POST user/v2/password/change/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/v2/password/change/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordUserInputConfirm  [POST user/v2/password/forgot/confirm]
curl -X POST "https://exodus.stockbit.com/user/v2/password/forgot/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPasswordUserNewInput  [POST user/v2/password/forgot/new]
curl -X POST "https://exodus.stockbit.com/user/v2/password/forgot/new" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestOTPForgotPasswordUser  [POST user/v2/password/forgot/otp]
curl -X POST "https://exodus.stockbit.com/user/v2/password/forgot/otp" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyOTPForgotPasswordUser  [POST user/v2/password/forgot/otp/verify]
curl -X POST "https://exodus.stockbit.com/user/v2/password/forgot/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# confirmChange  [POST user/v2/setting/change/confirm]
curl -X POST "https://exodus.stockbit.com/user/v2/setting/change/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ConfirmDataChangeRequest>'   # JSON body

# proposeNewEmail  [POST user/v2/setting/change/email]
curl -X POST "https://exodus.stockbit.com/user/v2/setting/change/email" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ChangeEmailRequest>'   # JSON body

# requestDataChangeOTP  [POST user/v2/setting/change/otp]
curl -X POST "https://exodus.stockbit.com/user/v2/setting/change/otp" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# proposeNewPhoneNumber  [POST user/v2/setting/change/phone]
curl -X POST "https://exodus.stockbit.com/user/v2/setting/change/phone" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ChangePhoneNumberRequest>'   # JSON body

# getChangeDataStatus  [GET user/v2/setting/change/status]
curl -X GET "https://exodus.stockbit.com/user/v2/setting/change/status?type=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyChangeDataIdentity  [POST user/v2/setting/change/verify/identity]
curl -X POST "https://exodus.stockbit.com/user/v2/setting/change/verify/identity" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<VerifyChangeDataIdentityRequest>'   # JSON body

# verifyDataChangeOTP  [POST user/v2/setting/change/verify/otp]
curl -X POST "https://exodus.stockbit.com/user/v2/setting/change/verify/otp" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getChangeDataToken  [POST user/v3/setting/token]
curl -X POST "https://exodus.stockbit.com/user/v3/setting/token" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getVerificationStatus  [GET user/verification/status]
curl -X GET "https://exodus.stockbit.com/user/verification/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# blockUser  [POST user/{user_id}/block]
curl -X POST "https://exodus.stockbit.com/user/{user_id}/block" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# unblockUser  [POST user/{user_id}/unblock]
curl -X POST "https://exodus.stockbit.com/user/{user_id}/unblock" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 28. `CompanyApi`  (41 endpoint)
<sub>com/stockbit/remote/api/company/CompanyApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `/company-price-feed/price-performance/{symbol}` | Path:`symbol` | `c<SuccessResponse<PricePerformanceDTO>>` | ✅ 200 |
| 2 | GET | `/keystats/ratio/v1/{symbol}` | Path:`symbol` · QueryMap:`map` | `c<SuccessResponse<KeyStatsDTO>>` | ✅ 200 |
| 3 | GET | `analyst-ratings/{symbol}` | Path:`symbol` | `c<SuccessResponse<AnalystRatingDTO>>` | ✅ 200 |
| 4 | GET | `analyst-ratings/{symbol}/consensus` | Path:`symbol` | `c<SuccessResponse<List<AnalystConsensusDTO>>>` | ✅ 200 |
| 5 | GET | `chartbit/token/mobile` | Query(src):`theme`,`symbol` | `c<SuccessResponse<CompanyChartbitTokenDTO>>` | ✅ 200 |
| 6 | GET | `charts/{symbol}/daily` | Path:`symbol` · Query(src):`timeframe` | `c<SuccessResponse<CompanyChartDTO>>` | ✅ 200 |
| 7 | GET | `company-price-feed/prices` | Query(src):`stock_code` | `c<SuccessResponse<CompanyPriceDTO>>` | ✅ 200 |
| 8 | GET | `comparison/v2/ratios` | Query(src):`symbol` | `c<SuccessResponse<CompanyRatioDTO>>` | ✅ 200 |
| 9 | POST | `comparison/v2/{symbol}/competitors` | Path:`symbol` · Body:`map` | `c<SuccessResponse<String>>` | ⊘ not tested (write) |
| 10 | GET | `comparison/v2/{symbol}/competitors` | Path:`symbol` | `c<SuccessResponse<CompanyCompetitorDTO>>` | ✅ 200 |
| 11 | DELETE | `comparison/v2/{symbol}/competitors/{competitor_symbol}` | Path:`symbol` · Path:`competitor_symbol` | `c<SuccessResponse<String>>` | ⊘ not tested (write) |
| 12 | GET | `corpaction/dividend` | QueryMap:`map` | `c<SuccessResponse<CorpActionDividendDTO>>` | ✅ 200 |
| 13 | GET | `corpaction/status` | Query:`symbol` | `c<SuccessResponse<List<CorpActionStatusDTO>>>` | ✅ 200 |
| 14 | GET | `corpaction/stock_dividend` | QueryMap:`map` | `c<SuccessResponse<CorpActionStockDividendDTO>>` | ✅ 200 |
| 15 | GET | `corpaction/{symbol}` | Path:`symbol` | `c<SuccessResponse<List<CorpActionInfoDTO>>>` | ✅ 200 |
| 16 | GET | `corpaction/{symbol}/bonus` | Path:`symbol` | `c<SuccessResponse<CorpActionBonusDTO>>` | ✅ 200 |
| 17 | GET | `corpaction/{symbol}/reversesplit` | Path:`symbol` | `c<SuccessResponse<CorpActionReverseSplitDTO>>` | ✅ 200 |
| 18 | GET | `corpaction/{symbol}/rightissue` | Path:`symbol` | `c<SuccessResponse<CorpActionRightIssueDTO>>` | ✅ 200 |
| 19 | GET | `corpaction/{symbol}/rups` | Path:`symbol` | `c<SuccessResponse<CorpActionRupsDTO>>` | ✅ 200 |
| 20 | GET | `corpaction/{symbol}/stock_conversion` | Path:`symbol` · Query(src):`page`,`limit` · Query(src):`page`,`limit` | `c<SuccessResponse<CorpActionStockConversionDTO>>` | ✅ 200 |
| 21 | GET | `corpaction/{symbol}/stocksplit` | Path:`symbol` | `c<SuccessResponse<CorpActionStockSplitDTO>>` | ✅ 200 |
| 22 | GET | `corpaction/{symbol}/tenderoffer` | Path:`symbol` | `c<SuccessResponse<CorpActionTenderOfferDTO>>` | ✅ 200 |
| 23 | GET | `corpaction/{symbol}/warrant` | Path:`symbol` | `c<SuccessResponse<CorpActionWarrantDTO>>` | ✅ 200 |
| 24 | POST | `emitten-metadata/shareholders/token` | — | `c<SuccessResponse<CompanyShareholderTokenDTO>>` | ⊘ not tested (write) |
| 25 | GET | `emitten-metadata/subsidiary/{symbol}` | Path:`symbol` | `c<SuccessResponse<CompanyProfileSubsidiaryDTO>>` | ✅ 200 |
| 26 | GET | `emitten/{symbol}/info` | Path:`symbol` | `c<SuccessResponse<CompanyDTO>>` | ✅ 200 |
| 27 | GET | `emitten/{symbol}/info` | Path:`symbol` | `c<SuccessResponse<CompanyInfoDTO>>` | ✅ 200 |
| 28 | GET | `emitten/{symbol}/profile` | Path:`symbol` | `c<SuccessResponse<CompanyProfileDTO>>` | ✅ 200 |
| 29 | GET | `emitten/{symbol}/profile` | Path:`symbol` | `c<SuccessResponse<CompanyMutualFundProfileDTO>>` | ✅ 200 |
| 30 | GET | `findata-view/foreign-domestic/v1/chart-data/{symbol}` | Path:`symbol` · QueryMap:`map` | `c<SuccessResponse<ForeignDomesticDTO>>` | ✅ 200 |
| 31 | GET | `findata-view/foreign-domestic/v1/period-ranges/{symbol}` | Path:`symbol` | `c<SuccessResponse<List<ForeignDomesticPeriodDTO>>>` | ✅ 200 |
| 32 | GET | `findata-view/v2/financials/{symbol}` | Path:`symbol` · Query(src):`data_type`,`report_type`,`statement_type`,`is_percentage` | `c<SuccessResponse<CompanyFinancialTableDTO>>` | ✅ 200 |
| 33 | POST | `fundachart/tokens` | Body:`fundaChartTokenRequest` | `c<SuccessResponse<FundachartTokenDTO>>` | ⊘ not tested (write) |
| 34 | GET | `fundachart/v2/{symbol}/financials` | Path:`symbol` · Query(src):`data_type`,`report` | `c<SuccessResponse<CompanyFinancialDTO>>` | ✅ 200 |
| 35 | GET | `order-trade/running-trade` | Query:`symbols` · Query(src):`symbols`,`order_by`,`sort` | `c<SuccessResponse<RunningTradeDTO>>` | ✅ 200 |
| 36 | GET | `order-trade/running-trade/chart/{symbol}` | Path:`symbol` · Query:`broker_code` · Query(src):`broker_code`,`to`,`period`,`market_board`,`investor_type` · Query:`to` · Query:`period` · Query:`market_board` · Query:`investor_type` | `c<SuccessResponse<BrokerFlowDTO>>` | ✅ 200 |
| 37 | GET | `order-trade/trade-book` | Query(src):`symbol`,`group_by`,`sort_by`,`sort_direction`,`time_interval`,`to` · HeaderMap:`map2` | `c<SuccessResponse<TradeBookDTO>>` | ✅ 200 |
| 38 | GET | `order-trade/trade-book/chart` | Query(src):`symbol`,`time_interval`,`to` · HeaderMap:`map2` | `c<SuccessResponse<TradeBookChartDTO>>` | ✅ 200 |
| 39 | GET | `research/company/{symbol}` | Path:`symbol` | `c<SuccessResponse<CompanyResearchDTO>>` | ✅ 200 |
| 40 | GET | `seasonality/{company_symbol}` | Path:`company_symbol` · Query(src):`year` | `c<SuccessResponse<SeasonalityDTO>>` | ✅ 200 |
| 41 | GET | `seasonality/{company_symbol}/years` | Path:`company_symbol` | `c<SuccessResponse<List<SeasonalityYearsDTO>>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCompanyPricePerformance  [GET /company-price-feed/price-performance/{symbol}]
curl -X GET "https://exodus.stockbit.com/company-price-feed/price-performance/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyKeyStats  [GET /keystats/ratio/v1/{symbol}]
curl -X GET "https://exodus.stockbit.com/keystats/ratio/v1/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getAnalystRating  [GET analyst-ratings/{symbol}]
curl -X GET "https://exodus.stockbit.com/analyst-ratings/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getAnalystConsensus  [GET analyst-ratings/{symbol}/consensus]
curl -X GET "https://exodus.stockbit.com/analyst-ratings/{symbol}/consensus" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyChartbitToken  [GET chartbit/token/mobile]
curl -X GET "https://exodus.stockbit.com/chartbit/token/mobile?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyChart  [GET charts/{symbol}/daily]
curl -X GET "https://exodus.stockbit.com/charts/{symbol}/daily?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyPrices  [GET company-price-feed/prices]
curl -X GET "https://exodus.stockbit.com/company-price-feed/prices?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyRatios  [GET comparison/v2/ratios]
curl -X GET "https://exodus.stockbit.com/comparison/v2/ratios?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# addCompanyCompetitor  [POST comparison/v2/{symbol}/competitors]
curl -X POST "https://exodus.stockbit.com/comparison/v2/{symbol}/competitors" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getCompanyCompetitors  [GET comparison/v2/{symbol}/competitors]
curl -X GET "https://exodus.stockbit.com/comparison/v2/{symbol}/competitors" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# deleteCompanyCompetitor  [DELETE comparison/v2/{symbol}/competitors/{competitor_symbol}]
curl -X DELETE "https://exodus.stockbit.com/comparison/v2/{symbol}/competitors/{competitor_symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCorpActioDividend  [GET corpaction/dividend]
curl -X GET "https://exodus.stockbit.com/corpaction/dividend?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCorpActionStatus  [GET corpaction/status]
curl -X GET "https://exodus.stockbit.com/corpaction/status?symbol=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCorpActionStockDividend  [GET corpaction/stock_dividend]
curl -X GET "https://exodus.stockbit.com/corpaction/stock_dividend?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getAllCorpAction  [GET corpaction/{symbol}]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionBonusBySymbol  [GET corpaction/{symbol}/bonus]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/bonus" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionReverseSplitBySymbol  [GET corpaction/{symbol}/reversesplit]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/reversesplit" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionRightIssueBySymbol  [GET corpaction/{symbol}/rightissue]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/rightissue" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionRUPSBySymbol  [GET corpaction/{symbol}/rups]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/rups" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCorpActionStockConversion  [GET corpaction/{symbol}/stock_conversion]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/stock_conversion?<map>=<int>&<map>=<int>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionStockSplitBySymbol  [GET corpaction/{symbol}/stocksplit]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/stocksplit" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionTenderOfferBySymbol  [GET corpaction/{symbol}/tenderoffer]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/tenderoffer" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionWarrantBySymbol  [GET corpaction/{symbol}/warrant]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/warrant" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyShareholderToken  [POST emitten-metadata/shareholders/token]
curl -X POST "https://exodus.stockbit.com/emitten-metadata/shareholders/token" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanySubsidiary  [GET emitten-metadata/subsidiary/{symbol}]
curl -X GET "https://exodus.stockbit.com/emitten-metadata/subsidiary/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyInfo  [GET emitten/{symbol}/info]
curl -X GET "https://exodus.stockbit.com/emitten/{symbol}/info" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyInfoV2  [GET emitten/{symbol}/info]
curl -X GET "https://exodus.stockbit.com/emitten/{symbol}/info" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyProfile  [GET emitten/{symbol}/profile]
curl -X GET "https://exodus.stockbit.com/emitten/{symbol}/profile" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getMutualFundProfile  [GET emitten/{symbol}/profile]
curl -X GET "https://exodus.stockbit.com/emitten/{symbol}/profile" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getForeignDomesticChart  [GET findata-view/foreign-domestic/v1/chart-data/{symbol}]
curl -X GET "https://exodus.stockbit.com/findata-view/foreign-domestic/v1/chart-data/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getForeignDomesticPeriod  [GET findata-view/foreign-domestic/v1/period-ranges/{symbol}]
curl -X GET "https://exodus.stockbit.com/findata-view/foreign-domestic/v1/period-ranges/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyFinancialTable  [GET findata-view/v2/financials/{symbol}]
curl -X GET "https://exodus.stockbit.com/findata-view/v2/financials/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getFundachartToken  [POST fundachart/tokens]
curl -X POST "https://exodus.stockbit.com/fundachart/tokens" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<FundaChartTokenRequest>'   # JSON body

# getCompanyFinancialInfo  [GET fundachart/v2/{symbol}/financials]
curl -X GET "https://exodus.stockbit.com/fundachart/v2/{symbol}/financials?<map>=<Map<String, Integer>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getRunningTrade  [GET order-trade/running-trade]
curl -X GET "https://exodus.stockbit.com/order-trade/running-trade?symbols=<List<String>>&<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBrokerFlow  [GET order-trade/running-trade/chart/{symbol}]
curl -X GET "https://exodus.stockbit.com/order-trade/running-trade/chart/{symbol}?broker_code=<List<String>>&<map>=<String>&to=<String>&period=<String>&market_board=<String>&investor_type=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getTradeBook  [GET order-trade/trade-book]
curl -X GET "https://exodus.stockbit.com/order-trade/trade-book?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

# getTradeBookChart  [GET order-trade/trade-book/chart]
curl -X GET "https://exodus.stockbit.com/order-trade/trade-book/chart?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

# getCompanyResearch  [GET research/company/{symbol}]
curl -X GET "https://exodus.stockbit.com/research/company/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSeasonality  [GET seasonality/{company_symbol}]
curl -X GET "https://exodus.stockbit.com/seasonality/{company_symbol}?<map>=<Map<String, Integer>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSeasonalityYears  [GET seasonality/{company_symbol}/years]
curl -X GET "https://exodus.stockbit.com/seasonality/{company_symbol}/years" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 29. `UserService`  (38 endpoint)
<sub>com/stockbit/remote/api/UserService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `moderation/user/report` | Body:`reportUserRequest` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 2 | POST | `registration/check/fullname` | Body:`registrationFullNameRequest` | `A<RegistrationCommonResponse>` | ⊘ not tested (write) |
| 3 | POST | `registration/check/password` | Body:`registrationPasswordRequest` | `A<RegistrationCommonResponse>` | ⊘ not tested (write) |
| 4 | POST | `registration/check/sns-email` | Body:`registrationEmailRequest` | `A<RegistrationEmailResponse>` | ⊘ not tested (write) |
| 5 | POST | `registration/check/username` | Body:`registrationUsernameRequest` | `A<RegistrationCommonResponse>` | ⊘ not tested (write) |
| 6 | POST | `registration/v3/check/email` | Body:`registrationEmailRequest` | `A<RegistrationEmailResponse>` | ⊘ not tested (write) |
| 7 | POST | `registration/v3/check/phone` | Body:`registrationPhoneNumRequest` | `A<RegistrationCommonResponse>` | ⊘ not tested (write) |
| 8 | POST | `registration/v3/otp/email` | Body:`registrationVerifyOTPRequest` | `A<RegistrationCommonResponse>` | ⊘ not tested (write) |
| 9 | POST | `registration/v3/otp/phone` | Body:`registrationVerifyOTPRequest` | `A<RegistrationUserResponse>` | ⊘ not tested (write) |
| 10 | POST | `tnc/v2/acceptance` | Body:`tnCAcceptanceRequest` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 11 | GET | `tnc/v2/get` | Query:`feature_ids` | `A<TnCResponse>` | ✅ 200 |
| 12 | POST | `user/admin/suspend` | Body:`userSuspendParams` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 13 | GET | `user/avatar/collection` | — | `A<Object>` | ✅ 200 |
| 14 | GET | `user/blocked` | QueryMap:`map` | `A<BlockedUserPagingResponse>` | ✅ 200 |
| 15 | POST | `user/connect/facebook` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 16 | POST | `user/connect/google` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 17 | POST | `user/deactivate/url` | — | `A<EIpoLinkResponse>` | ⊘ not tested (write) |
| 18 | POST | `user/disconnect/facebook` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 19 | POST | `user/disconnect/google` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 20 | PUT | `user/profile` | Body:`map` | `A<ProfileExodusResponse>` | ⊘ not tested (write) |
| 21 | PUT | `user/profile/country` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 22 | GET | `user/profile/{username}` | Path:`username` | `A<ProfileExodusResponse>` | ✅ 200 |
| 23 | POST | `user/setting/bank/email/send` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 24 | POST | `user/setting/bank/email/verify` | Body:`map` | `A<ChangeRequestResponse>` | ⊘ not tested (write) |
| 25 | POST | `user/setting/bank/identity/validate` | Body:`map` | `A<SecuritiesIdentityVerificationResponse>` | ⊘ not tested (write) |
| 26 | POST | `user/setting/email` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 27 | POST | `user/setting/email/confirm` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 28 | PUT | `user/setting/password` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 29 | POST | `user/setting/password/forgot` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 30 | POST | `user/setting/phone` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 31 | POST | `user/setting/phone/confirm` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 32 | POST | `user/setting/pin/phone/send` | Body:`map` | `A<TradingStockbitResetPinTokenResponse>` | ⊘ not tested (write) |
| 33 | POST | `user/setting/pin/phone/validate` | Body:`map` | `A<TradingStockbitResetPinPhoneVerificationResponse>` | ⊘ not tested (write) |
| 34 | POST | `user/setting/token` | Body:`map` | `A<Object>` | ⊘ not tested (write) |
| 35 | POST | `user/upload/token` | Body:`generateUserUploadTokenRequest` | `A<AwsUploadTokenResponse>` | ⊘ not tested (write) |
| 36 | POST | `user/{user_id}/block` | Path:`user_id` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 37 | POST | `user/{user_id}/unblock` | Path:`user_id` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 38 | GET | `verified-badge/user/{user_id}` | Path:`user_id` | `A<UserEmittenResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# reportUser  [POST moderation/user/report]
curl -X POST "https://exodus.stockbit.com/moderation/user/report" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ReportUserRequest>'   # JSON body

# validateRegisterFullname  [POST registration/check/fullname]
curl -X POST "https://exodus.stockbit.com/registration/check/fullname" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RegistrationFullNameRequest>'   # JSON body

# validateRegisterPassword  [POST registration/check/password]
curl -X POST "https://exodus.stockbit.com/registration/check/password" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RegistrationPasswordRequest>'   # JSON body

# registrationEmailSocial  [POST registration/check/sns-email]
curl -X POST "https://exodus.stockbit.com/registration/check/sns-email" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RegistrationEmailRequest>'   # JSON body

# validateRegisterUsername  [POST registration/check/username]
curl -X POST "https://exodus.stockbit.com/registration/check/username" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RegistrationUsernameRequest>'   # JSON body

# registrationEmail  [POST registration/v3/check/email]
curl -X POST "https://exodus.stockbit.com/registration/v3/check/email" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RegistrationEmailRequest>'   # JSON body

# registrationPhone  [POST registration/v3/check/phone]
curl -X POST "https://exodus.stockbit.com/registration/v3/check/phone" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RegistrationPhoneNumRequest>'   # JSON body

# verifyEmailRegistration  [POST registration/v3/otp/email]
curl -X POST "https://exodus.stockbit.com/registration/v3/otp/email" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RegistrationVerifyOTPRequest>'   # JSON body

# validateOtpUnverifiedUser  [POST registration/v3/otp/phone]
curl -X POST "https://exodus.stockbit.com/registration/v3/otp/phone" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RegistrationVerifyOTPRequest>'   # JSON body

# postTnc  [POST tnc/v2/acceptance]
curl -X POST "https://exodus.stockbit.com/tnc/v2/acceptance" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<TnCAcceptanceRequest>'   # JSON body

# getTnC  [GET tnc/v2/get]
curl -X GET "https://exodus.stockbit.com/tnc/v2/get?feature_ids=<List<Integer>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# suspendUser  [POST user/admin/suspend]
curl -X POST "https://exodus.stockbit.com/user/admin/suspend" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<UserSuspendParams>'   # JSON body

# getAvatarCollection  [GET user/avatar/collection]
curl -X GET "https://exodus.stockbit.com/user/avatar/collection" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBlockedList  [GET user/blocked]
curl -X GET "https://exodus.stockbit.com/user/blocked?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# connectToFacebook  [POST user/connect/facebook]
curl -X POST "https://exodus.stockbit.com/user/connect/facebook" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# connectToGoogle  [POST user/connect/google]
curl -X POST "https://exodus.stockbit.com/user/connect/google" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# generateUserDeleteUrl  [POST user/deactivate/url]
curl -X POST "https://exodus.stockbit.com/user/deactivate/url" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# disconnectToFacebook  [POST user/disconnect/facebook]
curl -X POST "https://exodus.stockbit.com/user/disconnect/facebook" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# disconnectToGoogle  [POST user/disconnect/google]
curl -X POST "https://exodus.stockbit.com/user/disconnect/google" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# editProfile  [PUT user/profile]
curl -X PUT "https://exodus.stockbit.com/user/profile" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# updateCountry  [PUT user/profile/country]
curl -X PUT "https://exodus.stockbit.com/user/profile/country" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getProfile  [GET user/profile/{username}]
curl -X GET "https://exodus.stockbit.com/user/profile/{username}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# sendEmailConfirmationAmendBank  [POST user/setting/bank/email/send]
curl -X POST "https://exodus.stockbit.com/user/setting/bank/email/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyEmailConfirmationAmendBank  [POST user/setting/bank/email/verify]
curl -X POST "https://exodus.stockbit.com/user/setting/bank/email/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# securitiesVerifyIdentityKTP  [POST user/setting/bank/identity/validate]
curl -X POST "https://exodus.stockbit.com/user/setting/bank/identity/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeEmail  [POST user/setting/email]
curl -X POST "https://exodus.stockbit.com/user/setting/email" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# confirmChangeEmail  [POST user/setting/email/confirm]
curl -X POST "https://exodus.stockbit.com/user/setting/email/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePassword  [PUT user/setting/password]
curl -X PUT "https://exodus.stockbit.com/user/setting/password" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# forgotStockbitPassword  [POST user/setting/password/forgot]
curl -X POST "https://exodus.stockbit.com/user/setting/password/forgot" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changePhoneNumber  [POST user/setting/phone]
curl -X POST "https://exodus.stockbit.com/user/setting/phone" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# confirmChangePhoneNumber  [POST user/setting/phone/confirm]
curl -X POST "https://exodus.stockbit.com/user/setting/phone/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifySecuritiesIdentityNumber  [POST user/setting/pin/phone/send]
curl -X POST "https://exodus.stockbit.com/user/setting/pin/phone/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifySecuritiesPinOtp  [POST user/setting/pin/phone/validate]
curl -X POST "https://exodus.stockbit.com/user/setting/pin/phone/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# changeRequest  [POST user/setting/token]
curl -X POST "https://exodus.stockbit.com/user/setting/token" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# generateUploadToken  [POST user/upload/token]
curl -X POST "https://exodus.stockbit.com/user/upload/token" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<GenerateUserUploadTokenRequest>'   # JSON body

# blockUser  [POST user/{user_id}/block]
curl -X POST "https://exodus.stockbit.com/user/{user_id}/block" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# unblockUser  [POST user/{user_id}/unblock]
curl -X POST "https://exodus.stockbit.com/user/{user_id}/unblock" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getUserEmittenStatus  [GET verified-badge/user/{user_id}]
curl -X GET "https://exodus.stockbit.com/verified-badge/user/{user_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 30. `StreamService`  (32 endpoint)
<sub>com/stockbit/remote/api/StreamService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `notes` | QueryMap:`map` | `A<CompanyNoteListResponse>` | ✅ 200 |
| 2 | GET | `research` | QueryMap:`map` | `A<ResearchListResponse>` | ✅ 200 |
| 3 | GET | `research/categories` | — | `A<ResearchListCategoryResponse>` | ✅ 200 |
| 4 | GET | `research/indicator/new` | QueryMap:`map` | `A<ResearchNotificationResponse>` | ✅ 200 |
| 5 | POST | `stream/addvote/{tp_id}` | Path:`tp_id` · QueryMap:`map` | `A<StreamResponse>` | ⊘ not tested (write) |
| 6 | GET | `stream/announcement/{value}` | Path:`value` | `A<AnnouncementResponse>` | 🟡 400 |
| 7 | PUT | `stream/commenter-type/{stream_id}` | Path:`stream_id` · Body:`jsonObject` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 8 | POST | `stream/delete/multiple` | Body:`jsonObject` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 9 | POST | `stream/follow/{postid}` | Path:`postid` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 10 | POST | `stream/like/{postid}` | Path:`postid` | `A<StreamResponse>` | ⊘ not tested (write) |
| 11 | GET | `stream/likers/{path}` | Path:`path` · QueryMap:`map` | `A<LikersResponse>` | 🔴 500 |
| 12 | POST | `stream/pin` | QueryMap:`map` | `A<remote.models.response.stream.StreamListResponse>` | ⊘ not tested (write) |
| 13 | POST | `stream/polling/vote/{polling_id}` | Path:`polling_id` · Body:`map` | `A<PollingResponse>` | ⊘ not tested (write) |
| 14 | POST | `stream/reply/{postid}` | Path:`postid` · Body:`jsonObject` | `A<StreamResponse>` | ⊘ not tested (write) |
| 15 | POST | `stream/report/{postid}` | Path:`postid` · QueryMap:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 16 | POST | `stream/save/{postid}` | Path:`postid` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 17 | POST | `stream/topic/untag/{stream_id}` | Path:`stream_id` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 18 | POST | `stream/unfollow/{postid}` | Path:`postid` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 19 | POST | `stream/unlike/{postid}` | Path:`postid` | `A<StreamResponse>` | ⊘ not tested (write) |
| 20 | POST | `stream/unpin` | QueryMap:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 21 | POST | `stream/unsave/{postid}` | Path:`postid` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 22 | POST | `stream/v2/delete/{post_id}` | Path:`post_id` · Body:`jsonObject` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 23 | GET | `stream/v2/uploadtoken` | — | `A<AwsTokenResponse>` | ✅ 200 |
| 24 | GET | `stream/v3` | QueryMap:`map` | `A<StreamListResponse>` | ✅ 200 |
| 25 | POST | `stream/v3/conversation/comments` | Body:`jsonObject` | `A<StreamListResponse>` | ⊘ not tested (write) |
| 26 | POST | `stream/v3/conversation/{parent_stream_id}` | Path:`parent_stream_id` | `A<StreamConversationResponse>` | ⊘ not tested (write) |
| 27 | GET | `stream/v3/symbol/{symbol}` | Path:`symbol` · QueryMap:`map` | `A<StreamListResponse>` | ✅ 200 |
| 28 | GET | `stream/v3/symbol/{symbol}/pinned` | Path:`symbol` | `A<StreamContentResponse>` | ✅ 200 |
| 29 | POST | `stream/v3/trending` | Body:`jsonObject` | `A<StreamListResponse>` | ⊘ not tested (write) |
| 30 | POST | `stream/v3/user/{username}` | Path:`username` · Body:`jsonObject` | `A<StreamListResponse>` | ⊘ not tested (write) |
| 31 | POST | `stream/v3/user/{username}/pinned` | Path:`username` | `A<StreamContentResponse>` | ⊘ not tested (write) |
| 32 | POST | `stream/{type}` | Path:`type` · Body:`jsonObject` | `A<StreamResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCompanyNotes  [GET notes]
curl -X GET "https://exodus.stockbit.com/notes?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getStreamResearch  [GET research]
curl -X GET "https://exodus.stockbit.com/research?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getStreamResearchCategories  [GET research/categories]
curl -X GET "https://exodus.stockbit.com/research/categories" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getStreamResearchNotification  [GET research/indicator/new]
curl -X GET "https://exodus.stockbit.com/research/indicator/new?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# votePrediction  [POST stream/addvote/{tp_id}]
curl -X POST "https://exodus.stockbit.com/stream/addvote/{tp_id}?<map>=<Map<String, Boolean>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getAnnouncements  [GET stream/announcement/{value}]
curl -X GET "https://exodus.stockbit.com/stream/announcement/{value}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateCommentType  [PUT stream/commenter-type/{stream_id}]
curl -X PUT "https://exodus.stockbit.com/stream/commenter-type/{stream_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# deleteMultipleStreamPost  [POST stream/delete/multiple]
curl -X POST "https://exodus.stockbit.com/stream/delete/multiple" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# followUser  [POST stream/follow/{postid}]
curl -X POST "https://exodus.stockbit.com/stream/follow/{postid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# likePost  [POST stream/like/{postid}]
curl -X POST "https://exodus.stockbit.com/stream/like/{postid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getLikers  [GET stream/likers/{path}]
curl -X GET "https://exodus.stockbit.com/stream/likers/{path}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# pinStreamPost  [POST stream/pin]
curl -X POST "https://exodus.stockbit.com/stream/pin?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# votePolling  [POST stream/polling/vote/{polling_id}]
curl -X POST "https://exodus.stockbit.com/stream/polling/vote/{polling_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, Integer>>'   # JSON body

# replyStream  [POST stream/reply/{postid}]
curl -X POST "https://exodus.stockbit.com/stream/reply/{postid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# reportStream  [POST stream/report/{postid}]
curl -X POST "https://exodus.stockbit.com/stream/report/{postid}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# saveStreamPost  [POST stream/save/{postid}]
curl -X POST "https://exodus.stockbit.com/stream/save/{postid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# unTagMentionedCompany  [POST stream/topic/untag/{stream_id}]
curl -X POST "https://exodus.stockbit.com/stream/topic/untag/{stream_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# unFollowUser  [POST stream/unfollow/{postid}]
curl -X POST "https://exodus.stockbit.com/stream/unfollow/{postid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# unLikePost  [POST stream/unlike/{postid}]
curl -X POST "https://exodus.stockbit.com/stream/unlike/{postid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# unPinStreamPost  [POST stream/unpin]
curl -X POST "https://exodus.stockbit.com/stream/unpin?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# unSaveStreamPost  [POST stream/unsave/{postid}]
curl -X POST "https://exodus.stockbit.com/stream/unsave/{postid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# deleteStreamPost  [POST stream/v2/delete/{post_id}]
curl -X POST "https://exodus.stockbit.com/stream/v2/delete/{post_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# getAwsToken  [GET stream/v2/uploadtoken]
curl -X GET "https://exodus.stockbit.com/stream/v2/uploadtoken" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getStream  [GET stream/v3]
curl -X GET "https://exodus.stockbit.com/stream/v3?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getStreamConversationPrev  [POST stream/v3/conversation/comments]
curl -X POST "https://exodus.stockbit.com/stream/v3/conversation/comments" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# getStreamConversation  [POST stream/v3/conversation/{parent_stream_id}]
curl -X POST "https://exodus.stockbit.com/stream/v3/conversation/{parent_stream_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getStreamSymbol  [GET stream/v3/symbol/{symbol}]
curl -X GET "https://exodus.stockbit.com/stream/v3/symbol/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getPinnedStreamCompany  [GET stream/v3/symbol/{symbol}/pinned]
curl -X GET "https://exodus.stockbit.com/stream/v3/symbol/{symbol}/pinned" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getStreamTrending  [POST stream/v3/trending]
curl -X POST "https://exodus.stockbit.com/stream/v3/trending" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# getStreamUser  [POST stream/v3/user/{username}]
curl -X POST "https://exodus.stockbit.com/stream/v3/user/{username}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# getPinnedStreamUser  [POST stream/v3/user/{username}/pinned]
curl -X POST "https://exodus.stockbit.com/stream/v3/user/{username}/pinned" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# submitStream  [POST stream/{type}]
curl -X POST "https://exodus.stockbit.com/stream/{type}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

```
</details>

## 31. `AuthApi`  (30 endpoint)
<sub>com/stockbit/remote/api/AuthApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `auth/biometric/v2/revoke` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | POST | `auth/biometric/v2/setup` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 3 | POST | `auth/session/device/{uuid}/remove` | Path:`uuid` · Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 4 | POST | `auth/touchid/revoke` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 5 | POST | `auth/touchid/setup` | — | `c<SuccessResponse<BiometricSetupDTO>>` | ⊘ not tested (write) |
| 6 | POST | `auth/v1/session/device/migrate` | Body:`map` | `c<SuccessResponse<DeviceMigrationDTO>>` | ⊘ not tested (write) |
| 7 | GET | `auth/v2/session/devices` | QueryMap:`map` | `c<SuccessResponse<DeviceListDTO>>` | ✅ 200 |
| 8 | POST | `auth/v3/non-login/pin/forgot/face-matching/verify` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 9 | POST | `auth/v3/non-login/pin/forgot/identity/verify` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 10 | POST | `auth/v3/non-login/pin/forgot/init` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 11 | POST | `auth/v3/non-login/pin/forgot/new-pin/confirm` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 12 | POST | `auth/v3/non-login/pin/forgot/new-pin/create` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 13 | POST | `auth/v3/non-login/pin/forgot/otp/send` | Body:`map` | `c<SuccessResponse<ForgotPinOTPDTO>>` | ⊘ not tested (write) |
| 14 | POST | `auth/v3/non-login/pin/forgot/otp/verify` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 15 | POST | `auth/v3/pin/forgot/face-matching/verify` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 16 | POST | `auth/v3/pin/forgot/identity/verify` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 17 | POST | `auth/v3/pin/forgot/init` | — | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 18 | POST | `auth/v3/pin/forgot/new-pin/confirm` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 19 | POST | `auth/v3/pin/forgot/new-pin/create` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 20 | POST | `auth/v3/pin/forgot/otp/send` | Body:`map` | `c<SuccessResponse<ForgotPinOTPDTO>>` | ⊘ not tested (write) |
| 21 | POST | `auth/v3/pin/forgot/otp/verify` | Body:`map` | `c<SuccessResponse<ForgotPinDTO>>` | ⊘ not tested (write) |
| 22 | POST | `login/refresh` | HeaderMap:`map` | `A<TokenResponse>` | ⊘ not tested (write) |
| 23 | POST | `login/v6/biometric` | Body:`loginBiometricDataParam` | `c<SuccessResponse<LoginV6DTO>>` | ⊘ not tested (write) |
| 24 | POST | `login/v6/biometric/challenge` | Body:`map` | `c<SuccessResponse<BiometricChallengeDTO>>` | ⊘ not tested (write) |
| 25 | POST | `login/v6/biometric/verify` | Body:`map` | `c<SuccessResponse<LoginV6DTO>>` | ⊘ not tested (write) |
| 26 | POST | `login/v6/new-device/verify` | Body:`verifyNewDeviceLoginDataParam` | `c<SuccessResponse<VerifyNewDeviceLoginDTO>>` | ⊘ not tested (write) |
| 27 | POST | `login/v6/social` | Body:`loginSocialDataParam` | `c<SuccessResponse<LoginV6DTO>>` | ⊘ not tested (write) |
| 28 | POST | `login/v6/unfreeze/verify` | Body:`verifyUnfreezeDataParam` | `c<SuccessResponse<VerifyLoginDTO>>` | ⊘ not tested (write) |
| 29 | POST | `login/v6/username` | Body:`loginUserNamePasswordDataParam` | `c<SuccessResponse<LoginV6DTO>>` | ⊘ not tested (write) |
| 30 | POST | `logout` | — | `A<BaseResponseImpl>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# revokeSocialBiometric  [POST auth/biometric/v2/revoke]
curl -X POST "https://exodus.stockbit.com/auth/biometric/v2/revoke" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# setupSocialBiometric  [POST auth/biometric/v2/setup]
curl -X POST "https://exodus.stockbit.com/auth/biometric/v2/setup" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# revokeDeviceSession  [POST auth/session/device/{uuid}/remove]
curl -X POST "https://exodus.stockbit.com/auth/session/device/{uuid}/remove" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# revokeBiometricLogin  [POST auth/touchid/revoke]
curl -X POST "https://exodus.stockbit.com/auth/touchid/revoke" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getBiometricSetupToken  [POST auth/touchid/setup]
curl -X POST "https://exodus.stockbit.com/auth/touchid/setup" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# migrateDeviceId  [POST auth/v1/session/device/migrate]
curl -X POST "https://exodus.stockbit.com/auth/v1/session/device/migrate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getDeviceList  [GET auth/v2/session/devices]
curl -X GET "https://exodus.stockbit.com/auth/v2/session/devices?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyForgotPinFaceMatchingNonLogin  [POST auth/v3/non-login/pin/forgot/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/auth/v3/non-login/pin/forgot/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPinDataVerificationNonLogin  [POST auth/v3/non-login/pin/forgot/identity/verify]
curl -X POST "https://exodus.stockbit.com/auth/v3/non-login/pin/forgot/identity/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPinNonLogin  [POST auth/v3/non-login/pin/forgot/init]
curl -X POST "https://exodus.stockbit.com/auth/v3/non-login/pin/forgot/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPinInputConfirmNonLogin  [POST auth/v3/non-login/pin/forgot/new-pin/confirm]
curl -X POST "https://exodus.stockbit.com/auth/v3/non-login/pin/forgot/new-pin/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPinNewInputNonLogin  [POST auth/v3/non-login/pin/forgot/new-pin/create]
curl -X POST "https://exodus.stockbit.com/auth/v3/non-login/pin/forgot/new-pin/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPinOTPNonLogin  [POST auth/v3/non-login/pin/forgot/otp/send]
curl -X POST "https://exodus.stockbit.com/auth/v3/non-login/pin/forgot/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPinOTPNonLogin  [POST auth/v3/non-login/pin/forgot/otp/verify]
curl -X POST "https://exodus.stockbit.com/auth/v3/non-login/pin/forgot/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPinFaceMatching  [POST auth/v3/pin/forgot/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/auth/v3/pin/forgot/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPinDataVerification  [POST auth/v3/pin/forgot/identity/verify]
curl -X POST "https://exodus.stockbit.com/auth/v3/pin/forgot/identity/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPin  [POST auth/v3/pin/forgot/init]
curl -X POST "https://exodus.stockbit.com/auth/v3/pin/forgot/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyForgotPinInputConfirm  [POST auth/v3/pin/forgot/new-pin/confirm]
curl -X POST "https://exodus.stockbit.com/auth/v3/pin/forgot/new-pin/confirm" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPinNewInput  [POST auth/v3/pin/forgot/new-pin/create]
curl -X POST "https://exodus.stockbit.com/auth/v3/pin/forgot/new-pin/create" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestForgotPinOTP  [POST auth/v3/pin/forgot/otp/send]
curl -X POST "https://exodus.stockbit.com/auth/v3/pin/forgot/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyForgotPinOTP  [POST auth/v3/pin/forgot/otp/verify]
curl -X POST "https://exodus.stockbit.com/auth/v3/pin/forgot/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getRefreshToken  [POST login/refresh]
curl -X POST "https://exodus.stockbit.com/login/refresh" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

# loginBiometric  [POST login/v6/biometric]
curl -X POST "https://exodus.stockbit.com/login/v6/biometric" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<LoginBiometricDataParam>'   # JSON body

# loginBiometricChallenge  [POST login/v6/biometric/challenge]
curl -X POST "https://exodus.stockbit.com/login/v6/biometric/challenge" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# loginBiometricVerify  [POST login/v6/biometric/verify]
curl -X POST "https://exodus.stockbit.com/login/v6/biometric/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyNewDevice  [POST login/v6/new-device/verify]
curl -X POST "https://exodus.stockbit.com/login/v6/new-device/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<VerifyNewDeviceLoginDataParam>'   # JSON body

# loginSocial  [POST login/v6/social]
curl -X POST "https://exodus.stockbit.com/login/v6/social" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<LoginSocialDataParam>'   # JSON body

# verifyUnfreeze  [POST login/v6/unfreeze/verify]
curl -X POST "https://exodus.stockbit.com/login/v6/unfreeze/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<VerifyUnfreezeDataParam>'   # JSON body

# loginUserNamePassword  [POST login/v6/username]
curl -X POST "https://exodus.stockbit.com/login/v6/username" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<LoginUserNamePasswordDataParam>'   # JSON body

# logout  [POST logout]
curl -X POST "https://exodus.stockbit.com/logout" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 32. `ChatApi`  (20 endpoint)
<sub>com/stockbit/remote/api/chat/ChatApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | DELETE | `chat/rooms/{room_id}` | Path:`room_id` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | POST | `chat/rooms/{room_id}/clear` | Path:`room_id` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 3 | GET | `chat/s3/policy` | Query(src):`filename` | `c<SuccessResponse<AWSUploadTokenDTO>>` | ✅ 200 |
| 4 | GET | `chat/v2/eligibility/new-personal` | QueryMap:`map` | `c<SuccessResponse<ChatEligibilityDTO>>` | ✅ 200 |
| 5 | DELETE | `chat/v2/invitations` | — | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 6 | POST | `chat/v2/invitations/bulk-respond` | Body:`bulkRespondMessageDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 7 | POST | `chat/v2/invitations/join/{invitation_code}` | Path:`invitation_code` | `c<SuccessResponse<JoinGroupDTO>>` | ⊘ not tested (write) |
| 8 | GET | `chat/v2/invitations/preview/{invitation_code}` | Path:`invitation_code` | `c<SuccessResponse<InvitationPreviewDTO>>` | ⚪ 404 |
| 9 | POST | `chat/v2/invitations/room-id/{room_id}/respond` | Path:`room_id` · Body:`acceptRejectMessageDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 10 | GET | `chat/v2/invitations/setting` | — | `c<SuccessResponse<ChatPrivacySettingsDTO>>` | ✅ 200 |
| 11 | PUT | `chat/v2/invitations/setting` | Body:`setChatPrivacySettingsParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 12 | POST | `chat/v2/messages` | Body:`sendMessageDataParam` | `c<SuccessResponse<SendMessageDTO>>` | ⊘ not tested (write) |
| 13 | POST | `chat/v2/messages/bulk` | Body:`shareContentDataParam` | `c<SuccessResponse<w>>` | ⊘ not tested (write) |
| 14 | POST | `chat/v2/messages/bulk-delete` | Body:`deleteMessagesDataParam` | `c<SuccessResponse<w>>` | ⊘ not tested (write) |
| 15 | POST | `chat/v2/messages/forward` | Body:`forwardMessagesDataParam` | `c<SuccessResponse<ForwardMessagesDTO>>` | ⊘ not tested (write) |
| 16 | POST | `chat/v2/messages/read` | Body:`map` | `c<SuccessResponse>` | ⊘ not tested (write) |
| 17 | GET | `chat/v2/receivers/shareable-search` | QueryMap:`map` | `c<SuccessResponse<ReceiverRoomDTO>>` | ✅ 200 |
| 18 | GET | `chat/v2/rooms` | Query(src):`limit` | `c<SuccessResponse<ListRoomDTO>>` | ✅ 200 |
| 19 | GET | `chat/v2/rooms/type/invited` | Query(src):`limit` | `c<SuccessResponse<ListRoomDTO>>` | ✅ 200 |
| 20 | GET | `chat/v2/rooms/unread/count` | — | `c<SuccessResponse<UnreadChatRoomDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# deleteChatRoom  [DELETE chat/rooms/{room_id}]
curl -X DELETE "https://exodus.stockbit.com/chat/rooms/{room_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# clearChatRoom  [POST chat/rooms/{room_id}/clear]
curl -X POST "https://exodus.stockbit.com/chat/rooms/{room_id}/clear" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getUploadToken  [GET chat/s3/policy]
curl -X GET "https://exodus.stockbit.com/chat/s3/policy?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getChatEligibility  [GET chat/v2/eligibility/new-personal]
curl -X GET "https://exodus.stockbit.com/chat/v2/eligibility/new-personal?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# deleteAllMessageRequest  [DELETE chat/v2/invitations]
curl -X DELETE "https://exodus.stockbit.com/chat/v2/invitations" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# bulkRespondMessageRequest  [POST chat/v2/invitations/bulk-respond]
curl -X POST "https://exodus.stockbit.com/chat/v2/invitations/bulk-respond" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<BulkRespondMessageDataParam>'   # JSON body

# joinGroup  [POST chat/v2/invitations/join/{invitation_code}]
curl -X POST "https://exodus.stockbit.com/chat/v2/invitations/join/{invitation_code}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getInvitationPreview  [GET chat/v2/invitations/preview/{invitation_code}]
curl -X GET "https://exodus.stockbit.com/chat/v2/invitations/preview/{invitation_code}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# respondMessageRequest  [POST chat/v2/invitations/room-id/{room_id}/respond]
curl -X POST "https://exodus.stockbit.com/chat/v2/invitations/room-id/{room_id}/respond" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<AcceptRejectMessageDataParam>'   # JSON body

# getChatPrivacySettings  [GET chat/v2/invitations/setting]
curl -X GET "https://exodus.stockbit.com/chat/v2/invitations/setting" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# putChatPrivacySettings  [PUT chat/v2/invitations/setting]
curl -X PUT "https://exodus.stockbit.com/chat/v2/invitations/setting" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<SetChatPrivacySettingsParam>'   # JSON body

# sendMessage  [POST chat/v2/messages]
curl -X POST "https://exodus.stockbit.com/chat/v2/messages" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<SendMessageDataParam>'   # JSON body

# shareContent  [POST chat/v2/messages/bulk]
curl -X POST "https://exodus.stockbit.com/chat/v2/messages/bulk" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ShareContentDataParam>'   # JSON body

# deleteMessages  [POST chat/v2/messages/bulk-delete]
curl -X POST "https://exodus.stockbit.com/chat/v2/messages/bulk-delete" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<DeleteMessagesDataParam>'   # JSON body

# forwardMessages  [POST chat/v2/messages/forward]
curl -X POST "https://exodus.stockbit.com/chat/v2/messages/forward" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ForwardMessagesDataParam>'   # JSON body

# readMessages  [POST chat/v2/messages/read]
curl -X POST "https://exodus.stockbit.com/chat/v2/messages/read" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getShareableRoomList  [GET chat/v2/receivers/shareable-search]
curl -X GET "https://exodus.stockbit.com/chat/v2/receivers/shareable-search?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getChatRoomList  [GET chat/v2/rooms]
curl -X GET "https://exodus.stockbit.com/chat/v2/rooms?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getChatRoomRequests  [GET chat/v2/rooms/type/invited]
curl -X GET "https://exodus.stockbit.com/chat/v2/rooms/type/invited?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getUnreadChatRoom  [GET chat/v2/rooms/unread/count]
curl -X GET "https://exodus.stockbit.com/chat/v2/rooms/unread/count" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 33. `ChatGroupApi`  (20 endpoint)
<sub>com/stockbit/remote/api/chat/ChatGroupApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `chat/v2/groups` | Body:`createGroupDataParam` | `c<SuccessResponse<GroupDTO>>` | ⊘ not tested (write) |
| 2 | GET | `chat/v2/groups/eligibility` | — | `c<SuccessResponse<GroupCreateEligibilityDTO>>` | ✅ 200 |
| 3 | GET | `chat/v2/groups/members/max` | — | `c<SuccessResponse<MaxGroupMemberDTO>>` | ✅ 200 |
| 4 | GET | `chat/v2/groups/members/suggestions` | Query(src):`limit` | `c<SuccessResponse<SuggestedMembersDTO>>` | ✅ 200 |
| 5 | GET | `chat/v2/groups/members/suggestions/contacts` | Query(src):`limit` | `c<SuccessResponse<SuggestedContactsDTO>>` | ✅ 200 |
| 6 | GET | `chat/v2/groups/room-id/{roomId}` | Path:`roomId` | `c<SuccessResponse<GroupDTO>>` | ⚪ 404 |
| 7 | PUT | `chat/v2/groups/{groupId}` | Path:`groupId` · Body:`updateGroupInfoDataParam` | `c<SuccessResponse<GroupDTO>>` | ⊘ not tested (write) |
| 8 | POST | `chat/v2/groups/{groupId}/change-admin-and-leave` | Path:`groupId` · Body:`changeAdminAndLeaveGroupDataParam` | `c<SuccessResponse<w>>` | ⊘ not tested (write) |
| 9 | GET | `chat/v2/groups/{groupId}/member/{memberId}` | Path:`groupId` · Path:`memberId` | `c<SuccessResponse<GroupMemberDTO>>` | 🚫 403 |
| 10 | GET | `chat/v2/groups/{groupId}/members` | Path:`groupId` · QueryMap:`map` | `c<SuccessResponse<ListGroupMemberDTO>>` | 🚫 403 |
| 11 | POST | `chat/v2/groups/{groupId}/members/invite` | Path:`groupId` · Body:`addGroupMembersDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 12 | POST | `chat/v2/groups/{groupId}/members/leave` | Path:`groupId` · Body:`leaveGroupDataParam` | `c<SuccessResponse<w>>` | ⊘ not tested (write) |
| 13 | POST | `chat/v2/groups/{groupId}/members/remove` | Path:`groupId` · Body:`removeGroupMemberDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 14 | POST | `chat/v2/groups/{groupId}/reset-link` | Path:`groupId` | `c<SuccessResponse<ResetInvitationLinkDTO>>` | ⊘ not tested (write) |
| 15 | POST | `chat/v2/groups/{groupId}/set-admin-status` | Path:`groupId` · Body:`assisgnUnassignGroupAdminDataParam` | `c<SuccessResponse<AssignUnassignAdminDTO>>` | ⊘ not tested (write) |
| 16 | GET | `chat/v2/groups/{groupId}/settings` | Path:`groupId` | `c<SuccessResponse<GroupSettingsDTO>>` | 🚫 403 |
| 17 | POST | `chat/v2/groups/{groupId}/settings` | Path:`groupId` · Body:`groupSettingDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 18 | GET | `chat/v2/groups/{group_id}/messages` | Path:`i2` · Query(src):`limit` | `c<SuccessResponse<MessagesDTO>>` | 🚫 403 |
| 19 | POST | `chat/v2/rooms/{roomId}/mute` | Path:`roomId` · Body:`muteUnmuteGroupDataParam` | `c<SuccessResponse<MuteUnmuteGroupDTO>>` | ⊘ not tested (write) |
| 20 | GET | `chat/v3/user/search` | Query(src):`keyword`,`page`,`limit` | `c<SuccessResponse<SuggestedContactsDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# createGroup  [POST chat/v2/groups]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<CreateGroupDataParam>'   # JSON body

# createGroupEligibility  [GET chat/v2/groups/eligibility]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/eligibility" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getMaxGroupMember  [GET chat/v2/groups/members/max]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/members/max" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSuggestedMembers  [GET chat/v2/groups/members/suggestions]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/members/suggestions?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSuggestedContacts  [GET chat/v2/groups/members/suggestions/contacts]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/members/suggestions/contacts?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getGroupDetail  [GET chat/v2/groups/room-id/{roomId}]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/room-id/{roomId}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateGroupInfo  [PUT chat/v2/groups/{groupId}]
curl -X PUT "https://exodus.stockbit.com/chat/v2/groups/{groupId}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<UpdateGroupInfoDataParam>'   # JSON body

# changeAdminAndLeaveGroup  [POST chat/v2/groups/{groupId}/change-admin-and-leave]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/change-admin-and-leave" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ChangeAdminAndLeaveGroupDataParam>'   # JSON body

# getGroupMemberDetail  [GET chat/v2/groups/{groupId}/member/{memberId}]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/{groupId}/member/{memberId}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getGroupMembers  [GET chat/v2/groups/{groupId}/members]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/{groupId}/members?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# addGroupMembers  [POST chat/v2/groups/{groupId}/members/invite]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/members/invite" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<AddGroupMembersDataParam>'   # JSON body

# leaveGroup  [POST chat/v2/groups/{groupId}/members/leave]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/members/leave" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<LeaveGroupDataParam>'   # JSON body

# removeGroupMembers  [POST chat/v2/groups/{groupId}/members/remove]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/members/remove" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RemoveGroupMemberDataParam>'   # JSON body

# resetGroupInvitationLink  [POST chat/v2/groups/{groupId}/reset-link]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/reset-link" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setGroupAdmin  [POST chat/v2/groups/{groupId}/set-admin-status]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/set-admin-status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<AssisgnUnassignGroupAdminDataParam>'   # JSON body

# getGroupSettings  [GET chat/v2/groups/{groupId}/settings]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/{groupId}/settings" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setGroupSettings  [POST chat/v2/groups/{groupId}/settings]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/settings" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<GroupSettingDataParam>'   # JSON body

# getMessages  [GET chat/v2/groups/{group_id}/messages]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/{group_id}/messages?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setMuteUnmuteGroup  [POST chat/v2/rooms/{roomId}/mute]
curl -X POST "https://exodus.stockbit.com/chat/v2/rooms/{roomId}/mute" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<MuteUnmuteGroupDataParam>'   # JSON body

# searchMembers  [GET chat/v3/user/search]
curl -X GET "https://exodus.stockbit.com/chat/v3/user/search?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 34. `TrustedDeviceApi`  (20 endpoint)
<sub>com/stockbit/remote/api/TrustedDeviceApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `mfa/v1/prompt/trusted/action` | Body:`map` | `c<SuccessResponse<PromptApprovalTrustedDeviceDTO>>` | ⊘ not tested (write) |
| 2 | GET | `mfa/v1/prompt/trusted/pending` | — | `c<SuccessResponse<PromptDetailTrustedDeviceDTO>>` | ✅ 200 |
| 3 | GET | `mfa/v1/prompt/trusted/validate` | Query(src):`token`,`signature` | `c<SuccessResponse<PromptDetailTrustedDeviceDTO>>` | 🟡 400 |
| 4 | POST | `mfa/v1/prompt/trusted/validate` | Body:`map` | `c<SuccessResponse<LoginRequesterDetailDTO>>` | ⊘ not tested (write) |
| 5 | GET | `mfa/v1/prompt/verified/result` | Query:`token` | `c<SuccessResponse<PromptResultDTO>>` | ✅ 200 |
| 6 | POST | `trusted-device/challenge/otp` | Body:`map` | `c<SuccessResponse<RequestOTPTrustedDeviceDTO>>` | ⊘ not tested (write) |
| 7 | POST | `trusted-device/challenge/otp/verify` | Body:`map` | `c<SuccessResponse<SetupTrustedDeviceDTO>>` | ⊘ not tested (write) |
| 8 | POST | `trusted-device/challenge/password` | Body:`map` | `c<SuccessResponse<SetupTrustedDeviceDTO>>` | ⊘ not tested (write) |
| 9 | POST | `trusted-device/challenge/pin` | Body:`map` | `c<SuccessResponse<SetupTrustedDeviceDTO>>` | ⊘ not tested (write) |
| 10 | POST | `trusted-device/challenge/prompt` | Body:`map` | `c<SuccessResponse<ChallengeChangeTrustedDeviceDTO>>` | ⊘ not tested (write) |
| 11 | POST | `trusted-device/challenge/prompt/verify` | Body:`map` | `c<SuccessResponse<ChangeTrustedDevicePromptDTO>>` | ⊘ not tested (write) |
| 12 | POST | `trusted-device/completion` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 13 | POST | `trusted-device/onboarding/close` | — | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 14 | GET | `trusted-device/status` | — | `c<SuccessResponse<StatusTrustedDeviceDTO>>` | ✅ 200 |
| 15 | POST | `trusted-device/v1/remove/completion` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 16 | POST | `trusted-device/v1/remove/init` | — | `c<SuccessResponse<TrustedDeviceRemovalInitiationDTO>>` | ⊘ not tested (write) |
| 17 | POST | `trusted-device/v2/challenge/face-matching/verify` | Body:`map` | `c<SuccessResponse<SetupTrustedDeviceDTO>>` | ⊘ not tested (write) |
| 18 | POST | `trusted-device/v2/change` | — | `c<SuccessResponse<ChangeTrustedDevicePromptDTO>>` | ⊘ not tested (write) |
| 19 | POST | `trusted-device/v2/recovery/challenge/identity` | Body:`recoveryValidateIdentityDataParam` | `c<SuccessResponse<ChangeTrustedDevicePromptDTO>>` | ⊘ not tested (write) |
| 20 | POST | `trusted-device/v2/setup` | — | `c<SuccessResponse<SetupTrustedDeviceDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# promptAction  [POST mfa/v1/prompt/trusted/action]
curl -X POST "https://exodus.stockbit.com/mfa/v1/prompt/trusted/action" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getPromptDetailPending  [GET mfa/v1/prompt/trusted/pending]
curl -X GET "https://exodus.stockbit.com/mfa/v1/prompt/trusted/pending" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getPromptDetail  [GET mfa/v1/prompt/trusted/validate]
curl -X GET "https://exodus.stockbit.com/mfa/v1/prompt/trusted/validate?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# validateTrustedDevice  [POST mfa/v1/prompt/trusted/validate]
curl -X POST "https://exodus.stockbit.com/mfa/v1/prompt/trusted/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getPromptResult  [GET mfa/v1/prompt/verified/result]
curl -X GET "https://exodus.stockbit.com/mfa/v1/prompt/verified/result?token=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# requestOTP  [POST trusted-device/challenge/otp]
curl -X POST "https://exodus.stockbit.com/trusted-device/challenge/otp" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyOTP  [POST trusted-device/challenge/otp/verify]
curl -X POST "https://exodus.stockbit.com/trusted-device/challenge/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyPassword  [POST trusted-device/challenge/password]
curl -X POST "https://exodus.stockbit.com/trusted-device/challenge/password" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyPIN  [POST trusted-device/challenge/pin]
curl -X POST "https://exodus.stockbit.com/trusted-device/challenge/pin" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# sendPromptChangeTrustedDevice  [POST trusted-device/challenge/prompt]
curl -X POST "https://exodus.stockbit.com/trusted-device/challenge/prompt" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyPromptChangeTrustedDevice  [POST trusted-device/challenge/prompt/verify]
curl -X POST "https://exodus.stockbit.com/trusted-device/challenge/prompt/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# completeSetup  [POST trusted-device/completion]
curl -X POST "https://exodus.stockbit.com/trusted-device/completion" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# setTrustedDeviceOnboardingClosed  [POST trusted-device/onboarding/close]
curl -X POST "https://exodus.stockbit.com/trusted-device/onboarding/close" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getTrustedDeviceStatus  [GET trusted-device/status]
curl -X GET "https://exodus.stockbit.com/trusted-device/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# completeRemoveTrustedDevice  [POST trusted-device/v1/remove/completion]
curl -X POST "https://exodus.stockbit.com/trusted-device/v1/remove/completion" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# initRemoveTrustedDevice  [POST trusted-device/v1/remove/init]
curl -X POST "https://exodus.stockbit.com/trusted-device/v1/remove/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyFaceMatching  [POST trusted-device/v2/challenge/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/trusted-device/v2/challenge/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestChangeTrustedDevice  [POST trusted-device/v2/change]
curl -X POST "https://exodus.stockbit.com/trusted-device/v2/change" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# validateRecoveryChangeIdentity  [POST trusted-device/v2/recovery/challenge/identity]
curl -X POST "https://exodus.stockbit.com/trusted-device/v2/recovery/challenge/identity" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RecoveryValidateIdentityDataParam>'   # JSON body

# setupTrustedDevice  [POST trusted-device/v2/setup]
curl -X POST "https://exodus.stockbit.com/trusted-device/v2/setup" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 35. `CompanyExodusService`  (18 endpoint)
<sub>com/stockbit/remote/api/company/CompanyExodusService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `chartbit/token/mobile` | Query(src):`symbol` | `A<Object>` | ✅ 200 |
| 2 | GET | `charts/{symbol}/daily` | Path:`symbol` · Query(src):`timeframe` | `A<CompanyPricesChartResponse>` | ✅ 200 |
| 3 | POST | `emitten-metadata/shareholders/token` | — | `A<Object>` | ⊘ not tested (write) |
| 4 | GET | `emitten/discover/{type}` | Path:`type` | `A<DiscoverHotlistResponse>` | 🔴 500 |
| 5 | GET | `emitten/indexes/catalog` | — | `A<DiscoverSectorSectionResponse>` | ✅ 200 |
| 6 | GET | `emitten/indexes/mobile` | — | `A<Object>` | ✅ 200 |
| 7 | GET | `emitten/sector/{sector}/company` | Path:`str` | `A<SubSectorCompanyResponse>` | ✅ 200 |
| 8 | GET | `emitten/stock/popular` | QueryMap:`map` | `A<SubSectorCompanyMemberResponse>` | ✅ 200 |
| 9 | GET | `emitten/trending` | QueryMap:`map` | `A<SubSectorCompanyMemberResponse>` | ✅ 200 |
| 10 | GET | `emitten/v3/sector/{sector}/subsector/{subsector}/company` | Path:`str` · Path:`str2` · QueryMap:`map` | `A<SubSectorCompanyMemberResponse>` | ✅ 200 |
| 11 | GET | `emitten/{symbol}/info` | Path:`symbol` | `A<CompanyResponse>` | ✅ 200 |
| 12 | GET | `findata-view/foreign-domestic/v1/chart-data/{symbol}` | Path:`symbol` · QueryMap:`map` | `A<Object>` | ✅ 200 |
| 13 | GET | `findata-view/foreign-domestic/v1/period-ranges/{symbol}` | Path:`symbol` | `A<Object>` | ✅ 200 |
| 14 | GET | `findata-view/marketdetectors/activity/{code}/detail` | Path:`code` · Query(src):`page`,`limit` | `A<CompanyBandarDetectorResponse>` | ✅ 200 |
| 15 | GET | `findata-view/marketdetectors/brokers` | Query(src):`limit`,`page` | `A<BrokerCodeResponse>` | ✅ 200 |
| 16 | GET | `findata-view/v2/financials/{symbol}` | Path:`symbol` · Query(src):`data_type`,`report_type`,`statement_type`,`is_percentage` | `A<Object>` | ✅ 200 |
| 17 | GET | `fundachart/{symbol}/financials` | Path:`symbol` · Query(src):`data_type`,`report` | `A<Object>` | ✅ 200 |
| 18 | GET | `marketdetectors/{symbol}` | Path:`symbol` · QueryMap:`map` | `A<CompanyBandarDetectorResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getChartbitToken  [GET chartbit/token/mobile]
curl -X GET "https://exodus.stockbit.com/chartbit/token/mobile?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getDailyChart  [GET charts/{symbol}/daily]
curl -X GET "https://exodus.stockbit.com/charts/{symbol}/daily?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyEmitenToken  [POST emitten-metadata/shareholders/token]
curl -X POST "https://exodus.stockbit.com/emitten-metadata/shareholders/token" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getDiscoverHotListByType  [GET emitten/discover/{type}]
curl -X GET "https://exodus.stockbit.com/emitten/discover/{type}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getDiscoverSectorSection  [GET emitten/indexes/catalog]
curl -X GET "https://exodus.stockbit.com/emitten/indexes/catalog" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getMarketIndexes  [GET emitten/indexes/mobile]
curl -X GET "https://exodus.stockbit.com/emitten/indexes/mobile" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyInSector  [GET emitten/sector/{sector}/company]
curl -X GET "https://exodus.stockbit.com/emitten/sector/{sector}/company" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getPopularStock  [GET emitten/stock/popular]
curl -X GET "https://exodus.stockbit.com/emitten/stock/popular?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getTrendingStock  [GET emitten/trending]
curl -X GET "https://exodus.stockbit.com/emitten/trending?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanySymbolInSubSector  [GET emitten/v3/sector/{sector}/subsector/{subsector}/company]
curl -X GET "https://exodus.stockbit.com/emitten/v3/sector/{sector}/subsector/{subsector}/company?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyInfo  [GET emitten/{symbol}/info]
curl -X GET "https://exodus.stockbit.com/emitten/{symbol}/info" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getForeignDomesticChart  [GET findata-view/foreign-domestic/v1/chart-data/{symbol}]
curl -X GET "https://exodus.stockbit.com/findata-view/foreign-domestic/v1/chart-data/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getForeignDomesticPeriod  [GET findata-view/foreign-domestic/v1/period-ranges/{symbol}]
curl -X GET "https://exodus.stockbit.com/findata-view/foreign-domestic/v1/period-ranges/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBrokerActivityDetail  [GET findata-view/marketdetectors/activity/{code}/detail]
curl -X GET "https://exodus.stockbit.com/findata-view/marketdetectors/activity/{code}/detail?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBrokerCode  [GET findata-view/marketdetectors/brokers]
curl -X GET "https://exodus.stockbit.com/findata-view/marketdetectors/brokers?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyFinancialTable  [GET findata-view/v2/financials/{symbol}]
curl -X GET "https://exodus.stockbit.com/findata-view/v2/financials/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyFinancialInfo  [GET fundachart/{symbol}/financials]
curl -X GET "https://exodus.stockbit.com/fundachart/{symbol}/financials?<map>=<Map<String, Integer>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBrokerDetector  [GET marketdetectors/{symbol}]
curl -X GET "https://exodus.stockbit.com/marketdetectors/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 36. `CorporateActionService`  (17 endpoint)
<sub>com/stockbit/remote/api/CorporateActionService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `corpaction` | QueryMap:`map` | `A<Object>` | ✅ 200 |
| 2 | GET | `corpaction/bonus` | QueryMap:`map` | `A<CorpActionBonusResponse>` | ✅ 200 |
| 3 | GET | `corpaction/dividend` | QueryMap:`map` | `A<CashDividendResponse>` | ✅ 200 |
| 4 | GET | `corpaction/economic` | — | `A<CalendarEconomicResponse>` | ✅ 200 |
| 5 | GET | `corpaction/ipo` | QueryMap:`map` | `A<IpoDataResponse>` | ✅ 200 |
| 6 | GET | `corpaction/pubex` | QueryMap:`map` | `A<PublicExposeDataResponse>` | ✅ 200 |
| 7 | GET | `corpaction/reversesplit` | QueryMap:`map` | `A<ReverseSplitDataResponse>` | ✅ 200 |
| 8 | GET | `corpaction/rightissue` | QueryMap:`map` | `A<RightIssueDataResponse>` | ✅ 200 |
| 9 | GET | `corpaction/rups` | QueryMap:`map` | `A<RupsDataResponse>` | ✅ 200 |
| 10 | GET | `corpaction/status` | Query:`symbol` | `A<Object>` | ✅ 200 |
| 11 | GET | `corpaction/stock_dividend` | QueryMap:`map` | `A<StockDividendResponse>` | ✅ 200 |
| 12 | GET | `corpaction/stocksplit` | QueryMap:`map` | `A<StockSplitDataResponse>` | ✅ 200 |
| 13 | GET | `corpaction/tenderoffer` | QueryMap:`map` | `A<TenderOfferResponse>` | ✅ 200 |
| 14 | GET | `corpaction/warrant` | QueryMap:`map` | `A<WarrantDataResponse>` | ✅ 200 |
| 15 | GET | `corpaction/{symbol}/ipo` | Path:`symbol` · QueryMap:`map` | `A<IpoDataResponse>` | 🔴 500 |
| 16 | GET | `corpaction/{symbol}/pubex` | Path:`symbol` · QueryMap:`map` | `A<PublicExposeDataResponse>` | ✅ 200 |
| 17 | GET | `corpaction/{symbol}/rups` | Path:`symbol` · QueryMap:`map` | `A<RupsDataResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getListCorpActionToday  [GET corpaction]
curl -X GET "https://exodus.stockbit.com/corpaction?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionBonus  [GET corpaction/bonus]
curl -X GET "https://exodus.stockbit.com/corpaction/bonus?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCorpActionCashDividend  [GET corpaction/dividend]
curl -X GET "https://exodus.stockbit.com/corpaction/dividend?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarEconomic  [GET corpaction/economic]
curl -X GET "https://exodus.stockbit.com/corpaction/economic" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionIpo  [GET corpaction/ipo]
curl -X GET "https://exodus.stockbit.com/corpaction/ipo?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionPublicExpose  [GET corpaction/pubex]
curl -X GET "https://exodus.stockbit.com/corpaction/pubex?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionReverseSplit  [GET corpaction/reversesplit]
curl -X GET "https://exodus.stockbit.com/corpaction/reversesplit?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionRightIssue  [GET corpaction/rightissue]
curl -X GET "https://exodus.stockbit.com/corpaction/rightissue?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionRups  [GET corpaction/rups]
curl -X GET "https://exodus.stockbit.com/corpaction/rups?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionInfo  [GET corpaction/status]
curl -X GET "https://exodus.stockbit.com/corpaction/status?symbol=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getStockDividend  [GET corpaction/stock_dividend]
curl -X GET "https://exodus.stockbit.com/corpaction/stock_dividend?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionStockSplit  [GET corpaction/stocksplit]
curl -X GET "https://exodus.stockbit.com/corpaction/stocksplit?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionTenderOffer  [GET corpaction/tenderoffer]
curl -X GET "https://exodus.stockbit.com/corpaction/tenderoffer?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionWarrant  [GET corpaction/warrant]
curl -X GET "https://exodus.stockbit.com/corpaction/warrant?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionIpoBySymbol  [GET corpaction/{symbol}/ipo]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/ipo?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionPublicExposeBySymbol  [GET corpaction/{symbol}/pubex]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/pubex?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListCorpActionRupsBySymbol  [GET corpaction/{symbol}/rups]
curl -X GET "https://exodus.stockbit.com/corpaction/{symbol}/rups?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 37. `WatchListService`  (13 endpoint)
<sub>com/stockbit/remote/api/WatchListService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `screener/finitem-watchlist` | QueryMap:`map` | `A<WatchlistSortResponse>` | ✅ 200 |
| 2 | POST | `watchlist` | Body:`map` | `A<Object>` | ⊘ not tested (write) |
| 3 | GET | `watchlist` | QueryMap:`map` | `A<WatchlistGroupResponse>` | ✅ 200 |
| 4 | PUT | `watchlist/people/alert` | Body:`map` | `A<Object>` | ⊘ not tested (write) |
| 5 | POST | `watchlist/people/item` | Body:`map` | `A<Object>` | ⊘ not tested (write) |
| 6 | GET | `watchlist/people/{user_id}/followers` | Path:`user_id` · QueryMap:`map` | `A<Object>` | ✅ 200 |
| 7 | GET | `watchlist/people/{user_id}/following` | Path:`user_id` · QueryMap:`map` | `A<Object>` | ✅ 200 |
| 8 | GET | `watchlist/suggestion/company` | Query(src):`watchlist_id` | `A<SubSectorCompanyMemberResponse>` | ✅ 200 |
| 9 | PUT | `watchlist/{watchlist_id}` | Path:`watchlist_id` · Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 10 | GET | `watchlist/{watchlist_id}` | Path:`watchlist_id` · Query(src):`limit` · Header:`Authorization-Carina` | `A<WatchlistDataResponse>` | ✅ 200 |
| 11 | POST | `watchlist/{watchlist_id}/company/item` | Path:`watchlist_id` · Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 12 | PUT | `watchlist/{watchlist_id}/company/item` | Path:`watchlist_id` · Body:`watchlistEditCompanyRequest` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 13 | POST | `watchlist/{watchlist_id}/symbol-only` | Path:`watchlist_id` · Body:`watchlistStocksSymbolOnlyRequest` | `A<WatchlistDataSymbolOnlyResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getWatchlistSortFunction  [GET screener/finitem-watchlist]
curl -X GET "https://exodus.stockbit.com/screener/finitem-watchlist?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# createWatchlistGroup  [POST watchlist]
curl -X POST "https://exodus.stockbit.com/watchlist" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getWatchlistGroup  [GET watchlist]
curl -X GET "https://exodus.stockbit.com/watchlist?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# toggleFollowedUserNotificationSubscription  [PUT watchlist/people/alert]
curl -X PUT "https://exodus.stockbit.com/watchlist/people/alert" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# postFollowSuggestedPeople  [POST watchlist/people/item]
curl -X POST "https://exodus.stockbit.com/watchlist/people/item" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getFollowers  [GET watchlist/people/{user_id}/followers]
curl -X GET "https://exodus.stockbit.com/watchlist/people/{user_id}/followers?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getFollowing  [GET watchlist/people/{user_id}/following]
curl -X GET "https://exodus.stockbit.com/watchlist/people/{user_id}/following?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getWatchListSuggestionCompany  [GET watchlist/suggestion/company]
curl -X GET "https://exodus.stockbit.com/watchlist/suggestion/company?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# editWatchlist  [PUT watchlist/{watchlist_id}]
curl -X PUT "https://exodus.stockbit.com/watchlist/{watchlist_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getWatchlist  [GET watchlist/{watchlist_id}]
curl -X GET "https://exodus.stockbit.com/watchlist/{watchlist_id}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Authorization-Carina: $AUTHORIZATION_CARINA"

# addCompanyToWatchlist  [POST watchlist/{watchlist_id}/company/item]
curl -X POST "https://exodus.stockbit.com/watchlist/{watchlist_id}/company/item" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# editWatchlistCompanies  [PUT watchlist/{watchlist_id}/company/item]
curl -X PUT "https://exodus.stockbit.com/watchlist/{watchlist_id}/company/item" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<WatchlistEditCompanyRequest>'   # JSON body

# getWatchlistStocksSymbolOnly  [POST watchlist/{watchlist_id}/symbol-only]
curl -X POST "https://exodus.stockbit.com/watchlist/{watchlist_id}/symbol-only" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<WatchlistStocksSymbolOnlyRequest>'   # JSON body

```
</details>

## 38. `CalendarApi`  (12 endpoint)
<sub>com/stockbit/remote/api/CalendarApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `corpaction` | QueryMap:`map` | `c<SuccessResponse<CalendarTodayDTO>>` | ✅ 200 |
| 2 | GET | `corpaction/bonus` | — | `c<SuccessResponse<List<CalendarBonusDTO>>>` | ✅ 200 |
| 3 | GET | `corpaction/dividend` | — | `c<SuccessResponse<List<CalendarDividendDTO>>>` | ✅ 200 |
| 4 | GET | `corpaction/economic` | — | `c<SuccessResponse<Object>>` | ✅ 200 |
| 5 | GET | `corpaction/ipo` | — | `c<SuccessResponse<List<CalendarIpoDTO>>>` | ✅ 200 |
| 6 | GET | `corpaction/pubex` | — | `c<SuccessResponse<List<CalendarPublicExposeDTO>>>` | ✅ 200 |
| 7 | GET | `corpaction/reversesplit` | — | `c<SuccessResponse<List<CalendarReverseSplitDTO>>>` | ✅ 200 |
| 8 | GET | `corpaction/rightissue` | — | `c<SuccessResponse<List<CalendarRightIssueDTO>>>` | ✅ 200 |
| 9 | GET | `corpaction/rups` | — | `c<SuccessResponse<List<CalendarRupsDTO>>>` | ✅ 200 |
| 10 | GET | `corpaction/stocksplit` | — | `c<SuccessResponse<List<CalendarStockSplitDTO>>>` | ✅ 200 |
| 11 | GET | `corpaction/tenderoffer` | — | `c<SuccessResponse<List<CalendarTenderOfferDTO>>>` | ✅ 200 |
| 12 | GET | `corpaction/warrant` | — | `c<SuccessResponse<List<CalendarWarrantDTO>>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCalendarToday  [GET corpaction]
curl -X GET "https://exodus.stockbit.com/corpaction?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarBonus  [GET corpaction/bonus]
curl -X GET "https://exodus.stockbit.com/corpaction/bonus" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarDividend  [GET corpaction/dividend]
curl -X GET "https://exodus.stockbit.com/corpaction/dividend" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarEconomic  [GET corpaction/economic]
curl -X GET "https://exodus.stockbit.com/corpaction/economic" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarIpo  [GET corpaction/ipo]
curl -X GET "https://exodus.stockbit.com/corpaction/ipo" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarPublicExpose  [GET corpaction/pubex]
curl -X GET "https://exodus.stockbit.com/corpaction/pubex" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarReverseSplit  [GET corpaction/reversesplit]
curl -X GET "https://exodus.stockbit.com/corpaction/reversesplit" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarRightIssue  [GET corpaction/rightissue]
curl -X GET "https://exodus.stockbit.com/corpaction/rightissue" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarRups  [GET corpaction/rups]
curl -X GET "https://exodus.stockbit.com/corpaction/rups" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarStockSplit  [GET corpaction/stocksplit]
curl -X GET "https://exodus.stockbit.com/corpaction/stocksplit" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarTenderOffer  [GET corpaction/tenderoffer]
curl -X GET "https://exodus.stockbit.com/corpaction/tenderoffer" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCalendarWarrant  [GET corpaction/warrant]
curl -X GET "https://exodus.stockbit.com/corpaction/warrant" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 39. `GroupService`  (12 endpoint)
<sub>com/stockbit/remote/api/chat/GroupService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `chat/v2/groups` | Body:`createGroupRequest` | `A<Object>` | ⊘ not tested (write) |
| 2 | GET | `chat/v2/groups/members/max` | — | `A<Object>` | ✅ 200 |
| 3 | PUT | `chat/v2/groups/{groupId}` | Path:`groupId` · Body:`updateGroupInfoRequest` | `A<Object>` | ⊘ not tested (write) |
| 4 | POST | `chat/v2/groups/{groupId}/change-admin-and-leave` | Path:`groupId` · Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 5 | GET | `chat/v2/groups/{groupId}/members` | Path:`groupId` · QueryMap:`map` | `A<Object>` | 🚫 403 |
| 6 | POST | `chat/v2/groups/{groupId}/members/invite` | Path:`groupId` · Body:`addGroupMembersRequest` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 7 | POST | `chat/v2/groups/{groupId}/members/leave` | Path:`groupId` · Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 8 | POST | `chat/v2/groups/{groupId}/members/remove` | Path:`groupId` · Body:`removeGroupMemberRequest` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 9 | POST | `chat/v2/groups/{groupId}/reset-link` | Path:`groupId` | `A<Object>` | ⊘ not tested (write) |
| 10 | POST | `chat/v2/groups/{groupId}/set-admin-status` | Path:`groupId` · Body:`assisgnUnassignGroupAdminRequest` | `A<Object>` | ⊘ not tested (write) |
| 11 | GET | `chat/v2/groups/{group_id}/messages` | Path:`i2` · Query(src):`limit` | `A<Object>` | 🚫 403 |
| 12 | POST | `chat/v2/rooms/{roomId}/mute` | Path:`roomId` · Body:`muteUnmuteGroupRequest` | `A<Object>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# createGroup  [POST chat/v2/groups]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<CreateGroupRequest>'   # JSON body

# getMaxGroupMember  [GET chat/v2/groups/members/max]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/members/max" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateGroupInfo  [PUT chat/v2/groups/{groupId}]
curl -X PUT "https://exodus.stockbit.com/chat/v2/groups/{groupId}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<UpdateGroupInfoRequest>'   # JSON body

# changeAdminAndLeaveGroup  [POST chat/v2/groups/{groupId}/change-admin-and-leave]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/change-admin-and-leave" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, Integer>>'   # JSON body

# getGroupMembers  [GET chat/v2/groups/{groupId}/members]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/{groupId}/members?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# addGroupMembers  [POST chat/v2/groups/{groupId}/members/invite]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/members/invite" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<AddGroupMembersRequest>'   # JSON body

# leaveGroup  [POST chat/v2/groups/{groupId}/members/leave]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/members/leave" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, Boolean>>'   # JSON body

# removeGroupMembers  [POST chat/v2/groups/{groupId}/members/remove]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/members/remove" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RemoveGroupMemberRequest>'   # JSON body

# onResetGroupLink  [POST chat/v2/groups/{groupId}/reset-link]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/reset-link" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setGroupAdmin  [POST chat/v2/groups/{groupId}/set-admin-status]
curl -X POST "https://exodus.stockbit.com/chat/v2/groups/{groupId}/set-admin-status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<AssisgnUnassignGroupAdminRequest>'   # JSON body

# getMessages  [GET chat/v2/groups/{group_id}/messages]
curl -X GET "https://exodus.stockbit.com/chat/v2/groups/{group_id}/messages?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setMuteUnmuteGroup  [POST chat/v2/rooms/{roomId}/mute]
curl -X POST "https://exodus.stockbit.com/chat/v2/rooms/{roomId}/mute" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<MuteUnmuteGroupRequest>'   # JSON body

```
</details>

## 40. `WatchlistApi`  (12 endpoint)
<sub>com/stockbit/remote/api/WatchlistApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `watchlist` | Body:`map` | `c<SuccessResponse<WatchlistGroupDTO>>` | ⊘ not tested (write) |
| 2 | GET | `watchlist` | Query:`category_types` · QueryMap:`map` | `c<SuccessResponse<List<WatchlistGroupDTO>>>` | ✅ 200 |
| 3 | POST | `watchlist/companies/items` | Body:`watchlistAddCompaniesRequestDTO` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 4 | GET | `watchlist/favorite` | Query:`category_types` · QueryMap:`map` | `c<SuccessResponse<List<WatchlistGroupDTO>>>` | ✅ 200 |
| 5 | PUT | `watchlist/favorite/{watchlist_id}` | Path:`watchlist_id` · Body:`map` | `c<SuccessResponse<List<WatchlistGroupDTO>>>` | ⊘ not tested (write) |
| 6 | PUT | `watchlist/favorites/rearrange` | Body:`rearrangeFavoriteWatchlistDataParam` | — | ⊘ not tested (write) |
| 7 | PUT | `watchlist/{watchlist_id}` | Path:`watchlist_id` · Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 8 | GET | `watchlist/{watchlist_id}` | Path:`watchlist_id` · Query(src):`limit` | `c<SuccessResponse<Object>>` | ✅ 200 |
| 9 | POST | `watchlist/{watchlist_id}/company/item` | Path:`watchlist_id` · Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 10 | PUT | `watchlist/{watchlist_id}/company/item` | Path:`watchlist_id` · Body:`watchlistEditCompanyRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 11 | POST | `watchlist/{watchlist_id}/symbol-only` | Path:`watchlist_id` · Body:`watchlistStockSymbolRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 12 | GET | `watchlist/{watchlist_id}/symbols` | Path:`watchlist_id` | `c<SuccessResponse<WatchlistSymbolListDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# createWatchlistGroup  [POST watchlist]
curl -X POST "https://exodus.stockbit.com/watchlist" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getWatchlistGroup  [GET watchlist]
curl -X GET "https://exodus.stockbit.com/watchlist?category_types=<List<String>>&<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# addCompaniesToWatchlist  [POST watchlist/companies/items]
curl -X POST "https://exodus.stockbit.com/watchlist/companies/items" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<WatchlistAddCompaniesRequestDTO>'   # JSON body

# getWatchlistFavorite  [GET watchlist/favorite]
curl -X GET "https://exodus.stockbit.com/watchlist/favorite?category_types=<List<String>>&<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# rearrangeWatchlistFavorite  [PUT watchlist/favorite/{watchlist_id}]
curl -X PUT "https://exodus.stockbit.com/watchlist/favorite/{watchlist_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, Boolean>>'   # JSON body

# rearrangeWatchlistFavorite  [PUT watchlist/favorites/rearrange]
curl -X PUT "https://exodus.stockbit.com/watchlist/favorites/rearrange" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RearrangeFavoriteWatchlistDataParam>'   # JSON body

# editWatchlist  [PUT watchlist/{watchlist_id}]
curl -X PUT "https://exodus.stockbit.com/watchlist/{watchlist_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getWatchlist  [GET watchlist/{watchlist_id}]
curl -X GET "https://exodus.stockbit.com/watchlist/{watchlist_id}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# addCompanyToWatchlist  [POST watchlist/{watchlist_id}/company/item]
curl -X POST "https://exodus.stockbit.com/watchlist/{watchlist_id}/company/item" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# editWatchlistCompanies  [PUT watchlist/{watchlist_id}/company/item]
curl -X PUT "https://exodus.stockbit.com/watchlist/{watchlist_id}/company/item" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<WatchlistEditCompanyRequest>'   # JSON body

# getWatchlistStocksSymbolOnly  [POST watchlist/{watchlist_id}/symbol-only]
curl -X POST "https://exodus.stockbit.com/watchlist/{watchlist_id}/symbol-only" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<WatchlistStockSymbolRequest>'   # JSON body

# getListStockFromWatchlist  [GET watchlist/{watchlist_id}/symbols]
curl -X GET "https://exodus.stockbit.com/watchlist/{watchlist_id}/symbols" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 41. `ReferralServiceLegacy`  (11 endpoint)
<sub>com/stockbit/remote/api/ReferralServiceLegacy.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `securities/referral/cashback` | FieldMap:`map` · _Multipart_ | `A<CashbackResponse>` | ⊘ not tested (write) |
| 2 | POST | `securities/referral/exchange` | FieldMap:`map` · _Multipart_ | `A<SpinTheWheelResponse>` | ⊘ not tested (write) |
| 3 | POST | `securities/referral/history` | FieldMap:`map` · _Multipart_ | `A<ReferralHistoryListResponse>` | ⊘ not tested (write) |
| 4 | POST | `securities/referral/info` | — | `A<ReferralInfoResponse>` | ⊘ not tested (write) |
| 5 | POST | `securities/referral/list` | FieldMap:`map` · _Multipart_ | `A<ReferralListResponse>` | ⊘ not tested (write) |
| 6 | POST | `securities/referral/redeem` | FieldMap:`map` · _Multipart_ | `A<RedeemUnitResponse>` | ⊘ not tested (write) |
| 7 | POST | `securities/referral/redeem/bulk` | FieldMap:`map` · _Multipart_ | `A<RedeemAllResponse>` | ⊘ not tested (write) |
| 8 | POST | `securities/referral/stocks` | — | `A<ReferralStockResponse>` | ⊘ not tested (write) |
| 9 | POST | `securities/referral/tnc` | FieldMap:`map` · _Multipart_ | `A<SnkResponse>` | ⊘ not tested (write) |
| 10 | POST | `securities/referral/update` | FieldMap:`map` · _Multipart_ | `A<UpdateReferralCodeResponse>` | ⊘ not tested (write) |
| 11 | POST | `securities/referral/voucher/list` | — | `A<CouponListResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCashbackOrderlist  [POST securities/referral/cashback]
curl -X POST "https://exodus.stockbit.com/securities/referral/cashback" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# spinTheWheel  [POST securities/referral/exchange]
curl -X POST "https://exodus.stockbit.com/securities/referral/exchange" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getReferralHistoryList  [POST securities/referral/history]
curl -X POST "https://exodus.stockbit.com/securities/referral/history" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getReferralInfo  [POST securities/referral/info]
curl -X POST "https://exodus.stockbit.com/securities/referral/info" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getReferralList  [POST securities/referral/list]
curl -X POST "https://exodus.stockbit.com/securities/referral/list" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# redeemInUnit  [POST securities/referral/redeem]
curl -X POST "https://exodus.stockbit.com/securities/referral/redeem" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# redeemAll  [POST securities/referral/redeem/bulk]
curl -X POST "https://exodus.stockbit.com/securities/referral/redeem/bulk" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getReferralStock  [POST securities/referral/stocks]
curl -X POST "https://exodus.stockbit.com/securities/referral/stocks" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSnk  [POST securities/referral/tnc]
curl -X POST "https://exodus.stockbit.com/securities/referral/tnc" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateReferralCode  [POST securities/referral/update]
curl -X POST "https://exodus.stockbit.com/securities/referral/update" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCouponList  [POST securities/referral/voucher/list]
curl -X POST "https://exodus.stockbit.com/securities/referral/voucher/list" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 42. `LoginApi`  (10 endpoint)
<sub>com/stockbit/remote/api/LoginApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `login/v4/new-device/prompt/send` | Body:`map` | `c<SuccessResponse<SendPromptTrustedDeviceDTO>>` | ⊘ not tested (write) |
| 2 | POST | `login/v4/new-device/prompt/verify` | Body:`map` | `c<SuccessResponse<LoginDTO>>` | ⊘ not tested (write) |
| 3 | POST | `login/v4/recovery/complete` | Body:`map` | `c<SuccessResponse<LoginDTO>>` | ⊘ not tested (write) |
| 4 | POST | `login/v4/recovery/identity/validate` | Body:`recoveryValidateIdentityDataParam` | `c<SuccessResponse<TrustedDeviceTokenDTO>>` | ⊘ not tested (write) |
| 5 | POST | `login/v4/recovery/init` | Body:`map` | `c<SuccessResponse<RecoveryInitiateDTO>>` | ⊘ not tested (write) |
| 6 | POST | `login/v4/recovery/otp` | Body:`map` | `c<SuccessResponse<RecoveryOTPRequestDTO>>` | ⊘ not tested (write) |
| 7 | POST | `login/v4/recovery/otp/verify` | Body:`map` | `c<SuccessResponse<LoginDTO>>` | ⊘ not tested (write) |
| 8 | POST | `login/v4/recovery/password/validate` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 9 | POST | `login/v4/recovery/pin/forgot` | Body:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 10 | POST | `login/v4/recovery/pin/validate` | Body:`map` | `c<SuccessResponse<RecoveryOTPRecipientDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# sendNewDevicePrompt  [POST login/v4/new-device/prompt/send]
curl -X POST "https://exodus.stockbit.com/login/v4/new-device/prompt/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyNewDevicePrompt  [POST login/v4/new-device/prompt/verify]
curl -X POST "https://exodus.stockbit.com/login/v4/new-device/prompt/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# completeRecoveryIdentity  [POST login/v4/recovery/complete]
curl -X POST "https://exodus.stockbit.com/login/v4/recovery/complete" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# validateRecoveryIdentity  [POST login/v4/recovery/identity/validate]
curl -X POST "https://exodus.stockbit.com/login/v4/recovery/identity/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RecoveryValidateIdentityDataParam>'   # JSON body

# initiateRecoveryIdentity  [POST login/v4/recovery/init]
curl -X POST "https://exodus.stockbit.com/login/v4/recovery/init" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestRecoveryOTP  [POST login/v4/recovery/otp]
curl -X POST "https://exodus.stockbit.com/login/v4/recovery/otp" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyRecoveryOTP  [POST login/v4/recovery/otp/verify]
curl -X POST "https://exodus.stockbit.com/login/v4/recovery/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# validateRecoveryPassword  [POST login/v4/recovery/password/validate]
curl -X POST "https://exodus.stockbit.com/login/v4/recovery/password/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestRecoveryResetPIN  [POST login/v4/recovery/pin/forgot]
curl -X POST "https://exodus.stockbit.com/login/v4/recovery/pin/forgot" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# validateRecoveryPin  [POST login/v4/recovery/pin/validate]
curl -X POST "https://exodus.stockbit.com/login/v4/recovery/pin/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

```
</details>

## 43. `ScreenerService`  (10 endpoint)
<sub>com/stockbit/remote/api/screener/ScreenerService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `screener/favorites` | — | `A<ScreenerFavoritesResponse>` | ✅ 200 |
| 2 | POST | `screener/favorites` | Body:`addFavoriteScreenerRequest` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 3 | DELETE | `screener/favorites/{id}` | Path:`str` · QueryMap:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 4 | GET | `screener/metric` | — | `A<ScreenerFinancialMetricResponse>` | ✅ 200 |
| 5 | GET | `screener/preset` | QueryMap:`map` · QueryMap:`map2` | `A<ScreenerPresetResponse>` | ✅ 200 |
| 6 | GET | `screener/templates` | — | `A<Object>` | ✅ 200 |
| 7 | POST | `screener/templates` | Body:`screenerTemplateRequest` | `A<ScreenerScreenResponse>` | ⊘ not tested (write) |
| 8 | GET | `screener/templates/{id}` | Path:`str` · Query(src):`type` | `A<ScreenerScreenGuruOrCustomResponse>` | ✅ 200 |
| 9 | DELETE | `screener/templates/{id}` | Path:`str` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 10 | GET | `screener/universe` | — | `A<ScreenerUniverseResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getScreenerFavorites  [GET screener/favorites]
curl -X GET "https://exodus.stockbit.com/screener/favorites" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setScreenerFavorite  [POST screener/favorites]
curl -X POST "https://exodus.stockbit.com/screener/favorites" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<AddFavoriteScreenerRequest>'   # JSON body

# removeScreenerFavorite  [DELETE screener/favorites/{id}]
curl -X DELETE "https://exodus.stockbit.com/screener/favorites/{id}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getScreenerFinancialMetric  [GET screener/metric]
curl -X GET "https://exodus.stockbit.com/screener/metric" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getScreenerPreset  [GET screener/preset]
curl -X GET "https://exodus.stockbit.com/screener/preset?<map>=<Map<String, Boolean>>&<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getScreenerSaved  [GET screener/templates]
curl -X GET "https://exodus.stockbit.com/screener/templates" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setScreenerSaved  [POST screener/templates]
curl -X POST "https://exodus.stockbit.com/screener/templates" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ScreenerTemplateRequest>'   # JSON body

# getScreenerGuruOrCustom  [GET screener/templates/{id}]
curl -X GET "https://exodus.stockbit.com/screener/templates/{id}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# removeScreenerSaved  [DELETE screener/templates/{id}]
curl -X DELETE "https://exodus.stockbit.com/screener/templates/{id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getScreenerUniverse  [GET screener/universe]
curl -X GET "https://exodus.stockbit.com/screener/universe" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 44. `VerificationApi`  (9 endpoint)
<sub>com/stockbit/remote/api/VerificationApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `mfa/verification/v1/challenge/face-matching/result` | Body:`map` | `c<SuccessResponse<FaceRecognitionSessionResultDTO>>` | ⊘ not tested (write) |
| 2 | POST | `mfa/verification/v1/challenge/face-matching/start` | Body:`map` | `c<SuccessResponse<FaceRecognitionSessionDTO>>` | ⊘ not tested (write) |
| 3 | POST | `mfa/verification/v1/challenge/face-matching/verify` | Body:`map` | `c<SuccessResponse<VerificationChallengeDTO>>` | ⊘ not tested (write) |
| 4 | POST | `mfa/verification/v1/challenge/identity/verify` | Body:`map` | `c<SuccessResponse<VerificationChallengeDTO>>` | ⊘ not tested (write) |
| 5 | POST | `mfa/verification/v1/challenge/otp/send` | Body:`map` | `c<SuccessResponse<VerificationOTPDTO>>` | ⊘ not tested (write) |
| 6 | POST | `mfa/verification/v1/challenge/otp/verify` | Body:`map` | `c<SuccessResponse<VerificationChallengeDTO>>` | ⊘ not tested (write) |
| 7 | POST | `mfa/verification/v1/challenge/password/verify` | Body:`map` | `c<SuccessResponse<VerificationChallengeDTO>>` | ⊘ not tested (write) |
| 8 | POST | `mfa/verification/v1/challenge/pin/verify` | Body:`map` | `c<SuccessResponse<VerificationChallengeDTO>>` | ⊘ not tested (write) |
| 9 | POST | `mfa/verification/v1/challenge/start` | Body:`map` | `c<SuccessResponse<VerificationChallengeDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getFaceMatchingResult  [POST mfa/verification/v1/challenge/face-matching/result]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/face-matching/result" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# startFaceMatching  [POST mfa/verification/v1/challenge/face-matching/start]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/face-matching/start" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyFaceMatching  [POST mfa/verification/v1/challenge/face-matching/verify]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/face-matching/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyIdentity  [POST mfa/verification/v1/challenge/identity/verify]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/identity/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# requestOTP  [POST mfa/verification/v1/challenge/otp/send]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/otp/send" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyOTP  [POST mfa/verification/v1/challenge/otp/verify]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/otp/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyPassword  [POST mfa/verification/v1/challenge/password/verify]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/password/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# verifyPin  [POST mfa/verification/v1/challenge/pin/verify]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/pin/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# startChallenge  [POST mfa/verification/v1/challenge/start]
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/start" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

```
</details>

## 45. `VirtualExodusService`  (9 endpoint)
<sub>com/stockbit/remote/api/VirtualExodusService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `virtualtrading/account/activate` | FieldMap:`map` | `A<TradingSwitchToVirtualResponse>` | ⊘ not tested (write) |
| 2 | POST | `virtualtrading/amend/` | Body:`requestBody` | `A<VirtualAmendOrderResponse>` | ⊘ not tested (write) |
| 3 | POST | `virtualtrading/buy/{symbol}` | Path:`symbol` · Body:`requestBody` | `A<VirtualBuyOrderResponse>` | ⊘ not tested (write) |
| 4 | POST | `virtualtrading/cancel` | Body:`requestBody` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 5 | GET | `virtualtrading/config/formula` | — | `A<TradingFormulaResponse>` | ✅ 200 |
| 6 | GET | `virtualtrading/order` | — | `A<TradingOrderlistResponse>` | 🚫 403 |
| 7 | GET | `virtualtrading/portfolio` | — | `A<VirtualPortfolioResponse>` | 🚫 403 |
| 8 | GET | `virtualtrading/portfolio/{symbol}` | Path:`symbol` | `A<VirtualPortfolioDetailResponse>` | 🚫 403 |
| 9 | POST | `virtualtrading/sell/{symbol}` | Path:`symbol` · Body:`requestBody` | `A<VirtualSellOrderResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# switchToVirtual  [POST virtualtrading/account/activate]
curl -X POST "https://exodus.stockbit.com/virtualtrading/account/activate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "<map>=<Map<String, String>>"

# amendOrder  [POST virtualtrading/amend/]
curl -X POST "https://exodus.stockbit.com/virtualtrading/amend/" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# buyOrder  [POST virtualtrading/buy/{symbol}]
curl -X POST "https://exodus.stockbit.com/virtualtrading/buy/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# cancelOrder  [POST virtualtrading/cancel]
curl -X POST "https://exodus.stockbit.com/virtualtrading/cancel" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getFormula  [GET virtualtrading/config/formula]
curl -X GET "https://exodus.stockbit.com/virtualtrading/config/formula" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getTradingOrderlist  [GET virtualtrading/order]
curl -X GET "https://exodus.stockbit.com/virtualtrading/order" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getPortfolio  [GET virtualtrading/portfolio]
curl -X GET "https://exodus.stockbit.com/virtualtrading/portfolio" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getPortfolioDetail  [GET virtualtrading/portfolio/{symbol}]
curl -X GET "https://exodus.stockbit.com/virtualtrading/portfolio/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# sellOrder  [POST virtualtrading/sell/{symbol}]
curl -X POST "https://exodus.stockbit.com/virtualtrading/sell/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

```
</details>

## 46. `NotificationApi`  (8 endpoint)
<sub>com/stockbit/remote/api/NotificationApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `notification` | QueryMap:`map` · Query:`types` | `c<SuccessResponse<NotificationPageDTO>>` | ✅ 200 |
| 2 | GET | `notification/count/unread` | Query:`types` | `c<SuccessResponse<NotificationPageDTO>>` | ✅ 200 |
| 3 | PUT | `notification/settings` | Body:`notificationSettingRequest` | `c<SuccessResponse<NotificationSettingGroupDTO>>` | ⊘ not tested (write) |
| 4 | POST | `notification/v2/push-notification/send-debug` | Header:`X-DeviceID` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 5 | GET | `notification/v2/push-notification/status` | Header:`X-DeviceID` · Query(src):`device_id` | `c<SuccessResponse<NotificationStatusDTO>>` | ✅ 200 |
| 6 | PATCH | `notification/v2/push-token/update` | Body:`pushNotificationTokenDataParam` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 7 | GET | `notification/v2/settings` | — | `c<SuccessResponse<List<NotificationSettingDTO>>>` | ✅ 200 |
| 8 | PATCH | `notifications/read` | Body:`notificationReadRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getListNotification  [GET notification]
curl -X GET "https://exodus.stockbit.com/notification?<map>=<Map<String, String>>&types=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getNotifUnreadCount  [GET notification/count/unread]
curl -X GET "https://exodus.stockbit.com/notification/count/unread?types=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setNotificationSetting  [PUT notification/settings]
curl -X PUT "https://exodus.stockbit.com/notification/settings" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<NotificationSettingRequest>'   # JSON body

# sendPushNotificationDebug  [POST notification/v2/push-notification/send-debug]
curl -X POST "https://exodus.stockbit.com/notification/v2/push-notification/send-debug" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-DeviceID: $X_DEVICEID"

# getPushNotificationTokenStatus  [GET notification/v2/push-notification/status]
curl -X GET "https://exodus.stockbit.com/notification/v2/push-notification/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-DeviceID: $X_DEVICEID"

# setPushNotificationToken  [PATCH notification/v2/push-token/update]
curl -X PATCH "https://exodus.stockbit.com/notification/v2/push-token/update" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<PushNotificationTokenDataParam>'   # JSON body

# getNotificationSetting  [GET notification/v2/settings]
curl -X GET "https://exodus.stockbit.com/notification/v2/settings" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setNotificationRead  [PATCH notifications/read]
curl -X PATCH "https://exodus.stockbit.com/notifications/read" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<NotificationReadRequest>'   # JSON body

```
</details>

## 47. `SearchApi`  (8 endpoint)
<sub>com/stockbit/remote/api/SearchApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `emitten/indexes/special-board` | — | `c<SuccessResponse<SpecialBoardDTO>>` | ✅ 200 |
| 2 | GET | `emitten/sectors` | — | `c<SuccessResponse<List<EmittenSectorSubSectorDTO>>>` | ✅ 200 |
| 3 | GET | `emitten/sectors/{sectorId}/subsectors` | Path:`sectorId` | `c<SuccessResponse<List<EmittenSectorSubSectorDTO>>>` | ✅ 200 |
| 4 | GET | `emitten/v3/sector/{sectorId}/subsector/{subSectorId}/company` | Path:`sectorId` · Path:`subSectorId` | `c<SuccessResponse<List<SubSectorCompanyDTO>>>` | ✅ 200 |
| 5 | GET | `emitten/v3/sector/{sector}/company` | Path:`str` | `c<SuccessResponse<List<SubSectorCompanyDTO>>>` | ✅ 200 |
| 6 | POST | `search/recent` | Body:`recentSearchRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 7 | GET | `search/recent` | QueryMap:`map` | `c<SuccessResponse<List<RecentSearchDTO>>>` | ✅ 200 |
| 8 | GET | `search/v2/company` | QueryMap:`map` · Query:`types` · Query:`boards` | `c<SuccessResponse<SearchCompanyResultDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getSpecialBoard  [GET emitten/indexes/special-board]
curl -X GET "https://exodus.stockbit.com/emitten/indexes/special-board" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEmittenSectors  [GET emitten/sectors]
curl -X GET "https://exodus.stockbit.com/emitten/sectors" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEmittenSubSectorsInSector  [GET emitten/sectors/{sectorId}/subsectors]
curl -X GET "https://exodus.stockbit.com/emitten/sectors/{sectorId}/subsectors" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanySymbolInSubSector  [GET emitten/v3/sector/{sectorId}/subsector/{subSectorId}/company]
curl -X GET "https://exodus.stockbit.com/emitten/v3/sector/{sectorId}/subsector/{subSectorId}/company" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEmittenSectorCompany  [GET emitten/v3/sector/{sector}/company]
curl -X GET "https://exodus.stockbit.com/emitten/v3/sector/{sector}/company" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# addRecentSearch  [POST search/recent]
curl -X POST "https://exodus.stockbit.com/search/recent" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RecentSearchRequest>'   # JSON body

# getRecentSearch  [GET search/recent]
curl -X GET "https://exodus.stockbit.com/search/recent?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# searchCompany  [GET search/v2/company]
curl -X GET "https://exodus.stockbit.com/search/v2/company?<map>=<Map<String, String>>&types=<List<String>>&boards=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 48. `OrderBookApi`  (7 endpoint)
<sub>com/stockbit/remote/api/OrderBookApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `company-price-feed/historical/summary/{symbol}` | Path:`symbol` · QueryMap:`map` | `c<SuccessResponse<HistoricalDataDTO>>` | ✅ 200 |
| 2 | GET | `company-price-feed/v2/orderbook/companies/{symbol}` | Path:`symbol` · Query:`i2` · Query:`board` · HeaderMap:`map` | `c<SuccessResponse<CompanyOrderBookDTO>>` | ✅ 200 |
| 3 | GET | `company-price-feed/v2/orderbook/companies/{symbol}` | Path:`symbol` · Query:`with_full_price_tick` · HeaderMap:`map` | `c<SuccessResponse<CompanyOrderBookDTO>>` | ✅ 200 |
| 4 | GET | `order-trade/broker/distribution` | Query(src):`symbol` | `c<SuccessResponse<BrokerDistributionDTO>>` | ✅ 200 |
| 5 | GET | `order-trade/order-queue` | Query(src):`stock_code`,`board_type`,`data_type`,`market_board`,`investor_type`,`order_status`,`period`,`action_type`,`limit` | `c<SuccessResponse<OrderQueueDTO>>` | ✅ 200 |
| 6 | GET | `orderbook/companies` | Query:`symbols` · HeaderMap:`map` | `c<SuccessResponse<List<CompanyOrderBookDTO>>>` | 🔴 500 |
| 7 | GET | `orderbook/companies/IHSG` | HeaderMap:`map` | `c<SuccessResponse<MarketIHSGOrderBookDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getHistoricalData  [GET company-price-feed/historical/summary/{symbol}]
curl -X GET "https://exodus.stockbit.com/company-price-feed/historical/summary/{symbol}?<map>=<HashMap<String, Object>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getOrderBookByCompanySymbol  [GET company-price-feed/v2/orderbook/companies/{symbol}]
curl -X GET "https://exodus.stockbit.com/company-price-feed/v2/orderbook/companies/{symbol}?<map>=<int>&board=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

# getOrderBookByCompanySymbol  [GET company-price-feed/v2/orderbook/companies/{symbol}]
curl -X GET "https://exodus.stockbit.com/company-price-feed/v2/orderbook/companies/{symbol}?with_full_price_tick=<boolean>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

# getBrokerDistribution  [GET order-trade/broker/distribution]
curl -X GET "https://exodus.stockbit.com/order-trade/broker/distribution?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getOrderQueue  [GET order-trade/order-queue]
curl -X GET "https://exodus.stockbit.com/order-trade/order-queue?<map>=<HashMap<String, Object>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompaniesOrderBook  [GET orderbook/companies]
curl -X GET "https://exodus.stockbit.com/orderbook/companies?symbols=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

# getIHSGOrderBook  [GET orderbook/companies/IHSG]
curl -X GET "https://exodus.stockbit.com/orderbook/companies/IHSG" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

```
</details>

## 49. `ChatService`  (6 endpoint)
<sub>com/stockbit/remote/api/chat/ChatService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | DELETE | `chat/rooms/{room_id}` | Path:`room_id` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 2 | POST | `chat/rooms/{room_id}/clear` | Path:`room_id` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 3 | GET | `chat/s3/policy` | Query(src):`filename` | `A<AwsUploadTokenResponse>` | ✅ 200 |
| 4 | POST | `chat/v2/messages/bulk` | Body:`shareContentRequest` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 5 | GET | `chat/v2/receivers/shareable-search` | QueryMap:`map` | `A<ReceiverChatListResponse>` | ✅ 200 |
| 6 | GET | `chat/v2/rooms` | Query(src):`limit` | `A<ChatRoomsListResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# deleteChatRoom  [DELETE chat/rooms/{room_id}]
curl -X DELETE "https://exodus.stockbit.com/chat/rooms/{room_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# clearChatRoom  [POST chat/rooms/{room_id}/clear]
curl -X POST "https://exodus.stockbit.com/chat/rooms/{room_id}/clear" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getPolicyS3  [GET chat/s3/policy]
curl -X GET "https://exodus.stockbit.com/chat/s3/policy?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# shareContent  [POST chat/v2/messages/bulk]
curl -X POST "https://exodus.stockbit.com/chat/v2/messages/bulk" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ShareContentRequest>'   # JSON body

# getShareableChatRoomList  [GET chat/v2/receivers/shareable-search]
curl -X GET "https://exodus.stockbit.com/chat/v2/receivers/shareable-search?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getChatRoomList  [GET chat/v2/rooms]
curl -X GET "https://exodus.stockbit.com/chat/v2/rooms?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 50. `EmittenApi`  (6 endpoint)
<sub>com/stockbit/remote/api/EmittenApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `emitten/company/catalog` | QueryMap:`map` | `c<SuccessResponse<EmittenCompanyCatalogDTO>>` | ✅ 200 |
| 2 | GET | `emitten/discover/{type}` | Path:`type` | `c<SuccessResponse<List<EmittenDiscoverDTO>>>` | 🔴 500 |
| 3 | GET | `emitten/indexes/mobile` | — | `c<SuccessResponse<EmittenIndexDTO>>` | ✅ 200 |
| 4 | GET | `emitten/trending` | QueryMap:`map` | `c<SuccessResponse<List<CompanyDTO>>>` | ✅ 200 |
| 5 | GET | `emitten/v2/{exchange}/{emitten_symbol}/info` | Path:`exchange` · Path:`emitten_symbol` | `c<SuccessResponse<EmittenInfoDTO>>` | 🔴 500 |
| 6 | GET | `emitten/v2/{exchange}/{symbol}/fin-items` | Path:`exchange` · Path:`symbol` | `c<SuccessResponse<EmittenFinItemsDTO>>` | 🔴 500 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCompanyCatalog  [GET emitten/company/catalog]
curl -X GET "https://exodus.stockbit.com/emitten/company/catalog?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEmittenDiscover  [GET emitten/discover/{type}]
curl -X GET "https://exodus.stockbit.com/emitten/discover/{type}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEmittenIndexes  [GET emitten/indexes/mobile]
curl -X GET "https://exodus.stockbit.com/emitten/indexes/mobile" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEmittenTrending  [GET emitten/trending]
curl -X GET "https://exodus.stockbit.com/emitten/trending?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEmittenInfo  [GET emitten/v2/{exchange}/{emitten_symbol}/info]
curl -X GET "https://exodus.stockbit.com/emitten/v2/{exchange}/{emitten_symbol}/info" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEmittenFinItems  [GET emitten/v2/{exchange}/{symbol}/fin-items]
curl -X GET "https://exodus.stockbit.com/emitten/v2/{exchange}/{symbol}/fin-items" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 51. `FaceRecognitionApi`  (6 endpoint)
<sub>com/stockbit/remote/api/FaceRecognitionApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `/user/credential/v1/non-login/phone/forgot/face-matching/start` | Body:`map` | `c<SuccessResponse<FaceRecognitionSessionDTO>>` | ⊘ not tested (write) |
| 2 | POST | `auth/v3/non-login/pin/forgot/face-matching/start` | Body:`map` | `c<SuccessResponse<FaceRecognitionSessionDTO>>` | ⊘ not tested (write) |
| 3 | POST | `mfa/face-matching/sessions` | Body:`map` | `c<SuccessResponse<FaceRecognitionSessionDTO>>` | ⊘ not tested (write) |
| 4 | GET | `mfa/face-matching/sessions/{correlation_id}/results` | Path:`correlation_id` | `c<SuccessResponse<FaceRecognitionSessionResultDTO>>` | 🔴 500 |
| 5 | GET | `mfa/v1/non-login/face-matching/sessions/{correlation_id}/results` | Path:`correlation_id` | `c<SuccessResponse<FaceRecognitionSessionResultDTO>>` | ⏳ 429 |
| 6 | POST | `user/credential/v1/non-login/password/forgot/face-matching/start` | Body:`map` | `c<SuccessResponse<FaceRecognitionSessionDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getSessionNonLoginForgotPhone  [POST /user/credential/v1/non-login/phone/forgot/face-matching/start]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/phone/forgot/face-matching/start" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getSessionNonLoginForgotPin  [POST auth/v3/non-login/pin/forgot/face-matching/start]
curl -X POST "https://exodus.stockbit.com/auth/v3/non-login/pin/forgot/face-matching/start" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getSession  [POST mfa/face-matching/sessions]
curl -X POST "https://exodus.stockbit.com/mfa/face-matching/sessions" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getSessionResult  [GET mfa/face-matching/sessions/{correlation_id}/results]
curl -X GET "https://exodus.stockbit.com/mfa/face-matching/sessions/{correlation_id}/results" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSessionResultNonLogin  [GET mfa/v1/non-login/face-matching/sessions/{correlation_id}/results]
curl -X GET "https://exodus.stockbit.com/mfa/v1/non-login/face-matching/sessions/{correlation_id}/results" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSessionNonLoginForgotPassword  [POST user/credential/v1/non-login/password/forgot/face-matching/start]
curl -X POST "https://exodus.stockbit.com/user/credential/v1/non-login/password/forgot/face-matching/start" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

```
</details>

## 52. `RequestVerifiedService`  (6 endpoint)
<sub>com/stockbit/remote/api/RequestVerifiedService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `request-verified/eligibility` | — | `A<RequestBadgeEligibilityResponse>` | ✅ 200 |
| 2 | POST | `request-verified/liveness/result` | Body:`submitResultLivenessRequest` | `A<LivenessScoreResponse>` | ⊘ not tested (write) |
| 3 | GET | `request-verified/liveness/secret` | — | `A<LivenessLicenseResponse>` | ✅ 200 |
| 4 | POST | `request-verified/photo-link` | Body:`submitPhotoVerifiedBadgeRequest` | `A<BaseResponseLegacyImpl>` | ⊘ not tested (write) |
| 5 | GET | `request-verified/status` | — | `A<RequestBadgeStatusResponse>` | ✅ 200 |
| 6 | GET | `request-verified/upload-token` | Query(src):`type` | `A<AwsTokenLegacyResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getEligibility  [GET request-verified/eligibility]
curl -X GET "https://exodus.stockbit.com/request-verified/eligibility" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# submitLivenessAndGetScore  [POST request-verified/liveness/result]
curl -X POST "https://exodus.stockbit.com/request-verified/liveness/result" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<SubmitResultLivenessRequest>'   # JSON body

# getLivenessSecret  [GET request-verified/liveness/secret]
curl -X GET "https://exodus.stockbit.com/request-verified/liveness/secret" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# postVerifiedPhotoLink  [POST request-verified/photo-link]
curl -X POST "https://exodus.stockbit.com/request-verified/photo-link" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<SubmitPhotoVerifiedBadgeRequest>'   # JSON body

# getVerifiedStatus  [GET request-verified/status]
curl -X GET "https://exodus.stockbit.com/request-verified/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getUploadToken  [GET request-verified/upload-token]
curl -X GET "https://exodus.stockbit.com/request-verified/upload-token?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 53. `ScreenerApi`  (6 endpoint)
<sub>com/stockbit/remote/api/screener/ScreenerApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `screener/favorites` | Body:`screenerAddFavoriteRequestDTO` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | GET | `screener/favorites` | — | `c<SuccessResponse<List<ScreenerFavoriteDTO>>>` | ✅ 200 |
| 3 | DELETE | `screener/favorites/{id}` | Path:`str` · QueryMap:`map` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 4 | POST | `screener/templates` | Body:`screenerTemplateDataParam` | `c<SuccessResponse<ScreenerScreenDTO>>` | ⊘ not tested (write) |
| 5 | GET | `screener/templates` | — | `c<SuccessResponse<List<ScreenerSavedDTO>>>` | ✅ 200 |
| 6 | DELETE | `screener/templates/{id}` | Path:`str` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# addFavoriteScreener  [POST screener/favorites]
curl -X POST "https://exodus.stockbit.com/screener/favorites" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ScreenerAddFavoriteRequestDTO>'   # JSON body

# getFavoriteScreener  [GET screener/favorites]
curl -X GET "https://exodus.stockbit.com/screener/favorites" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# deleteFavoriteScreener  [DELETE screener/favorites/{id}]
curl -X DELETE "https://exodus.stockbit.com/screener/favorites/{id}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# createNewScreener  [POST screener/templates]
curl -X POST "https://exodus.stockbit.com/screener/templates" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ScreenerTemplateDataParam>'   # JSON body

# getScreenerSaved  [GET screener/templates]
curl -X GET "https://exodus.stockbit.com/screener/templates" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# deleteScreenerSaved  [DELETE screener/templates/{id}]
curl -X DELETE "https://exodus.stockbit.com/screener/templates/{id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 54. `SearchService`  (6 endpoint)
<sub>com/stockbit/remote/api/SearchService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `emitten/company/catalog` | QueryMap:`map` | `A<DiscoverMarketResponse>` | ✅ 200 |
| 2 | GET | `emitten/trending` | QueryMap:`map` | `A<Object>` | ✅ 200 |
| 3 | GET | `emitten/v3/sector/{sector}/subsector/{subsector}/company` | Path:`str` · Path:`str2` | `A<SubSectorCompanyResponse>` | ✅ 200 |
| 4 | POST | `search/recent` | Body:`searchRecentRequest` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 5 | GET | `search/recent` | — | `A<Object>` | ✅ 200 |
| 6 | GET | `watchlist/search/company` | Query(src):`keyword`,`watchlist_id`,`page`,`limit` | `A<SearchCompanyWatchlistResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCompanyCatalog  [GET emitten/company/catalog]
curl -X GET "https://exodus.stockbit.com/emitten/company/catalog?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getTrending  [GET emitten/trending]
curl -X GET "https://exodus.stockbit.com/emitten/trending?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanySymbolInSubSector  [GET emitten/v3/sector/{sector}/subsector/{subsector}/company]
curl -X GET "https://exodus.stockbit.com/emitten/v3/sector/{sector}/subsector/{subsector}/company" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# addRecentSearch  [POST search/recent]
curl -X POST "https://exodus.stockbit.com/search/recent" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<SearchRecentRequest>'   # JSON body

# getRecentSearch  [GET search/recent]
curl -X GET "https://exodus.stockbit.com/search/recent" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanySearchWatchlist  [GET watchlist/search/company]
curl -X GET "https://exodus.stockbit.com/watchlist/search/company?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 55. `TippingService`  (6 endpoint)
<sub>com/stockbit/remote/api/TippingService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `tip` | Body:`tippingRequest` | `A<TippingSendResponse>` | ⊘ not tested (write) |
| 2 | GET | `tip/activity` | QueryMap:`map` | `A<TippingActivityPageListingResponse>` | ✅ 200 |
| 3 | POST | `tip/claim` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 4 | GET | `tip/detail/{id}` | Path:`str` | `A<TippingResponse>` | ✅ 200 |
| 5 | PATCH | `tip/gopay-account` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 6 | GET | `tip/jar` | QueryMap:`map` | `A<MyTipJarResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# tippingSend  [POST tip]
curl -X POST "https://exodus.stockbit.com/tip" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<TippingRequest>'   # JSON body

# getTippingActivity  [GET tip/activity]
curl -X GET "https://exodus.stockbit.com/tip/activity?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# tippingClaim  [POST tip/claim]
curl -X POST "https://exodus.stockbit.com/tip/claim" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getTippingDetail  [GET tip/detail/{id}]
curl -X GET "https://exodus.stockbit.com/tip/detail/{id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateGopayAccount  [PATCH tip/gopay-account]
curl -X PATCH "https://exodus.stockbit.com/tip/gopay-account" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# loadTippingMyJarV2  [GET tip/jar]
curl -X GET "https://exodus.stockbit.com/tip/jar?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 56. `AlertApi`  (5 endpoint)
<sub>com/stockbit/remote/api/AlertApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `alert` | Body:`createAlertRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | GET | `alert` | QueryMap:`map` | `c<SuccessResponse<List<AlertItemDTO>>>` | ✅ 200 |
| 3 | GET | `alert/v2/status/active` | QueryMap:`map` | `c<SuccessResponse<List<AlertActiveItemDTO>>>` | ✅ 200 |
| 4 | GET | `alert/{alertid}` | Path:`alertid` | `c<SuccessResponse<AlertDTO>>` | ✅ 200 |
| 5 | PUT | `alert/{alertid}` | Path:`alertid` · Body:`createAlertRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# createAlert  [POST alert]
curl -X POST "https://exodus.stockbit.com/alert" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<CreateAlertRequest>'   # JSON body

# getTriggeredAlerts  [GET alert]
curl -X GET "https://exodus.stockbit.com/alert?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getActiveAlerts  [GET alert/v2/status/active]
curl -X GET "https://exodus.stockbit.com/alert/v2/status/active?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getAlert  [GET alert/{alertid}]
curl -X GET "https://exodus.stockbit.com/alert/{alertid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateAlert  [PUT alert/{alertid}]
curl -X PUT "https://exodus.stockbit.com/alert/{alertid}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<CreateAlertRequest>'   # JSON body

```
</details>

## 57. `NotificationService`  (5 endpoint)
<sub>com/stockbit/remote/api/NotificationService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `notification` | QueryMap:`map` · Query:`types` | `A<NotificationPageListingResponse>` | ✅ 200 |
| 2 | GET | `notification/count/unread` | Query:`types` | `A<NotificationPageListingResponse>` | ✅ 200 |
| 3 | GET | `notification/settings` | — | `A<Object>` | ✅ 200 |
| 4 | PUT | `notification/settings` | Body:`notificationSettingRequest` | `A<Object>` | ⊘ not tested (write) |
| 5 | PATCH | `notifications/read` | Body:`aVar` | `A<BaseResponseImpl>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getListNotification  [GET notification]
curl -X GET "https://exodus.stockbit.com/notification?<map>=<Map<String, String>>&types=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getNotifUnreadCount  [GET notification/count/unread]
curl -X GET "https://exodus.stockbit.com/notification/count/unread?types=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getNotificationSetting  [GET notification/settings]
curl -X GET "https://exodus.stockbit.com/notification/settings" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setNotificationSetting  [PUT notification/settings]
curl -X PUT "https://exodus.stockbit.com/notification/settings" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<NotificationSettingRequest>'   # JSON body

# setNotificationRead  [PATCH notifications/read]
curl -X PATCH "https://exodus.stockbit.com/notifications/read" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<com.stockbit.remote.models.request.a>'   # JSON body

```
</details>

## 58. `ShareTradeApi`  (5 endpoint)
<sub>com/stockbit/remote/api/sharetrade/ShareTradeApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `sharetrade/setting` | — | `c<SuccessResponse<AutoShareTradeSettingStatusDTO>>` | ✅ 200 |
| 2 | PUT | `sharetrade/setting/autoshare` | Body:`saveAutoShareTradeSettingRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 3 | POST | `sharetrade/share` | Body:`shareTradeOrderRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 4 | GET | `sharetrade/target` | Query(src):`limit` | `c<SuccessResponse<ShareTradeTargetListDTO>>` | ✅ 200 |
| 5 | PUT | `sharetrade/target` | Body:`saveAutoShareMyOrderRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getAutoShareTradeSettingStatus  [GET sharetrade/setting]
curl -X GET "https://exodus.stockbit.com/sharetrade/setting" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# saveAutoShareTradeSetting  [PUT sharetrade/setting/autoshare]
curl -X PUT "https://exodus.stockbit.com/sharetrade/setting/autoshare" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<SaveAutoShareTradeSettingRequest>'   # JSON body

# shareTradeOrder  [POST sharetrade/share]
curl -X POST "https://exodus.stockbit.com/sharetrade/share" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ShareTradeOrderRequest>'   # JSON body

# getShareTradeTargetList  [GET sharetrade/target]
curl -X GET "https://exodus.stockbit.com/sharetrade/target?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# saveAutoShareMyOrder  [PUT sharetrade/target]
curl -X PUT "https://exodus.stockbit.com/sharetrade/target" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<SaveAutoShareMyOrderRequest>'   # JSON body

```
</details>

## 59. `SocialUserApi`  (5 endpoint)
<sub>com/stockbit/remote/api/SocialUserApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `user/avatar/collection` | — | `c<SuccessResponse<List<AvatarCollectionDTO>>>` | ✅ 200 |
| 2 | PUT | `user/profile` | Body:`map` | `c<SuccessResponse<EditSocialInfoDTO>>` | ⊘ not tested (write) |
| 3 | POST | `user/upload/token` | Body:`map` | `c<SuccessResponse<UploadAvatarTokenDTO>>` | ⊘ not tested (write) |
| 4 | GET | `usergraph/socialinfo/user/me` | — | `c<SuccessResponse<SocialInfoDTO>>` | ✅ 200 |
| 5 | GET | `usergraph/socialinfo/{username}` | Path:`username` | `c<SuccessResponse<SocialInfoDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getAvatarCollection  [GET user/avatar/collection]
curl -X GET "https://exodus.stockbit.com/user/avatar/collection" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setProfileSocial  [PUT user/profile]
curl -X PUT "https://exodus.stockbit.com/user/profile" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# generateUploadToken  [POST user/upload/token]
curl -X POST "https://exodus.stockbit.com/user/upload/token" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getMyProfileSocial  [GET usergraph/socialinfo/user/me]
curl -X GET "https://exodus.stockbit.com/usergraph/socialinfo/user/me" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getProfileSocial  [GET usergraph/socialinfo/{username}]
curl -X GET "https://exodus.stockbit.com/usergraph/socialinfo/{username}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 60. `BannerApi`  (4 endpoint)
<sub>com/stockbit/remote/api/banner/BannerApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `banner/notification` | QueryMap:`map` | `c<SuccessResponse<BannerNotificationDTO>>` | ✅ 200 |
| 2 | PATCH | `banner/notification/status/update` | Body:`bannerNotificationUpdateStatusRequest` | `c<SuccessResponse<BannerUpdateStatusDTO>>` | ⊘ not tested (write) |
| 3 | GET | `notification/v2/banners` | — | `c<SuccessResponse<BannerNotificationInAppDTO>>` | ✅ 200 |
| 4 | PATCH | `notification/v2/banners/{id}/dismiss` | Path:`str` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getBannerNotification  [GET banner/notification]
curl -X GET "https://exodus.stockbit.com/banner/notification?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateStatusBannerNotification  [PATCH banner/notification/status/update]
curl -X PATCH "https://exodus.stockbit.com/banner/notification/status/update" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<BannerNotificationUpdateStatusRequest>'   # JSON body

# getBannerInAppNotification  [GET notification/v2/banners]
curl -X GET "https://exodus.stockbit.com/notification/v2/banners" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# dismissBannerInAppNotification  [PATCH notification/v2/banners/{id}/dismiss]
curl -X PATCH "https://exodus.stockbit.com/notification/v2/banners/{id}/dismiss" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 61. `BrokerActivityApi`  (4 endpoint)
<sub>com/stockbit/remote/api/brokeractivity/BrokerActivityApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `order-trade/broker/activity` | Query:`broker_code` · Query(src):`broker_code`,`to`,`transaction_type`,`market_board`,`investor_type`,`period` · Query:`to` · Query:`transaction_type` · Query:`market_board` · Query:`investor_type` · Query:`period` · Query(src):`broker_code`,`to`,`transaction_type`,`market_board`,`investor_type`,`period` · Query(src):`broker_code`,`to`,`transaction_type`,`market_board`,`investor_type`,`period` | `c<SuccessResponse<BrokerActivityListDTO>>` | ✅ 200 |
| 2 | GET | `order-trade/broker/activity-chart` | Query:`brokers_code` · Query:`symbols` · Query(src):`brokers_code`,`symbols`,`to`,`market_board`,`investor_type`,`period` · Query:`to` · Query:`market_board` · Query:`investor_type` · Query:`period` | `c<SuccessResponse<BrokerActivityChartDTO>>` | ✅ 200 |
| 3 | GET | `order-trade/broker/activity/historical` | Query:`interval` · Query:`date_from` · Query:`date_to` · Query:`period` · Query:`broker_codes` · Query:`symbols` · Query:`market_board` · Query:`investor_type` · Query:`transaction_type` · Query:`pagination.page` · Query:`pagination.limit` | `c<SuccessResponse<BrokerActivityDailyDTO>>` | ✅ 200 |
| 4 | GET | `order-trade/broker/top` | QueryMap:`map` · HeaderMap:`map2` | `c<SuccessResponse<BrokerActivityDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getBrokerActivityList  [GET order-trade/broker/activity]
curl -X GET "https://exodus.stockbit.com/order-trade/broker/activity?broker_code=<List<String>>&<map>=<String>&to=<String>&transaction_type=<String>&market_board=<String>&investor_type=<String>&period=<String>&<map>=<Integer>&<map>=<Integer>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBrokerActivityChart  [GET order-trade/broker/activity-chart]
curl -X GET "https://exodus.stockbit.com/order-trade/broker/activity-chart?brokers_code=<List<String>>&symbols=<List<String>>&<map>=<String>&to=<String>&market_board=<String>&investor_type=<String>&period=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBrokerActivityDaily  [GET order-trade/broker/activity/historical]
curl -X GET "https://exodus.stockbit.com/order-trade/broker/activity/historical?interval=<String>&date_from=<String>&date_to=<String>&period=<String>&broker_codes=<List<String>>&symbols=<List<String>>&market_board=<String>&investor_type=<String>&transaction_type=<String>&pagination.page=<Integer>&pagination.limit=<Integer>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getTopBrokerActivity  [GET order-trade/broker/top]
curl -X GET "https://exodus.stockbit.com/order-trade/broker/top?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

```
</details>

## 62. `CompanyNoteApi`  (4 endpoint)
<sub>com/stockbit/remote/api/stream/notes/CompanyNoteApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `notes` | Body:`createNoteDataParam` | `c<SuccessResponse<w>>` | ⊘ not tested (write) |
| 2 | GET | `notes` | QueryMap:`map` | `c<SuccessResponse<CompanyNoteListDTO>>` | ✅ 200 |
| 3 | DELETE | `notes/{id}` | Path:`str` | `c<SuccessResponse<w>>` | ⊘ not tested (write) |
| 4 | PUT | `notes/{id}` | Path:`str` · Body:`updateNoteDataParam` | `c<SuccessResponse<w>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# createCompanyNote  [POST notes]
curl -X POST "https://exodus.stockbit.com/notes" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<CreateNoteDataParam>'   # JSON body

# getCompanyNotes  [GET notes]
curl -X GET "https://exodus.stockbit.com/notes?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# deleteCompanyNote  [DELETE notes/{id}]
curl -X DELETE "https://exodus.stockbit.com/notes/{id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateCompanyNote  [PUT notes/{id}]
curl -X PUT "https://exodus.stockbit.com/notes/{id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<UpdateNoteDataParam>'   # JSON body

```
</details>

## 63. `FriendDiscoveryService`  (4 endpoint)
<sub>com/stockbit/remote/api/FriendDiscoveryService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `friend-discovery/contacts/remove-all` | — | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 2 | GET | `friend-discovery/suggestions/contacts` | QueryMap:`map` | `A<ContactResponse>` | ✅ 200 |
| 3 | GET | `friend-discovery/suggestions/query` | QueryMap:`map` | `A<SuggestedUserPagingResponse>` | ✅ 200 |
| 4 | POST | `friend-discovery/v2/contacts/save` | Body:`discoverSaveContactRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# removeAccessContact  [POST friend-discovery/contacts/remove-all]
curl -X POST "https://exodus.stockbit.com/friend-discovery/contacts/remove-all" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getContacts  [GET friend-discovery/suggestions/contacts]
curl -X GET "https://exodus.stockbit.com/friend-discovery/suggestions/contacts?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSuggestionContact  [GET friend-discovery/suggestions/query]
curl -X GET "https://exodus.stockbit.com/friend-discovery/suggestions/query?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# saveContact  [POST friend-discovery/v2/contacts/save]
curl -X POST "https://exodus.stockbit.com/friend-discovery/v2/contacts/save" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<DiscoverSaveContactRequest>'   # JSON body

```
</details>

## 64. `InsiderApi`  (4 endpoint)
<sub>com/stockbit/remote/api/insider/InsiderApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `insider/company/majorholder` | QueryMap:`map` | `c<SuccessResponse<InsiderCompanyDTO>>` | ✅ 200 |
| 2 | GET | `insider/company/majorholder` | Query:`symbols` · QueryMap:`map` | `c<SuccessResponse<InsiderActivityDTO>>` | ✅ 200 |
| 3 | GET | `insider/majorholder/ownership` | Query(src):`insider`,`source_type`,`page` | `c<SuccessResponse<InsiderDetailDTO>>` | ✅ 200 |
| 4 | GET | `insider/shareholding/composition/companies/{symbol}` | Path:`symbol` · QueryMap:`map` | `c<SuccessResponse<ShareholderCompositionDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCompanyInsider  [GET insider/company/majorholder]
curl -X GET "https://exodus.stockbit.com/insider/company/majorholder?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getInsiderActivity  [GET insider/company/majorholder]
curl -X GET "https://exodus.stockbit.com/insider/company/majorholder?symbols=<List<String>>&<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getInsiderDetail  [GET insider/majorholder/ownership]
curl -X GET "https://exodus.stockbit.com/insider/majorholder/ownership?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getShareholderComposition  [GET insider/shareholding/composition/companies/{symbol}]
curl -X GET "https://exodus.stockbit.com/insider/shareholding/composition/companies/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 65. `UserFollowApi`  (4 endpoint)
<sub>com/stockbit/remote/api/UserFollowApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | PUT | `watchlist/people/alert` | Body:`turnOnNotificationSubscribetionRequest` | `c<SuccessResponse<FollowedDTO>>` | ⊘ not tested (write) |
| 2 | POST | `watchlist/people/item` | Body:`followPeopleRequest` | `c<SuccessResponse<FollowPeopleDTO>>` | ⊘ not tested (write) |
| 3 | GET | `watchlist/people/{user_id}/followers` | Path:`user_id` · QueryMap:`map` | `c<SuccessResponse<FollowersDTO>>` | ✅ 200 |
| 4 | GET | `watchlist/people/{user_id}/following` | Path:`user_id` · QueryMap:`map` | `c<SuccessResponse<FollowersDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# toggleFollowedUserNotificationSubscription  [PUT watchlist/people/alert]
curl -X PUT "https://exodus.stockbit.com/watchlist/people/alert" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<TurnOnNotificationSubscribetionRequest>'   # JSON body

# postFollowSuggestedPeople  [POST watchlist/people/item]
curl -X POST "https://exodus.stockbit.com/watchlist/people/item" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<FollowPeopleRequest>'   # JSON body

# getFollowers  [GET watchlist/people/{user_id}/followers]
curl -X GET "https://exodus.stockbit.com/watchlist/people/{user_id}/followers?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getFollowing  [GET watchlist/people/{user_id}/following]
curl -X GET "https://exodus.stockbit.com/watchlist/people/{user_id}/following?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 66. `ChatPersonalApi`  (3 endpoint)
<sub>com/stockbit/remote/api/chat/ChatPersonalApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `chat/v2/personal/room/{room_id}` | Path:`room_id` | `c<SuccessResponse<RoomDTO>>` | 🟡 400 |
| 2 | GET | `chat/v2/personal/{room_id}/messages` | Path:`room_id` · Query(src):`limit` | `c<SuccessResponse<MessagesDTO>>` | 🚫 403 |
| 3 | GET | `chat/v2/rooms/{room_id}` | Path:`room_id` | `c<SuccessResponse<RoomDTO>>` | ⚪ 404 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getRoomByUserId  [GET chat/v2/personal/room/{room_id}]
curl -X GET "https://exodus.stockbit.com/chat/v2/personal/room/{room_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getMessages  [GET chat/v2/personal/{room_id}/messages]
curl -X GET "https://exodus.stockbit.com/chat/v2/personal/{room_id}/messages?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getRoomByRoomId  [GET chat/v2/rooms/{room_id}]
curl -X GET "https://exodus.stockbit.com/chat/v2/rooms/{room_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 67. `ComparisonService`  (3 endpoint)
<sub>com/stockbit/remote/api/company/ComparisonService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `comparison/v2/ratios` | Query(src):`symbol` | `A<Object>` | ✅ 200 |
| 2 | GET | `comparison/v2/{symbol}/competitors` | Path:`symbol` | `A<Object>` | ✅ 200 |
| 3 | DELETE | `comparison/v2/{symbol}/competitors/{competitor_symbol}` | Path:`symbol` · Path:`competitor_symbol` | `A<BaseResponseImpl>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCompanyRatios  [GET comparison/v2/ratios]
curl -X GET "https://exodus.stockbit.com/comparison/v2/ratios?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyCompetitors  [GET comparison/v2/{symbol}/competitors]
curl -X GET "https://exodus.stockbit.com/comparison/v2/{symbol}/competitors" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# deleteCompanyCompetitor  [DELETE comparison/v2/{symbol}/competitors/{competitor_symbol}]
curl -X DELETE "https://exodus.stockbit.com/comparison/v2/{symbol}/competitors/{competitor_symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 68. `LivestreamApi`  (3 endpoint)
<sub>com/stockbit/remote/api/LivestreamApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `live-stream/event` | Query(src):`page`,`limit` | `c<SuccessResponse<List<LivestreamDTO>>>` | ✅ 200 |
| 2 | GET | `live-stream/event/{event_id}` | Path:`event_id` | `c<SuccessResponse<LivestreamDTO>>` | ✅ 200 |
| 3 | POST | `live-stream/event/{event_id}/question` | Path:`event_id` · Body:`jsonObject` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getLivestream  [GET live-stream/event]
curl -X GET "https://exodus.stockbit.com/live-stream/event?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getDetailLivestream  [GET live-stream/event/{event_id}]
curl -X GET "https://exodus.stockbit.com/live-stream/event/{event_id}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# submitQuestion  [POST live-stream/event/{event_id}/question]
curl -X POST "https://exodus.stockbit.com/live-stream/event/{event_id}/question" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

```
</details>

## 69. `OrderBookService`  (3 endpoint)
<sub>com/stockbit/remote/api/OrderBookService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `company-price-feed/trade-book` | Query(src):`symbol`,`group_by`,`sort_by`,`sort_direction`,`time_interval`,`to` | `A<Object>` | ✅ 200 |
| 2 | GET | `orderbook/companies/{symbol}` | Path:`symbol` | `A<CompanyOrderbookResponse>` | ✅ 200 |
| 3 | GET | `orderbook/companies/{symbol}` | Path:`symbol` | `A<Object>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getInitTradeBook  [GET company-price-feed/trade-book]
curl -X GET "https://exodus.stockbit.com/company-price-feed/trade-book?<map>=<HashMap<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCompanyOrderBook  [GET orderbook/companies/{symbol}]
curl -X GET "https://exodus.stockbit.com/orderbook/companies/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getIHSGOrderBook  [GET orderbook/companies/{symbol}]
curl -X GET "https://exodus.stockbit.com/orderbook/companies/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 70. `PriceFeedService`  (3 endpoint)
<sub>com/stockbit/remote/api/company/PriceFeedService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `company-price-feed/indicative-price-volume/{symbol}` | Path:`symbol` | `A<IEPIEVResponse>` | ✅ 200 |
| 2 | GET | `company-price-feed/running-trade` | Query(src):`symbol`,`order_by` | `A<Object>` | ✅ 200 |
| 3 | GET | `company-price-feed/v2/running-trade` | Query(src):`symbol`,`order_by` | `A<Object>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getIEPIEV  [GET company-price-feed/indicative-price-volume/{symbol}]
curl -X GET "https://exodus.stockbit.com/company-price-feed/indicative-price-volume/{symbol}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getInitRunningTrade  [GET company-price-feed/running-trade]
curl -X GET "https://exodus.stockbit.com/company-price-feed/running-trade?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getInitRunningTradeV2  [GET company-price-feed/v2/running-trade]
curl -X GET "https://exodus.stockbit.com/company-price-feed/v2/running-trade?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 71. `SocialSubscriptionApi`  (3 endpoint)
<sub>com/stockbit/remote/api/SocialSubscriptionApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `pro-sub/order/history` | QueryMap:`map` · Query:`str` | `c<SuccessResponse<SocialSubscriptionHistoryDTO>>` | ✅ 200 |
| 2 | GET | `pro-sub/products` | — | `c<SuccessResponse<List<SocialSubscriptionProductDTO>>>` | ✅ 200 |
| 3 | POST | `pro-sub/transaction/verify/google` | Body:`jsonObject` | `c<SuccessResponse<SocialSubscriptionVerifyDTO>>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getSubscriptionHistory  [GET pro-sub/order/history]
curl -X GET "https://exodus.stockbit.com/pro-sub/order/history?<map>=<Map<String, String>>&<map>=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSubscriptionProducts  [GET pro-sub/products]
curl -X GET "https://exodus.stockbit.com/pro-sub/products" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyPurchase  [POST pro-sub/transaction/verify/google]
curl -X POST "https://exodus.stockbit.com/pro-sub/transaction/verify/google" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

```
</details>

## 72. `AcademyApi`  (2 endpoint)
<sub>com/stockbit/remote/api/AcademyApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `academy/tokens/new` | — | `c<SuccessResponse<AcademyTokenDTO>>` | ⊘ not tested (write) |
| 2 | GET | `academy/unboxing` | QueryMap:`map` | `c<SuccessResponse<List<UnboxingDTO>>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getAcademyToken  [POST academy/tokens/new]
curl -X POST "https://exodus.stockbit.com/academy/tokens/new" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getUnboxingList  [GET academy/unboxing]
curl -X GET "https://exodus.stockbit.com/academy/unboxing?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 73. `ExploreService`  (2 endpoint)
<sub>com/stockbit/remote/api/ExploreService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `friend-discovery/contacts/discoverable` | — | `A<BlacklistStatusResponse>` | ✅ 200 |
| 2 | POST | `friend-discovery/contacts/discoverable` | — | `A<BlacklistStatusResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getStatusBlacklist  [GET friend-discovery/contacts/discoverable]
curl -X GET "https://exodus.stockbit.com/friend-discovery/contacts/discoverable" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# setStatusBlacklist  [POST friend-discovery/contacts/discoverable]
curl -X POST "https://exodus.stockbit.com/friend-discovery/contacts/discoverable" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 74. `FriendDiscoveryApi`  (2 endpoint)
<sub>com/stockbit/remote/api/FriendDiscoveryApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `friend-discovery/contacts/status` | — | `c<SuccessResponse<ContactStatusDTO>>` | ✅ 200 |
| 2 | GET | `friend-discovery/followed-by` | QueryMap:`map` | `c<SuccessResponse<FollowedByListDTO>>` | 🔴 500 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getContactStatus  [GET friend-discovery/contacts/status]
curl -X GET "https://exodus.stockbit.com/friend-discovery/contacts/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getFollowedBy  [GET friend-discovery/followed-by]
curl -X GET "https://exodus.stockbit.com/friend-discovery/followed-by?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 75. `MoversApi`  (2 endpoint)
<sub>com/stockbit/remote/api/movers/MoversApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `order-trade/market-mover` | QueryMap:`map` · Query:`filter_stocks` | `c<SuccessResponse<MoversListDTO>>` | ✅ 200 |
| 2 | GET | `order-trade/market-mover/{category}/options` | Path:`category` · Query:`filter_stocks` | `c<SuccessResponse<MoversOptionsDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getMoversList  [GET order-trade/market-mover]
curl -X GET "https://exodus.stockbit.com/order-trade/market-mover?<map>=<Map<String, String>>&filter_stocks=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getMoverCategoryOptions  [GET order-trade/market-mover/{category}/options]
curl -X GET "https://exodus.stockbit.com/order-trade/market-mover/{category}/options?filter_stocks=<List<String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 76. `PaywallApi`  (2 endpoint)
<sub>com/stockbit/remote/api/PaywallApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `paywall/counter/increment` | Body:`jsonObject` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | GET | `paywall/eligibility/check` | QueryMap:`map` | `c<SuccessResponse<PaywallDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# incrementPaywallCounter  [POST paywall/counter/increment]
curl -X POST "https://exodus.stockbit.com/paywall/counter/increment" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# getPaywallEligibility  [GET paywall/eligibility/check]
curl -X GET "https://exodus.stockbit.com/paywall/eligibility/check?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 77. `SeasonalityService`  (2 endpoint)
<sub>com/stockbit/remote/api/company/SeasonalityService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `seasonality/{company_symbol}` | Path:`company_symbol` · Query(src):`year` | `A<Object>` | ✅ 200 |
| 2 | GET | `seasonality/{company_symbol}/years` | Path:`company_symbol` | `A<Object>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getSeasonality  [GET seasonality/{company_symbol}]
curl -X GET "https://exodus.stockbit.com/seasonality/{company_symbol}?<map>=<Map<String, Integer>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSeasonalityYearsData  [GET seasonality/{company_symbol}/years]
curl -X GET "https://exodus.stockbit.com/seasonality/{company_symbol}/years" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 78. `SocialUserService`  (2 endpoint)
<sub>com/stockbit/remote/api/SocialUserService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `usergraph/socialinfo/user/me` | — | `A<Object>` | ✅ 200 |
| 2 | GET | `usergraph/socialinfo/{username}` | Path:`username` | `A<Object>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getMyProfileSocial  [GET usergraph/socialinfo/user/me]
curl -X GET "https://exodus.stockbit.com/usergraph/socialinfo/user/me" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getProfileSocial  [GET usergraph/socialinfo/{username}]
curl -X GET "https://exodus.stockbit.com/usergraph/socialinfo/{username}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 79. `UnboxingService`  (2 endpoint)
<sub>com/stockbit/remote/api/UnboxingService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `academy/unboxing` | QueryMap:`map` | `A<UnboxingListResponse>` | ✅ 200 |
| 2 | GET | `academy/unboxing/{volume}` | Path:`volume` | `A<UnboxingDetailResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getUnboxingList  [GET academy/unboxing]
curl -X GET "https://exodus.stockbit.com/academy/unboxing?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getDetailUnboxing  [GET academy/unboxing/{volume}]
curl -X GET "https://exodus.stockbit.com/academy/unboxing/{volume}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 80. `ChartsApi`  (1 endpoint)
<sub>com/stockbit/remote/api/ChartsApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `charts/{symbol}` | Path:`symbol` · Query(src):`timeframe` | `c<SuccessResponse<ChartsDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCharts  [GET charts/{symbol}]
curl -X GET "https://exodus.stockbit.com/charts/{symbol}?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 81. `ChatBroadcastApi`  (1 endpoint)
<sub>com/stockbit/remote/api/chat/ChatBroadcastApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `chat/v2/broadcast/{room_id}/messages` | Path:`room_id` · Query(src):`limit` | `c<SuccessResponse<MessagesDTO>>` | 🚫 403 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getMessages  [GET chat/v2/broadcast/{room_id}/messages]
curl -X GET "https://exodus.stockbit.com/chat/v2/broadcast/{room_id}/messages?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 82. `DiscoverSectorApi`  (1 endpoint)
<sub>com/stockbit/remote/api/DiscoverSectorApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `emitten/sector/catalog` | — | `c<SuccessResponse<List<DiscoverSectorDTO>>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getDiscoverSector  [GET emitten/sector/catalog]
curl -X GET "https://exodus.stockbit.com/emitten/sector/catalog" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 83. `MessageService`  (1 endpoint)
<sub>com/stockbit/remote/api/chat/MessageService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `chat/v2/messages` | Body:`sendMessageV2Request` | `A<SendMessageResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# sendMessage  [POST chat/v2/messages]
curl -X POST "https://exodus.stockbit.com/chat/v2/messages" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<SendMessageV2Request>'   # JSON body

```
</details>

## 84. `SecuritiesAuthService`  (1 endpoint)
<sub>com/stockbit/remote/api/SecuritiesAuthService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `sekuritas/auth/token` | QueryMap:`map` | `A<TradingStockbitTokenResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getSecuritiesAuthToken  [GET sekuritas/auth/token]
curl -X GET "https://exodus.stockbit.com/sekuritas/auth/token?<map>=<Map<String, Boolean>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 85. `StreamApi`  (1 endpoint)
<sub>com/stockbit/remote/api/stream/StreamApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `stream/v2/uploadtoken` | — | `c<SuccessResponse<UploadTokenDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getUploadToken  [GET stream/v2/uploadtoken]
curl -X GET "https://exodus.stockbit.com/stream/v2/uploadtoken" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 86. `TopStockApi`  (1 endpoint)
<sub>com/stockbit/remote/api/TopStockApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `order-trade/top-stock` | QueryMap:`map` | `c<SuccessResponse<TopStockDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getTopStock  [GET order-trade/top-stock]
curl -X GET "https://exodus.stockbit.com/order-trade/top-stock?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 87. `WebSocketAuthService`  (1 endpoint)
<sub>com/stockbit/remote/api/WebSocketAuthService.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `auth/websocket/key` | — | `A<WebSocketProtobufKeyResponse>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getWsKey  [GET auth/websocket/key]
curl -X GET "https://exodus.stockbit.com/auth/websocket/key" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 88. `WebSocketSocialAuthApi`  (1 endpoint)
<sub>com/stockbit/remote/api/WebSocketSocialAuthApi.java · qualifier `CLIENT_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `/auth/websocket/key` | — | `c<SuccessResponse<WebSocketTokenDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getWsKey  [GET /auth/websocket/key]
curl -X GET "https://exodus.stockbit.com/auth/websocket/key" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

# ━━ HOST: FLIPT — `https://flipt.stockbit.com` ━━

**Auth:** service/anon (feature-flag eval)

## 89. `FliptService`  (1 endpoint)
<sub>com/stockbit/remote/api/FliptService.java · qualifier `CLIENT_FLIPT`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `evaluate/v1/boolean` | Body:`fliptRequestParams` | `A<Object>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getBooleanEvaluation  [POST evaluate/v1/boolean]
curl -X POST "https://flipt.stockbit.com/evaluate/v1/boolean" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<FliptRequestParams>'   # JSON body

```
</details>

# ━━ HOST: LEGACY v2.4 — `https://api.stockbit.com/v2.4` ━━

**Auth:** Bearer (social access token) — legacy

## 90. `UserServiceLegacy`  (5 endpoint)
<sub>com/stockbit/remote/api/UserServiceLegacy.java · qualifier `CLIENT_BASE_LEGACY`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `glossary` | QueryMap:`map` | — | ✅ 200 |
| 2 | GET | `glossary/letter/{letter}` | Path:`letter` · _Multipart_ | — | ✅ 200 |
| 3 | POST | `user/registration/phone` | FieldMap:`map` | — | ⊘ not tested (write) |
| 4 | POST | `user/setting/createpassword` | FieldMap:`map` | — | ⊘ not tested (write) |
| 5 | POST | `user/verification/phone` | FieldMap:`map` | — | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getGlossaryItemSearch  [GET glossary]
curl -X GET "https://api.stockbit.com/v2.4/glossary?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getGlossaryItemByLetter  [GET glossary/letter/{letter}]
curl -X GET "https://api.stockbit.com/v2.4/glossary/letter/{letter}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# registerUnverified  [POST user/registration/phone]
curl -X POST "https://api.stockbit.com/v2.4/user/registration/phone" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "<map>=<Map<String, String>>"

# setPassword  [POST user/setting/createpassword]
curl -X POST "https://api.stockbit.com/v2.4/user/setting/createpassword" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "<map>=<Map<String, String>>"

# validateOtpUnverifiedUser  [POST user/verification/phone]
curl -X POST "https://api.stockbit.com/v2.4/user/verification/phone" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "<map>=<Map<String, String>>"

```
</details>

# ━━ HOST: SEKURITAS — `https://api-sekuritas.stockbit.com` ━━

**Auth:** Bearer securities/trading token (PIN-gated)

## 91. `SecuritiesOAService`  (16 endpoint)
<sub>com/stockbit/remote/api/SecuritiesOAService.java · qualifier `SECURITIES_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `/v2/account/upload/token` | QueryMap:`map` | `A<GoogleUploadTokenSecuritiesResponse>` | 🟡 400 |
| 2 | POST | `/v2/registration/rdn/confirmation` | Body:`jagoWebviewUrlRequest` | `A<JagoWebviewUrlResponse>` | ⊘ not tested (write) |
| 3 | GET | `/v3/registration/link/{partner}` | Path:`partner` | `A<JagoLinkInformationResponse>` | ✅ 200 |
| 4 | POST | `/v3/registration/rdn/binding/{rdn_name}` | Path:`rdn_name` · Body:`map` | `A<FormSubmitResultResponse>` | ⊘ not tested (write) |
| 5 | GET | `v2/account/upload/url` | QueryMap:`map` | `A<GoogleUploadTokenAmendBankResponse>` | 🟡 400 |
| 6 | POST | `v2/registration/bank/validate` | Body:`bankCheckRequest` | `A<BankCheckResponse>` | ⊘ not tested (write) |
| 7 | GET | `v2/registration/bibit/access` | — | `A<Object>` | ⚪ 404 |
| 8 | GET | `v2/registration/bibit/check` | — | `A<Object>` | ✅ 200 |
| 9 | POST | `v2/registration/bibit/register` | Body:`bibitValidateRequest` | `A<Object>` | ⊘ not tested (write) |
| 10 | GET | `v2/registration/check` | — | `A<OASecuritiesStatusResponse>` | ✅ 200 |
| 11 | POST | `v2/registration/referral` | Body:`referralValidateRequest` | `A<ReferralNameResponse>` | ⊘ not tested (write) |
| 12 | GET | `v2/registration/upload/presign` | QueryMap:`map` | `A<UploadPreSignResponse>` | 🟡 400 |
| 13 | GET | `v2/registration/upload/token` | QueryMap:`map` | `A<GoogleUploadTokenSecuritiesResponse>` | 🟡 400 |
| 14 | GET | `v3/registration/form/{version}` | Path:`version` | `A<SecuritiesFormResponse>` | 🟡 400 |
| 15 | GET | `{url}` | Path:`url` | `A<SimpleItemListResponse>` | ⚪ 404 |
| 16 | POST | `{url}` | Path:`url` · Body:`requestBody` | `A<FormSubmitResultResponse>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getAmendUploadTokenOld  [GET /v2/account/upload/token]
curl -X GET "https://api-sekuritas.stockbit.com/v2/account/upload/token?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getJagoWebviewUrl  [POST /v2/registration/rdn/confirmation]
curl -X POST "https://api-sekuritas.stockbit.com/v2/registration/rdn/confirmation" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JagoWebviewUrlRequest>'   # JSON body

# getJagoLinkInformation  [GET /v3/registration/link/{partner}]
curl -X GET "https://api-sekuritas.stockbit.com/v3/registration/link/{partner}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# bindingJagoRegistration  [POST /v3/registration/rdn/binding/{rdn_name}]
curl -X POST "https://api-sekuritas.stockbit.com/v3/registration/rdn/binding/{rdn_name}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getAmendUploadToken  [GET v2/account/upload/url]
curl -X GET "https://api-sekuritas.stockbit.com/v2/account/upload/url?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# bankCheck  [POST v2/registration/bank/validate]
curl -X POST "https://api-sekuritas.stockbit.com/v2/registration/bank/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<BankCheckRequest>'   # JSON body

# getBibitAccountAccess  [GET v2/registration/bibit/access]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/bibit/access" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBibitAccountStatus  [GET v2/registration/bibit/check]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/bibit/check" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# validateBibitAccess  [POST v2/registration/bibit/register]
curl -X POST "https://api-sekuritas.stockbit.com/v2/registration/bibit/register" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<BibitValidateRequest>'   # JSON body

# getSecuritiesStatus  [GET v2/registration/check]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/check" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# submitReferral  [POST v2/registration/referral]
curl -X POST "https://api-sekuritas.stockbit.com/v2/registration/referral" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<ReferralValidateRequest>'   # JSON body

# getUploadPreSign  [GET v2/registration/upload/presign]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/upload/presign?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getUploadToken  [GET v2/registration/upload/token]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/upload/token?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSecuritiesForm  [GET v3/registration/form/{version}]
curl -X GET "https://api-sekuritas.stockbit.com/v3/registration/form/{version}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getSimpleListItem  [GET {url}]
curl -X GET "https://api-sekuritas.stockbit.com/{url}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# submitForm  [POST {url}]
curl -X POST "https://api-sekuritas.stockbit.com/{url}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

```
</details>

## 92. `AccountApi`  (10 endpoint)
<sub>com/stockbit/remote/api/AccountApi.java · qualifier `SECURITIES_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `/v2/account/bank/amend` | — | `A<AmendBankStatusResponse>` | ✅ 200 |
| 2 | POST | `/v2/account/bank/amend` | Body:`amendBankSubmitParams` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 3 | GET | `/v2/account/liveness/quota` | — | `A<LivenessQuotaResponse>` | ✅ 200 |
| 4 | POST | `/v2/account/liveness/result` | Body:`map` | `A<LivenessScoreResponse>` | ⊘ not tested (write) |
| 5 | POST | `/v2/account/liveness/secret` | Body:`map` | `A<LivenessLicenseResponse>` | ⊘ not tested (write) |
| 6 | GET | `account/personal` | — | `c<SuccessResponse<TradingAccountDataDTO>>` | ✅ 200 |
| 7 | POST | `account/personal/amend` | Body:`updateAssetProfileTradingRequest` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 8 | GET | `account/upload_token` | QueryMap:`map` | `c<SuccessResponse<UploadTokenDTO>>` | 🔴 500 |
| 9 | GET | `master-data/banks` | QueryMap:`map` | `A<BankListReponse>` | ✅ 200 |
| 10 | PUT | `v2/account/bank/amend` | Body:`map` | `A<BaseResponseImpl>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getAmendBankStatus  [GET /v2/account/bank/amend]
curl -X GET "https://api-sekuritas.stockbit.com/v2/account/bank/amend" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# submitAmendBankData  [POST /v2/account/bank/amend]
curl -X POST "https://api-sekuritas.stockbit.com/v2/account/bank/amend" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<AmendBankSubmitParams>'   # JSON body

# getLivenessQuota  [GET /v2/account/liveness/quota]
curl -X GET "https://api-sekuritas.stockbit.com/v2/account/liveness/quota" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# submitLivenessAndGetScore  [POST /v2/account/liveness/result]
curl -X POST "https://api-sekuritas.stockbit.com/v2/account/liveness/result" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getLivenessLicense  [POST /v2/account/liveness/secret]
curl -X POST "https://api-sekuritas.stockbit.com/v2/account/liveness/secret" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getTradingProfileStatus  [GET account/personal]
curl -X GET "https://api-sekuritas.stockbit.com/account/personal" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# updateAssetData  [POST account/personal/amend]
curl -X POST "https://api-sekuritas.stockbit.com/account/personal/amend" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<UpdateAssetProfileTradingRequest>'   # JSON body

# getUploadToken  [GET account/upload_token]
curl -X GET "https://api-sekuritas.stockbit.com/account/upload_token?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getListBank  [GET master-data/banks]
curl -X GET "https://api-sekuritas.stockbit.com/master-data/banks?<map>=<Map<String, Boolean>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# changeSelectedAccountBank  [PUT v2/account/bank/amend]
curl -X PUT "https://api-sekuritas.stockbit.com/v2/account/bank/amend" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

```
</details>

## 93. `SecuritiesOAApi`  (7 endpoint)
<sub>com/stockbit/remote/api/SecuritiesOAApi.java · qualifier `SECURITIES_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `/v2/registration/pin/validate` | Body:`requestBody` | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 2 | GET | `v2/account/upload/url` | Query(src):`type`,`content_type`,`request_count` | `c<SuccessResponse<GoogleUploadTokenDTO>>` | 🟡 400 |
| 3 | GET | `v2/registration/bibit/access` | — | `c<SuccessResponse<BibitAccountAccessDTO>>` | ⚪ 404 |
| 4 | GET | `v2/registration/bibit/check` | — | `c<SuccessResponse<OABibitStatusDTO>>` | ✅ 200 |
| 5 | POST | `v2/registration/bibit/register` | Body:`map` | `c<SuccessResponse<BibitAccountValidationDTO>>` | ⊘ not tested (write) |
| 6 | GET | `v2/registration/check` | — | `c<SuccessResponse<Object>>` | ✅ 200 |
| 7 | GET | `v2/registration/upload/url` | QueryMap:`map` | `c<SuccessResponse<MarginTradingESignUploadURLDTO>>` | 🟡 400 |

<details><summary>cURL — semua endpoint</summary>

```bash
# validateNewPin  [POST /v2/registration/pin/validate]
curl -X POST "https://api-sekuritas.stockbit.com/v2/registration/pin/validate" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getGoogleUploadToken  [GET v2/account/upload/url]
curl -X GET "https://api-sekuritas.stockbit.com/v2/account/upload/url?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBibitAccountAccess  [GET v2/registration/bibit/access]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/bibit/access" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getBibitRegistrationStatus  [GET v2/registration/bibit/check]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/bibit/check" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# validateBibitAccess  [POST v2/registration/bibit/register]
curl -X POST "https://api-sekuritas.stockbit.com/v2/registration/bibit/register" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<Map<String, String>>'   # JSON body

# getSecuritiesStatus  [GET v2/registration/check]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/check" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getMarginTradingUploadURLToGCP  [GET v2/registration/upload/url]
curl -X GET "https://api-sekuritas.stockbit.com/v2/registration/upload/url?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 94. `TradingCommunityApi`  (4 endpoint)
<sub>com/stockbit/remote/api/TradingCommunityApi.java · qualifier `SECURITIES_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `remisier/affiliate/members` | QueryMap:`map` | `c<SuccessResponse<TradingCommunityDashboardDTO>>` | ⚪ 404 |
| 2 | POST | `remisier/referral/apply` | Body:`jsonObject` | `c<SuccessResponse<TradingCommunityApplyCodeDTO>>` | ⊘ not tested (write) |
| 3 | GET | `remisier/referral/status` | — | `c<SuccessResponse<TradingCommunityStatusDTO>>` | ⚪ 404 |
| 4 | GET | `remisier/referral/{code}` | Path:`code` | `c<SuccessResponse<TradingCommunityDTO>>` | ⚪ 404 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCommunityMembers  [GET remisier/affiliate/members]
curl -X GET "https://api-sekuritas.stockbit.com/remisier/affiliate/members?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# applyCommunityCode  [POST remisier/referral/apply]
curl -X POST "https://api-sekuritas.stockbit.com/remisier/referral/apply" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '<JsonObject>'   # JSON body

# getCommunityStatus  [GET remisier/referral/status]
curl -X GET "https://api-sekuritas.stockbit.com/remisier/referral/status" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getCommunityCode  [GET remisier/referral/{code}]
curl -X GET "https://api-sekuritas.stockbit.com/remisier/referral/{code}" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 95. `CacheTradingCommunityApi`  (1 endpoint)
<sub>com/stockbit/remote/api/CacheTradingCommunityApi.java · qualifier `SECURITIES_BASE_EXODUS`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `remisier/info` | — | `c<SuccessResponse<TradingCommunityInfoDTO>>` | ✅ 200 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getCommunityInfo  [GET remisier/info]
curl -X GET "https://api-sekuritas.stockbit.com/remisier/info" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

# ━━ HOST: SEKURITAS (e-IPO auth) — `https://api-sekuritas.stockbit.com` ━━

**Auth:** Bearer securities/trading token (PIN-gated)

## 96. `EIpoAuthLegacyApi`  (3 endpoint)
<sub>com/stockbit/remote/api/EIpoAuthLegacyApi.java · qualifier `EIPO_AUTH_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `auth/eipo/webview/link` | — | `c<SuccessResponse<EIpoCompanyLinkDTO>>` | ✅ 200 |
| 2 | GET | `partner/eipo/access_token` | Header:`str` | `c<SuccessResponse<EIpoTokenDTO>>` | 🔑 401 |
| 3 | GET | `partner/refresh_token` | Query:`token` · HeaderMap:`map` | `c<SuccessResponse<EIpoTokenDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getEIpoCompanyLink  [GET auth/eipo/webview/link]
curl -X GET "https://api-sekuritas.stockbit.com/auth/eipo/webview/link" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEIpoToken  [GET partner/eipo/access_token]
curl -X GET "https://api-sekuritas.stockbit.com/partner/eipo/access_token" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# refreshEIpoToken  [GET partner/refresh_token]
curl -X GET "https://api-sekuritas.stockbit.com/partner/refresh_token?token=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

```
</details>

# ━━ HOST: SEKURITAS (e-IPO) — `https://api-sekuritas.stockbit.com` ━━

**Auth:** Bearer securities/trading token (PIN-gated)

## 97. `EIpoLegacyApi`  (7 endpoint)
<sub>com/stockbit/remote/api/EIpoLegacyApi.java · qualifier `EIPO_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `eipo/company/detail` | Query:`emiten_code` | `c<SuccessResponse<EIpoCompanyDetailDTO>>` | 🔑 401 |
| 2 | GET | `eipo/company/unboxing` | Query:`emiten_code` | `c<SuccessResponse<EIpoUnboxingDTO>>` | 🟡 400 |
| 3 | POST | `eipo/order` | FieldMap:`map` · _Multipart_ | `c<SuccessResponse<EIpoCreateDTO>>` | ⊘ not tested (write) |
| 4 | GET | `eipo/order/detail` | Query:`emiten_code` | `c<SuccessResponse<EIpoOrderDetailDTO>>` | 🔑 401 |
| 5 | POST | `eipo/order/verify` | FieldMap:`map` · _Multipart_ | `c<SuccessResponse<Object>>` | ⊘ not tested (write) |
| 6 | GET | `eipo/rdn_balance` | — | `c<SuccessResponse<EIpoBalanceDTO>>` | 🔑 401 |
| 7 | GET | `eipo/status` | Query:`emiten_code` | `c<SuccessResponse<EIpoStatusDetailDTO>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getEIpoCompanyDetailNew  [GET eipo/company/detail]
curl -X GET "https://api-sekuritas.stockbit.com/eipo/company/detail?emiten_code=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEIpoUnboxing  [GET eipo/company/unboxing]
curl -X GET "https://api-sekuritas.stockbit.com/eipo/company/unboxing?emiten_code=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# createEIpoOrder  [POST eipo/order]
curl -X POST "https://api-sekuritas.stockbit.com/eipo/order" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEIpoOrderDetail  [GET eipo/order/detail]
curl -X GET "https://api-sekuritas.stockbit.com/eipo/order/detail?emiten_code=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# verifyEIpoOrder  [POST eipo/order/verify]
curl -X POST "https://api-sekuritas.stockbit.com/eipo/order/verify" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEIpoRdnBalance  [GET eipo/rdn_balance]
curl -X GET "https://api-sekuritas.stockbit.com/eipo/rdn_balance" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEIpoStatus  [GET eipo/status]
curl -X GET "https://api-sekuritas.stockbit.com/eipo/status?emiten_code=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

```
</details>

## 98. `EIpoApi`  (4 endpoint)
<sub>com/stockbit/remote/api/EIpoApi.java · qualifier `EIPO_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `auth/eipo/webview/link` | — | `c<SuccessResponse<EIpoCompanyLinkDTO>>` | ✅ 200 |
| 2 | GET | `eipo/social/company/detail` | Query:`emiten_code` | `c<SuccessResponse<EIpoCompanyDetailDTO>>` | 🟡 400 |
| 3 | GET | `eipo/social/company/list` | QueryMap:`map2` · HeaderMap:`map` | `c<SuccessResponse<List<EIpoDTO>>>` | 🟡 400 |
| 4 | GET | `eipo/social/company/status` | Query:`emiten_code` · HeaderMap:`map` | `c<SuccessResponse<EIpoCompanyStatusDTO>>` | 🔴 500 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getEIpoCompanyLink  [GET auth/eipo/webview/link]
curl -X GET "https://api-sekuritas.stockbit.com/auth/eipo/webview/link" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEIpoCompanyDetail  [GET eipo/social/company/detail]
curl -X GET "https://api-sekuritas.stockbit.com/eipo/social/company/detail?emiten_code=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"

# getEIpoCompanyList  [GET eipo/social/company/list]
curl -X GET "https://api-sekuritas.stockbit.com/eipo/social/company/list?<map>=<Map<String, String>>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

# getEIpoCompanyStatus  [GET eipo/social/company/status]
curl -X GET "https://api-sekuritas.stockbit.com/eipo/social/company/status?emiten_code=<String>" \
  -H "User-Agent: okhttp/4.12.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "X-Custom-Header: ..."   # @HeaderMap

```
</details>

# ━━ HOST: 3RD-PARTY SDK — `(vendor SDK)` ━━

**Auth:** see interceptor

## 99. `a`  (2 endpoint)
<sub>com/stockbit/lib/pocket/android/flipt/data/a.java · qualifier `(vendor)`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `evaluate/v1/batch` | Body:`fliptBatchRequestDataParam` | `A<FliptBatchEvaluateDTO>` | ⊘ not tested (write) |
| 2 | POST | `evaluate/v1/variant` | Body:`fliptRequestDataParam` | `A<FliptVariantDTO>` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# a  [POST evaluate/v1/batch]
curl -X POST "(vendor SDK)/evaluate/v1/batch" \
  -H "Content-Type: application/json" \
  -d '<FliptBatchRequestDataParam>'   # JSON body

# b  [POST evaluate/v1/variant]
curl -X POST "(vendor SDK)/evaluate/v1/variant" \
  -H "Content-Type: application/json" \
  -d '<FliptRequestDataParam>'   # JSON body

```
</details>

## 100. `a`  (1 endpoint)
<sub>com/midtrans/sdk/analytics/a.java · qualifier `(vendor)`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `/track` | Query:`str` | — | — (vendor/skip) |

<details><summary>cURL — semua endpoint</summary>

```bash
# f  [GET /track]
curl -X GET "(vendor SDK)/track?<map>=<String>"

```
</details>

# ━━ HOST: GIPHY (vendor) — `https://api.giphy.com` ━━

**Auth:** see interceptor

## 101. `GifsService`  (4 endpoint)
<sub>com/stockbit/remote/api/GifsService.java · qualifier `GIPHY_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `v1/gifs/search` | QueryMap:`map` | `A<GiphyResponse>` | — (vendor/skip) |
| 2 | GET | `v1/gifs/trending` | QueryMap:`map` | `A<GiphyResponse>` | — (vendor/skip) |
| 3 | GET | `v1/stickers/search` | QueryMap:`map` | `A<GiphyResponse>` | — (vendor/skip) |
| 4 | GET | `v1/stickers/trending` | QueryMap:`map` | `A<GiphyResponse>` | — (vendor/skip) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getGiphySearch  [GET v1/gifs/search]
curl -X GET "https://api.giphy.com/v1/gifs/search?<map>=<Map<String, String>>"

# getGiphyTrending  [GET v1/gifs/trending]
curl -X GET "https://api.giphy.com/v1/gifs/trending?<map>=<Map<String, String>>"

# getStickerSearch  [GET v1/stickers/search]
curl -X GET "https://api.giphy.com/v1/stickers/search?<map>=<Map<String, String>>"

# getStickerTrending  [GET v1/stickers/trending]
curl -X GET "https://api.giphy.com/v1/stickers/trending?<map>=<Map<String, String>>"

```
</details>

## 102. `GiphyApi`  (4 endpoint)
<sub>com/stockbit/remote/api/GiphyApi.java · qualifier `GIPHY_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `v1/gifs/search` | QueryMap:`map` | `A<ListGiphyDTO>` | — (vendor/skip) |
| 2 | GET | `v1/gifs/trending` | QueryMap:`map` | `A<ListGiphyDTO>` | — (vendor/skip) |
| 3 | GET | `v1/stickers/search` | QueryMap:`map` | `A<ListGiphyDTO>` | — (vendor/skip) |
| 4 | GET | `v1/stickers/trending` | QueryMap:`map` | `A<ListGiphyDTO>` | — (vendor/skip) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getGiphySearch  [GET v1/gifs/search]
curl -X GET "https://api.giphy.com/v1/gifs/search?<map>=<Map<String, String>>"

# getGiphyTrending  [GET v1/gifs/trending]
curl -X GET "https://api.giphy.com/v1/gifs/trending?<map>=<Map<String, String>>"

# getStickerSearch  [GET v1/stickers/search]
curl -X GET "https://api.giphy.com/v1/stickers/search?<map>=<Map<String, String>>"

# getStickerTrending  [GET v1/stickers/trending]
curl -X GET "https://api.giphy.com/v1/stickers/trending?<map>=<Map<String, String>>"

```
</details>

# ━━ HOST: MAS ONLINE (non-trading) — `https://api.masonline.id` ━━

**Auth:** Bearer securities (non-trading)

## 103. `TransferStockService`  (9 endpoint)
<sub>com/stockbit/remote/api/TransferStockService.java · qualifier `SECURITIES_BASE_NON_TRADING`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `stock-transfer/get-notification` | — | `A<Object>` | ⚪ 404 |
| 2 | GET | `stock-transfer/is-exist` | — | `A<IsExistResponse>` | 🔑 401 |
| 3 | GET | `stock-transfer/securities` | QueryMap:`map` | `A<SecuritiesListResponse>` | 🔑 401 |
| 4 | GET | `stock-transfer/transactions` | QueryMap:`map` | `A<TransactionListResponse>` | 🔑 401 |
| 5 | POST | `stock-transfer/transactions/cancel` | Body:`requestBody` | `A<BaseResponseImpl>` | ⊘ not tested (write) |
| 6 | GET | `stock-transfer/upload/token` | QueryMap:`map` | `A<GoogleUploadTokenSecuritiesResponse>` | 🔑 401 |
| 7 | GET | `stock-transfer/v2/form` | QueryMap:`map` | `A<TransferStockFormResponse>` | 🔑 401 |
| 8 | POST | `stock-transfer/v2/transactions` | Body:`requestBody` | `A<SaveStockTransferResponse>` | ⊘ not tested (write) |
| 9 | GET | `stock-transfer/v2/transactions/{id}` | Path:`str` | `A<TransferStockDetailResponse>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# getNotification  [GET stock-transfer/get-notification]
curl -X GET "https://api.masonline.id/stock-transfer/get-notification"

# getIsExist  [GET stock-transfer/is-exist]
curl -X GET "https://api.masonline.id/stock-transfer/is-exist"

# getListSecurities  [GET stock-transfer/securities]
curl -X GET "https://api.masonline.id/stock-transfer/securities?<map>=<HashMap<String, String>>"

# getListTransactions  [GET stock-transfer/transactions]
curl -X GET "https://api.masonline.id/stock-transfer/transactions?<map>=<HashMap<String, String>>"

# cancelRequest  [POST stock-transfer/transactions/cancel]
curl -X POST "https://api.masonline.id/stock-transfer/transactions/cancel" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getToken  [GET stock-transfer/upload/token]
curl -X GET "https://api.masonline.id/stock-transfer/upload/token?<map>=<HashMap<String, String>>"

# getMapping  [GET stock-transfer/v2/form]
curl -X GET "https://api.masonline.id/stock-transfer/v2/form?<map>=<HashMap<String, String>>"

# saveForm  [POST stock-transfer/v2/transactions]
curl -X POST "https://api.masonline.id/stock-transfer/v2/transactions" \
  -H "Content-Type: application/json" \
  -d '<RequestBody>'   # JSON body

# getDetailTransaction  [GET stock-transfer/v2/transactions/{id}]
curl -X GET "https://api.masonline.id/stock-transfer/v2/transactions/{id}"

```
</details>

## 104. `EstatementApi`  (3 endpoint)
<sub>com/stockbit/remote/api/EstatementApi.java · qualifier `SECURITIES_BASE_NON_TRADING`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `estatement/tax` | Query:`year` | `c<SuccessResponse<Object>>` | 🔑 401 |
| 2 | GET | `estatement/tax/year` | — | `c<SuccessResponse<List<Integer>>>` | 🔑 401 |
| 3 | GET | `estatement/transaction-history` | Query:`str` · Query:`str2` | `c<SuccessResponse<Object>>` | 🔑 401 |

<details><summary>cURL — semua endpoint</summary>

```bash
# requestEmailEstatement  [GET estatement/tax]
curl -X GET "https://api.masonline.id/estatement/tax?year=<int>"

# getYearList  [GET estatement/tax/year]
curl -X GET "https://api.masonline.id/estatement/tax/year"

# requestTransctionHistory  [GET estatement/transaction-history]
curl -X GET "https://api.masonline.id/estatement/transaction-history?<map>=<String>&<map>=<String>"

```
</details>

# ━━ HOST: MIDTRANS Core (payment vendor) — `https://api.midtrans.com` ━━

**Auth:** Midtrans client/server key (vendor)

## 105. `b`  (2 endpoint)
<sub>A/a/a/a/a/b.java · qualifier `(vendor)`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `charge` | Body:`tokenRequestModel` | — | ⊘ not tested (write) |
| 2 | POST | `users/{user_id}/tokens` | Path:`user_id` · Body:`list` | — | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# g  [POST charge]
curl -X POST "https://api.midtrans.com/charge" \
  -H "Content-Type: application/json" \
  -d '<TokenRequestModel>'   # JSON body

# h  [POST users/{user_id}/tokens]
curl -X POST "https://api.midtrans.com/users/{user_id}/tokens" \
  -H "Content-Type: application/json" \
  -d '<List<SaveCardRequest>>'   # JSON body

```
</details>

# ━━ HOST: MIDTRANS Snap (payment vendor; sandbox: app.sandbox.midtrans.com) — `https://app.midtrans.com` ━━

**Auth:** Midtrans client/server key (vendor)

## 106. `g`  (13 endpoint)
<sub>A/a/a/a/a/g.java · qualifier `(vendor)`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`bankTransferPaymentRequest` | — | ⊘ not tested (write) |
| 2 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`creditCardPaymentRequest` | — | ⊘ not tested (write) |
| 3 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`telkomselEcashPaymentRequest` | — | ⊘ not tested (write) |
| 4 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`shopeePayQrisPaymentRequest` | — | ⊘ not tested (write) |
| 5 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`basePaymentRequest` | — | ⊘ not tested (write) |
| 6 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`indosatDompetkuPaymentRequest` | — | ⊘ not tested (write) |
| 7 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`shopeePayPaymentRequest` | — | ⊘ not tested (write) |
| 8 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`newMandiriClickPayPaymentRequest` | — | ⊘ not tested (write) |
| 9 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`klikBCAPaymentRequest` | — | ⊘ not tested (write) |
| 10 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`danamonOnlinePaymentRequest` | — | ⊘ not tested (write) |
| 11 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`gCIPaymentRequest` | — | ⊘ not tested (write) |
| 12 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`uobEzpayPaymentRequest` | — | ⊘ not tested (write) |
| 13 | POST | `v1/transactions/{snap_token}/pay` | Path:`snap_token` · Body:`goPayPaymentRequest` | — | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# b  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<BankTransferPaymentRequest>'   # JSON body

# c  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<CreditCardPaymentRequest>'   # JSON body

# e  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<TelkomselEcashPaymentRequest>'   # JSON body

# g  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<ShopeePayQrisPaymentRequest>'   # JSON body

# h  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<BasePaymentRequest>'   # JSON body

# i  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<IndosatDompetkuPaymentRequest>'   # JSON body

# j  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<ShopeePayPaymentRequest>'   # JSON body

# k  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<NewMandiriClickPayPaymentRequest>'   # JSON body

# l  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<KlikBCAPaymentRequest>'   # JSON body

# m  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<DanamonOnlinePaymentRequest>'   # JSON body

# n  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<GCIPaymentRequest>'   # JSON body

# o  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<UobEzpayPaymentRequest>'   # JSON body

# p  [POST v1/transactions/{snap_token}/pay]
curl -X POST "https://app.midtrans.com/v1/transactions/{snap_token}/pay" \
  -H "Content-Type: application/json" \
  -d '<GoPayPaymentRequest>'   # JSON body

```
</details>

# ━━ HOST: ONEKYC / eKYC vendor — `(eKYC vendor host)` ━━

**Auth:** see interceptor

## 107. `InterfaceC4089i`  (10 endpoint)
<sub>b0/InterfaceC4089i.java · qualifier `(vendor)`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | POST | `/onekyc/v1/flow/execute/state` | Body:`—` · Header:`x-onekyc-token` · Header:`x-onekyc-partner` | `UnifiedKycResponse$DetailConfirmationApiModel` | ⊘ not tested (write) |
| 2 | PUT | `/onekyc/v1/submissions/forms/{formId}` | Path:`formId` · Body:`—` · Header:`x-onekyc-token` · Header:`x-onekyc-partner` | `UnifiedKycResponse$SlikFormResponseApiModel` | ⊘ not tested (write) |
| 3 | POST | `/{route}/v1/challenge/{challengeId}/submit` | Path:`route` · Path:`challengeId` · Body:`—` · Header:`x-onekyc-token` · Header:`x-onekyc-partner` · Header:`x-onekyc-session-id` | `UnifiedKycResponse$ChallengeSubmissionResponseApiModel` | ⊘ not tested (write) |
| 4 | POST | `/{route}/v2/challenge` | Path:`route` · Header:`x-onekyc-token` · Header:`x-onekyc-partner` · Header:`x-onekyc-session-id` · Header:`x-partner-session-id` | `UnifiedKycResponse$CreateChallengeApiModel` | ⊘ not tested (write) |
| 5 | POST | `coe/v1/consent/initiate` | Header:`x-onekyc-token` · Header:`x-consent-flow` | `UnifiedKycResponse$OneKycResponse<UnifiedKycResponse$InitiateConsentData>` | ⊘ not tested (write) |
| 6 | POST | `coe/v1/consent/{consentId}/submit` | Path:`consentId` · Body:`—` · Header:`x-onekyc-token` | `UnifiedKycResponse$OneKycResponse<Object>` | ⊘ not tested (write) |
| 7 | PUT | `coe/v1/submissions/urls` | Body:`—` · Header:`x-onekyc-token` · Header:`x-partner-session-id` · Header:`x-sdk-session-id` | `UnifiedKycResponse$OneKycResponse<UnifiedKycResponse$OneKycSubmissionData>` | ⊘ not tested (write) |
| 8 | POST | `onekyc/v1/consent/{consentId}/submit` | Path:`consentId` · Body:`—` · Header:`x-onekyc-token` · Header:`x-onekyc-partner` | `UnifiedKycResponse$SubmitConsentApiModel` | ⊘ not tested (write) |
| 9 | POST | `onekyc/v1/flow/next` | Header:`x-onekyc-token` · Header:`x-onekyc-partner` | `UnifiedKycResponse$OneKycNextFlowModel` | ⊘ not tested (write) |
| 10 | PUT | `onekyc/v1/submissions/urls` | Body:`—` · Header:`x-onekyc-token` · Header:`x-onekyc-partner` · Header:`x-partner-session-id` · Header:`x-onekyc-session-id` | `UnifiedKycResponse$SubmissionUrlApiModel` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# d  [POST /onekyc/v1/flow/execute/state]
curl -X POST "(eKYC vendor host)/onekyc/v1/flow/execute/state" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-onekyc-partner: $X_ONEKYC_PARTNER" \
  -H "Content-Type: application/json" \
  -d '<?>'   # JSON body

# u  [PUT /onekyc/v1/submissions/forms/{formId}]
curl -X PUT "(eKYC vendor host)/onekyc/v1/submissions/forms/{formId}" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-onekyc-partner: $X_ONEKYC_PARTNER" \
  -H "Content-Type: application/json" \
  -d '<?>'   # JSON body

# s  [POST /{route}/v1/challenge/{challengeId}/submit]
curl -X POST "(eKYC vendor host)/{route}/v1/challenge/{challengeId}/submit" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-onekyc-partner: $X_ONEKYC_PARTNER" \
  -H "x-onekyc-session-id: $X_ONEKYC_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '<?>'   # JSON body

# k  [POST /{route}/v2/challenge]
curl -X POST "(eKYC vendor host)/{route}/v2/challenge" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-onekyc-partner: $X_ONEKYC_PARTNER" \
  -H "x-onekyc-session-id: $X_ONEKYC_SESSION_ID" \
  -H "x-partner-session-id: $X_PARTNER_SESSION_ID"

# p  [POST coe/v1/consent/initiate]
curl -X POST "(eKYC vendor host)/coe/v1/consent/initiate" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-consent-flow: $X_CONSENT_FLOW"

# i  [POST coe/v1/consent/{consentId}/submit]
curl -X POST "(eKYC vendor host)/coe/v1/consent/{consentId}/submit" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<?>'   # JSON body

# r  [PUT coe/v1/submissions/urls]
curl -X PUT "(eKYC vendor host)/coe/v1/submissions/urls" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-partner-session-id: $X_PARTNER_SESSION_ID" \
  -H "x-sdk-session-id: $X_SDK_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '<?>'   # JSON body

# n  [POST onekyc/v1/consent/{consentId}/submit]
curl -X POST "(eKYC vendor host)/onekyc/v1/consent/{consentId}/submit" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-onekyc-partner: $X_ONEKYC_PARTNER" \
  -H "Content-Type: application/json" \
  -d '<?>'   # JSON body

# f  [POST onekyc/v1/flow/next]
curl -X POST "(eKYC vendor host)/onekyc/v1/flow/next" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-onekyc-partner: $X_ONEKYC_PARTNER"

# c  [PUT onekyc/v1/submissions/urls]
curl -X PUT "(eKYC vendor host)/onekyc/v1/submissions/urls" \
  -H "x-onekyc-token: $X_ONEKYC_TOKEN" \
  -H "x-onekyc-partner: $X_ONEKYC_PARTNER" \
  -H "x-partner-session-id: $X_PARTNER_SESSION_ID" \
  -H "x-onekyc-session-id: $X_ONEKYC_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '<?>'   # JSON body

```
</details>

## 108. `InterfaceC4082b`  (3 endpoint)
<sub>b0/InterfaceC4082b.java · qualifier `(vendor)`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | PATCH | `v1/users/kyc/edd-info` | Body:`kycDueDiligenceSubmissionData` | `KycDueDiligenceResponse` | ⊘ not tested (write) |
| 2 | PATCH | `v2/users/kyc/confirm` | Body:`kycConfirmRequestV2` · Header:`x-onekyc-session-id` | — | ⊘ not tested (write) |
| 3 | POST | `v2/users/kyc/url` | Body:`kycUrlRequest` | `KycUrlResponse` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# c  [PATCH v1/users/kyc/edd-info]
curl -X PATCH "(eKYC vendor host)/v1/users/kyc/edd-info" \
  -H "Content-Type: application/json" \
  -d '<KycDueDiligenceSubmissionData>'   # JSON body

# b  [PATCH v2/users/kyc/confirm]
curl -X PATCH "(eKYC vendor host)/v2/users/kyc/confirm" \
  -H "x-onekyc-session-id: $X_ONEKYC_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '<KycConfirmRequestV2>'   # JSON body

# a  [POST v2/users/kyc/url]
curl -X POST "(eKYC vendor host)/v2/users/kyc/url" \
  -H "Content-Type: application/json" \
  -d '<KycUrlRequest>'   # JSON body

```
</details>

## 109. `InterfaceC4088h`  (1 endpoint)
<sub>b0/InterfaceC4088h.java · qualifier `(vendor)`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | PUT | `onekyc/v1/submissions/urls` | Body:`—` · Header:`x-onekyc-partner` · Header:`x-onekyc-session-id` | `UnifiedKycResponse$SubmissionUrlApiModel` | ⊘ not tested (write) |

<details><summary>cURL — semua endpoint</summary>

```bash
# c  [PUT onekyc/v1/submissions/urls]
curl -X PUT "(eKYC vendor host)/onekyc/v1/submissions/urls" \
  -H "x-onekyc-partner: $X_ONEKYC_PARTNER" \
  -H "x-onekyc-session-id: $X_ONEKYC_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '<?>'   # JSON body

```
</details>

# ━━ HOST: YOUTUBE (vendor) — `https://www.youtube.com` ━━

**Auth:** see interceptor

## 110. `ChatYoutubeApi`  (1 endpoint)
<sub>com/stockbit/remote/api/chat/ChatYoutubeApi.java · qualifier `YOUTUBE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `oembed` | QueryMap:`map` | `A<YoutubeMetaDTO>` | — (vendor/skip) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getMetadata  [GET oembed]
curl -X GET "https://www.youtube.com/oembed?<map>=<Map<String, String>>"

```
</details>

## 111. `YoutubeService`  (1 endpoint)
<sub>com/stockbit/remote/api/YoutubeService.java · qualifier `YOUTUBE_BASE`</sub>

| # | Method | Path | Dependencies (params) | → Response | Live test |
|---|---|---|---|---|---|
| 1 | GET | `oembed` | QueryMap:`map` | `A<YoutubeMetaResponseData>` | — (vendor/skip) |

<details><summary>cURL — semua endpoint</summary>

```bash
# getEmbed  [GET oembed]
curl -X GET "https://www.youtube.com/oembed?<map>=<Map<String, String>>"

```
</details>
# Appendix A — Auth & MFA Login Flow (sample request + sample response, terverifikasi live)

> Diverifikasi end-to-end pada 2026-05-30 terhadap server produksi. Semua di host **`exodus.stockbit.com`**.
> Nilai sensitif diredaksi: `$STOCKBIT_PASSWORD`, kode OTP, dan token JWT dipotong (`eyJ...<redacted>`).
> **Koreksi penting:** host login = `exodus.stockbit.com` (BUKAN `api.stockbit.com/v2.4` seperti di File 04 — host legacy menolak dengan *"Silahkan update aplikasi"*). `player_id` (UUID device) **wajib**; bila `null` → `400 INVALID_PARAMETER`. Tidak ada request-signing (`signature` boleh `""`).

Header global yang dipakai di semua langkah:
```
-H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" -H "Content-Type: application/json"
```

## Diagram alur

```
login/v6/username ──(new_device.multi_factor: login_token + verification_token)
   └─> mfa/.../challenge/start ──(next_challenge=CHALLENGE_OTP, channels=[EMAIL])
        └─> mfa/.../challenge/otp/send  (channel=CHANNEL_EMAIL)     → OTP ke email
             └─> mfa/.../challenge/otp/verify (otp)                 → next=CHALLENGE_OTP (channels=[WHATSAPP,SMS])
                  └─> mfa/.../challenge/otp/send (channel=CHANNEL_WHATSAPP) → OTP ke HP
                       └─> mfa/.../challenge/otp/verify (otp)       → next=CHALLENGE_FINISH
                            └─> login/v6/new-device/verify (multi_factor.login_token) → user + access token
RE-LOGIN player_id sama → langsung token (data.login.token_data), tanpa MFA
```

---

## A.1 — Login username/password  → memicu MFA perangkat baru

`POST /login/v6/username`  · Auth: none · Body `LoginUserNamePasswordDataParam`

```bash
curl -X POST "https://exodus.stockbit.com/login/v6/username" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '{"user":"nkurniasih824@gmail.com","password":"'"$STOCKBIT_PASSWORD"'","player_id":"2292F1CB-37AD-42C7-942E-FBD6C0F26669","signature":""}'
```

**200 OK** (perangkat belum dikenal → minta MFA):
```json
{
  "message": "You have been successfully logged in",
  "data": {
    "new_device": {
      "multi_factor": {
        "login_token": "3c0a3ff6-cd23-4257-b9f6-7ed6bafafe9f",
        "verification_token": "2da3c70d-da18-47b3-b842-c2ed58aa225f"
      }
    }
  }
}
```

**Mode gagal yang teramati:**
```jsonc
// player_id = null  →  HTTP 400
{"message":"Permintaan tidak valid","error_type":"INVALID_PARAMETER"}
// dikirim ke host legacy api.stockbit.com/v2.4  →  HTTP 200 tapi ditolak gate versi
{"error":"InvalidParameter","message":"Silahkan update aplikasi kamu ke versi terbaru dan nikmati fitur yang lebih stabil"}
```

## A.2 — Start MFA challenge

`POST /mfa/verification/v1/challenge/start` · Body `{verification_token}`

```bash
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/start" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '{"verification_token":"2da3c70d-da18-47b3-b842-c2ed58aa225f"}'
```

**200 OK:**
```json
{
  "message": "Start challenge berhasil",
  "data": {
    "next_challenge": "CHALLENGE_OTP",
    "supporting_data": {
      "otp": {
        "channels": [{ "channel": "CHANNEL_EMAIL", "target": "nku**********@gmail.com" }],
        "default_channel": "CHANNEL_EMAIL",
        "show_forgot_phone_button": false
      }
    }
  }
}
```

## A.3 — Kirim OTP #1 (email)

`POST /mfa/verification/v1/challenge/otp/send` · Body `{verification_token, channel}`

```bash
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/otp/send" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '{"verification_token":"2da3c70d-da18-47b3-b842-c2ed58aa225f","channel":"CHANNEL_EMAIL"}'
```

**200 OK:**
```json
{"message":"OTP Berhasil terkirim","data":{"channel":"CHANNEL_EMAIL","target":"nku**********@gmail.com","next_attempt_in":60}}
```

## A.4 — Verifikasi OTP #1 (email) → muncul challenge ke-2

`POST /mfa/verification/v1/challenge/otp/verify` · Body `{verification_token, otp}`

```bash
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/otp/verify" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '{"verification_token":"2da3c70d-da18-47b3-b842-c2ed58aa225f","otp":"<OTP_EMAIL>"}'
```

**200 OK** (MFA 2-lapis: lanjut OTP ke nomor HP):
```json
{
  "message": "Verifikasi OTP sukses",
  "data": {
    "next_challenge": "CHALLENGE_OTP",
    "supporting_data": {
      "otp": {
        "channels": [
          { "channel": "CHANNEL_WHATSAPP", "target": "628*******771" },
          { "channel": "CHANNEL_SMS", "target": "628*******771" }
        ],
        "default_channel": "CHANNEL_WHATSAPP",
        "show_forgot_phone_button": true
      }
    }
  }
}
```

## A.5 — Kirim OTP #2 (WhatsApp)

`POST /mfa/verification/v1/challenge/otp/send` · Body `{verification_token, channel}`

```bash
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/otp/send" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '{"verification_token":"2da3c70d-da18-47b3-b842-c2ed58aa225f","channel":"CHANNEL_WHATSAPP"}'
```

**200 OK:**
```json
{"message":"OTP Berhasil terkirim","data":{"channel":"CHANNEL_WHATSAPP","target":"628*******771","next_attempt_in":60}}
```

## A.6 — Verifikasi OTP #2 (WhatsApp) → CHALLENGE_FINISH

`POST /mfa/verification/v1/challenge/otp/verify` · Body `{verification_token, otp}`

```bash
curl -X POST "https://exodus.stockbit.com/mfa/verification/v1/challenge/otp/verify" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '{"verification_token":"2da3c70d-da18-47b3-b842-c2ed58aa225f","otp":"<OTP_WHATSAPP>"}'
```

**200 OK** (semua challenge selesai):
```json
{"message":"Verifikasi OTP sukses","data":{"next_challenge":"CHALLENGE_FINISH","supporting_data":{}}}
```

## A.7 — Selesaikan login perangkat baru → access token

`POST /login/v6/new-device/verify` · Body `VerifyNewDeviceLoginDataParam` = `{multi_factor:{login_token}, trusted_device?}`

```bash
curl -X POST "https://exodus.stockbit.com/login/v6/new-device/verify" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '{"multi_factor":{"login_token":"3c0a3ff6-cd23-4257-b9f6-7ed6bafafe9f"}}'
```

**200 OK:**
```json
{
  "message": "You have been successfully logged in",
  "data": {
    "user": {
      "id": 3780805, "username": "niaben", "email": "nkurniasih824@gmail.com",
      "avatar": "https://avatar.stockbit.com/female/ToyFaces_Colored_BG_9-min.png",
      "country": "ID", "sns": {"facebook": false, "apple": false, "google": true},
      "has_password_been_set": true, "is_phone_verified": true, "is_verified": true,
      "privilege": {"name": "PRIVILEGE_MEMBER", "code": 0},
      "watchlist_id": 7174647, "exchange": "ID"
    },
    "access": { "token": "eyJhbGciOiJSUzI1NiIs...<redacted JWT>" }
  }
}
```

> `login_token` **sekali pakai**. Memanggil ulang langkah ini → `{"message":"Sesi kamu telah berakhir. Silahkan coba lagi.","error_type":"INVALID_MFA_SESSION"}`.

## A.8 — Re-login (perangkat sudah dikenal) → token langsung tanpa MFA

Kirim ulang `login/v6/username` dengan **`player_id` yang sama**. Struktur respons berubah dari `data.new_device` → `data.login` dan berisi token + refresh.

```bash
curl -X POST "https://exodus.stockbit.com/login/v6/username" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id" \
  -H "Content-Type: application/json" \
  -d '{"user":"nkurniasih824@gmail.com","password":"'"$STOCKBIT_PASSWORD"'","player_id":"2292F1CB-37AD-42C7-942E-FBD6C0F26669","signature":""}'
```

**200 OK:**
```json
{
  "message": "You have been successfully logged in",
  "data": {
    "login": {
      "user": { "id": 3780805, "username": "niaben", "email": "nkurniasih824@gmail.com",
                "is_verified": true, "privilege": {"name": "PRIVILEGE_MEMBER", "code": 0},
                "watchlist_id": 7174647, "exchange": "ID" },
      "token_data": {
        "access":  { "token": "eyJhbGciOiJSUzI1NiIs...<redacted>", "expired_at": "2026-05-31T09:52:27Z" },
        "refresh": { "token": "eyJhbGciOiJSUzI1NiIs...<redacted>", "expired_at": "2026-06-06T09:52:27Z" }
      },
      "support": { "id": "TlisiCoN-WEHn-9Oyx-I5M9eDtsOyqD" }
    }
  }
}
```

JWT access payload (hasil decode bagian `data`):
```json
{ "use":"niaben", "ema":"nkurniasih824@gmail.com", "ful":"Nia Kurniasih",
  "dvc":"f4f20993837a2bbd61a2fec250553e93", "did":"android", "uid":3780805, "cou":"ID",
  "iss":"STOCKBIT", "ver":"v1", "exp":1780221147 }
```
> Access token berlaku ~24 jam; refresh ~7 hari. Gunakan refresh token via `POST /login/refresh` (lihat `AuthApi.getRefreshToken`, header `@HeaderMap`).

## A.9 — Verifikasi token (contoh endpoint terautentikasi)

```bash
# dengan token → 200
curl -X GET "https://exodus.stockbit.com/user/credential/v1/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"
```
```json
{"message":"success","data":{"change_password":"CHANGE_PASSWORD_STATUS_NONE"}}
```

```bash
curl -X GET "https://exodus.stockbit.com/user/avatar/collection" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android" -H "Accept-Language: id"
```
```json
{"message":"Avatar collection successfully retrieved","data":[
  {"order":0,"file":"male/ToyFaces_Colored_BG_29-min.png","group":"GROUP_TYPE_MALE"}, ...]}
```

```bash
# TANPA token → 401 (membuktikan auth ditegakkan)
curl -i -X GET "https://exodus.stockbit.com/user/credential/v1/status" \
  -H "X-AppVersion: 3.21.0" -H "X-Platform: android"
# HTTP/2 401
```

---

# Appendix B — Live GET Validation Report (read-only)

> Diverifikasi 372 endpoint **GET** host-Stockbit terhadap server produksi pada 2026-05-30 memakai access token social (uid 3780805). Endpoint POST/PUT/PATCH/DELETE **tidak dieksekusi** (mutasi akun nyata).

## B.0 Temuan kritis — `User-Agent` wajib

Semua request tanpa `User-Agent` app ditolak Cloudflare: **`HTTP 403`, body `error code: 1010`**. Dengan `-A "okhttp/4.12.0"` request lolos. Karena itu seluruh template cURL di dokumen ini sudah ditambahi `-H "User-Agent: okhttp/4.12.0"`.

| | Python-urllib UA | okhttp/4.12.0 UA |
|---|---|---|
| `GET /user/credential/v1/status` | `403` (1010) | `200` ✅ |

## B.1 Distribusi status (372 GET)

| HTTP | Jumlah | Arti |
|---|---|---|
| 200 | 197 | ✅ sukses — endpoint & cURL valid |
| 401 | 76 | butuh **token securities** (PIN-gated), bukan token social |
| 400 | 67 | endpoint ada; perlu nilai param valid (cURL lengkap, data uji kurang) |
| 404 | 13 | tidak ada data untuk nilai uji / route dinamis @Url |
| 500 | 11 | server error utk input uji (mis. exchange/symbol salah) |
| 403 | 7 | akses ditolak utk resource uji / butuh konteks (virtual-trading, grup) |
| 429 | 1 | rate-limited (retry) |

## B.2 Per host

| Host | Hasil |
|---|---|
| EXODUS | `200`×179 · `400`×56 · `500`×9 · `403`×7 · `404`×3 · `429`×1 |
| CARINA | `401`×61 · `200`×4 · `404`×3 · `400`×1 |
| SEKURITAS | `200`×12 · `400`×10 · `404`×6 · `401`×6 · `500`×2 |
| MASONLINE | `401`×9 · `404`×1 |
| LEGACY | `200`×2 |

**Interpretasi:** host **EXODUS** (token social) mayoritas `200`. Host **CARINA / SEKURITAS / MASONLINE** mayoritas `401 "Akses token kedaluwarsa"` karena butuh **token securities/trading terpisah** (lihat §2 tier auth) — bukan kekurangan cURL.

## B.3 Endpoint @Url dinamis (bukan path tetap)

Beberapa method memakai `@Url`/`@Path(encoded)` sehingga path final dibentuk runtime — string `{url}`/`{url}/{desired_type}` di tabel BUKAN endpoint literal:
- `SecuritiesOAService` / `SecuritiesOpeningAccountApi` → `{url}`, `{url}/{desired_type}` (URL penuh dari response sebelumnya)
Panggil dengan URL absolut yang diberikan server, bukan string literal di atas.

## B.4 Contoh endpoint terverifikasi `200 OK` (197 total)

```
GET user/v2/setting/change/status
GET tnc/v2/get
GET user/v2/discovery/trending
GET user/credential/v1/status
GET user/profile/{username}
GET user/verification/status
GET corpaction/{symbol}
GET analyst-ratings/{symbol}/consensus
GET analyst-ratings/{symbol}
GET comparison/v2/{symbol}/competitors
GET emitten/{symbol}/info
GET emitten/{symbol}/info
GET /keystats/ratio/v1/{symbol}
GET /company-price-feed/price-performance/{symbol}
GET emitten/{symbol}/profile
GET research/company/{symbol}
GET emitten-metadata/subsidiary/{symbol}
GET corpaction/dividend
GET corpaction/status
GET corpaction/stock_dividend
GET findata-view/foreign-domestic/v1/chart-data/{symbol}
GET findata-view/foreign-domestic/v1/period-ranges/{symbol}
GET corpaction/{symbol}/bonus
GET corpaction/{symbol}/rups
GET corpaction/{symbol}/reversesplit
GET corpaction/{symbol}/rightissue
GET corpaction/{symbol}/stocksplit
GET corpaction/{symbol}/tenderoffer
GET corpaction/{symbol}/warrant
GET emitten/{symbol}/profile
GET oms/auth/maintenance/status
GET user/avatar/collection
GET user/blocked
GET user/profile/{username}
GET tnc/v2/get
GET verified-badge/user/{user_id}
GET stream/v2/uploadtoken
GET notes
GET stream/v3/symbol/{symbol}/pinned
GET stream/v3
```
… dan 157 lainnya.

## B.5 Kesimpulan kelengkapan cURL

- **cURL valid & lengkap** untuk semua GET host-EXODUS (197/372 `200`; sisanya `400/404/500` murni karena nilai param/akses uji, bukan struktur cURL).
- **Diperbaiki di dokumen:** (1) ditambah header wajib `User-Agent: okhttp/4.12.0` ke semua template; (2) catatan tier **token securities** untuk host carina/sekuritas/masonline; (3) catatan endpoint `@Url` dinamis.
- POST/PUT/PATCH/DELETE tidak diuji sesuai batas read-only (mencegah order/withdraw/transfer nyata).
---


---


---


---

# Appendix C — Query Param dari Source + Re-test (67 endpoint GET yang semula `400`)

> Key digali dari `Remote*DataSourceImpl`/repository + pesan server; **nilai** enum diverifikasi empiris (read-only). Hasil: **49/67 → `200`**. Endpoint chained ditandai ⛓ (lihat Appendix D).

**Pola nilai:** enum market-data = **INTEGER** (`1`) · `timeframe`/`time_interval` = kode huruf-kecil (`1d`,`1m`) · `notification/.../status` butuh header **`X-DeviceID`**. Sumber kebenaran key = source (mis. `insider/majorholder/ownership` key asli `insider`, bukan `insider_id`).

| Endpoint | Query/Header terverifikasi | Re-test |
|---|---|---|
| `order-trade/broker/activity-chart` | `?brokers_code=YP&symbols=BBCA&to=2024-12-31&market_board=1&investor_type=1&period=1` | ✅ 200 |
| `order-trade/broker/activity/historical` | `?period=1&broker_codes=YP&symbols=BBCA&market_board=1&investor_type=1&transaction_type=1&interval=1&pagination.page=1&pagination.limit=10` | ✅ 200 |
| `order-trade/broker/activity` | `?broker_code=YP&to=2024-12-31&transaction_type=1&market_board=1&investor_type=1&period=1` | ✅ 200 |
| `charts/{symbol}` | `?timeframe=1d` | ✅ 200 |
| `chat/v2/rooms` | `?limit=10` | ✅ 200 |
| `chat/v2/rooms/type/invited` | `?limit=10` | ✅ 200 |
| `chat/s3/policy` | `?filename=test.jpg` | ✅ 200 |
| `chat/v2/groups/members/suggestions/contacts` | `?limit=10` | ✅ 200 |
| `chat/v2/groups/members/suggestions` | `?limit=10` | ✅ 200 |
| `chat/v3/user/search` | `?keyword=niaben&page=1&limit=10` | ✅ 200 |
| `chat/v2/rooms` | `?limit=10` | ✅ 200 |
| `chat/s3/policy` | `?filename=test.jpg` | ✅ 200 |
| `order-trade/running-trade/chart/{symbol}` | `?broker_code=YP&to=2024-12-31&period=1&market_board=1&investor_type=1` | ✅ 200 |
| `charts/{symbol}/daily` | `?timeframe=1D` | ✅ 200 |
| `chartbit/token/mobile` | `?theme=light&symbol=BBCA` | ✅ 200 |
| `fundachart/v2/{symbol}/financials` | `?data_type=1&report=1` | ✅ 200 |
| `findata-view/v2/financials/{symbol}` | `?data_type=1&report_type=1&statement_type=1&is_percentage=false` | ✅ 200 |
| `company-price-feed/prices` | `?stock_code=BBCA` | ✅ 200 |
| `comparison/v2/ratios` | `?symbol=BBCA` | ✅ 200 |
| `corpaction/{symbol}/stock_conversion` | `?page=1&limit=10` | ✅ 200 |
| `order-trade/running-trade` | `?symbols=BBCA&order_by=1&sort=1` | ✅ 200 |
| `seasonality/{company_symbol}` | `?year=2024` | ✅ 200 |
| `seasonality/{company_symbol}/years` | — | ✅ 200 |
| `order-trade/trade-book` | `?symbol=BBCA&group_by=1&sort_by=1&sort_direction=1&time_interval=1&to=2024-12-31` | ✅ 200 |
| `order-trade/trade-book/chart` | `?symbol=BBCA&time_interval=1m&to=2024-12-31` | ✅ 200 |
| `findata-view/marketdetectors/activity/{code}/detail` | `?page=1&limit=10` · ⛓ {code}=kode broker valid dari GET findata-view/marketdetectors/brokers (field data[].code, mis. AD) | ✅ 200 |
| `findata-view/marketdetectors/brokers` | `?limit=10&page=1` | ✅ 200 |
| `chartbit/token/mobile` | `?symbol=BBCA` | ✅ 200 |
| `fundachart/{symbol}/financials` | `?data_type=1&report=1` | ✅ 200 |
| `findata-view/v2/financials/{symbol}` | `?data_type=1&report_type=1&statement_type=1&is_percentage=false` | ✅ 200 |
| `charts/{symbol}/daily` | `?timeframe=1` | ✅ 200 |
| `comparison/v2/ratios` | `?symbol=BBCA` | ✅ 200 |
| `insider/majorholder/ownership` | `?insider=1000000439&page=1` · ⛓ insider_id dari GET insider/company/majorholder?symbol=BBCA (field movement[].id) | ✅ 200 |
| `live-stream/event` | `?page=1&limit=10` | ✅ 200 |
| `notification/v2/push-notification/status` | HEADER `X-DeviceID: f4f20993837a2bbd61a2fec250553e93` | ✅ 200 |
| `order-trade/broker/distribution` | `?symbol=BBCA` | ✅ 200 |
| `order-trade/order-queue` | `?stock_code=BBCA&board_type=1&data_type=1&market_board=1&investor_type=1&order_status=1&period=1&action_type=1&limit=10` | ✅ 200 |
| `company-price-feed/trade-book` | `?symbol=BBCA&group_by=1&sort_by=1&sort_direction=1&time_interval=1&to=2024-12-31` | ✅ 200 |
| `company-price-feed/running-trade` | `?symbol=BBCA&order_by=1` | ✅ 200 |
| `company-price-feed/v2/running-trade` | `?symbol=BBCA&order_by=1` | ✅ 200 |
| `request-verified/upload-token` | `?type=1` | ✅ 200 |
| `screener/templates/{id}` | `?type=1` | ✅ 200 |
| `watchlist/search/company` | `?keyword=BBCA&watchlist_id=7174647&page=1&limit=10` | ✅ 200 |
| `seasonality/{company_symbol}` | `?year=2024` | ✅ 200 |
| `seasonality/{company_symbol}/years` | — | ✅ 200 |
| `sharetrade/target` | `?limit=10` | ✅ 200 |
| `watchlist/suggestion/company` | `?watchlist_id=7174647` | ✅ 200 |
| `watchlist/{watchlist_id}` | `?limit=10` | ✅ 200 |
| `watchlist/{watchlist_id}` | `?limit=10` | ✅ 200 |
| `chat/v2/personal/room/{room_id}` | — · ⛓ {room_id} = user id lawan chat (dari GET chat/v3/user/search → data[].id) | 🟡 400 |
| `eipo/social/company/detail` | `?emiten_code=1` · ⛓ emiten_code dari GET eipo/social/company/list → data[].emiten_code | 🟡 400 |
| `eipo/social/company/list` | — | 🟡 400 |
| `eipo/company/unboxing` | `?emiten_code=1` · ⛓ emiten_code dari GET eipo/social/company/list → data[].emiten_code | 🟡 400 |
| `v2/account/upload/url` | `?type=1&content_type=1&request_count=1` | 🟡 400 |
| `v2/registration/upload/url` | — | 🟡 400 |
| `v2/account/upload/url` | — | 🟡 400 |
| `/v2/account/upload/token` | — | 🟡 400 |
| `v3/registration/form/{version}` | — | 🟡 400 |
| `v2/registration/upload/presign` | — | 🟡 400 |
| `v2/registration/upload/token` | — | 🟡 400 |
| `stream/announcement/{value}` | — | 🟡 400 |
| `v1/oa-file-utility/file/presign-download` | `?file_url=1` · ⛓ file_url dari response upload (*/upload/url | upload/presign) → data.url | 🟡 400 |
| `mfa/v1/prompt/trusted/validate` | `?token=1&signature=1` | 🟡 400 |
| `chat/v2/broadcast/{room_id}/messages` | `?limit=10` · ⛓ {room_id} dari GET chat/v2/rooms (broadcast) → data.rooms[].id | 🚫 403 |
| `chat/v2/groups/{group_id}/messages` | `?limit=10` · ⛓ {group_id} dari GET chat/v2/groups (list grup) → data[].id | 🚫 403 |
| `chat/v2/personal/{room_id}/messages` | `?limit=10` · ⛓ {room_id} dari GET chat/v2/rooms → data.rooms[].id | 🚫 403 |
| `chat/v2/groups/{group_id}/messages` | `?limit=10` · ⛓ {group_id} dari GET chat/v2/groups (list grup) → data[].id | 🚫 403 |

## cURL terverifikasi `200`

```bash
# order-trade/broker/activity-chart
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/broker/activity-chart?brokers_code=YP&symbols=BBCA&to=2024-12-31&market_board=1&investor_type=1&period=1"

# order-trade/broker/activity/historical
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/broker/activity/historical?period=1&broker_codes=YP&symbols=BBCA&market_board=1&investor_type=1&transaction_type=1&interval=1&pagination.page=1&pagination.limit=10"

# order-trade/broker/activity
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/broker/activity?broker_code=YP&to=2024-12-31&transaction_type=1&market_board=1&investor_type=1&period=1"

# charts/{symbol}
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/charts/{symbol}?timeframe=1d"

# chat/v2/rooms
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/chat/v2/rooms?limit=10"

# chat/v2/rooms/type/invited
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/chat/v2/rooms/type/invited?limit=10"

# chat/s3/policy
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/chat/s3/policy?filename=test.jpg"

# chat/v2/groups/members/suggestions/contacts
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/chat/v2/groups/members/suggestions/contacts?limit=10"

# chat/v2/groups/members/suggestions
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/chat/v2/groups/members/suggestions?limit=10"

# chat/v3/user/search
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/chat/v3/user/search?keyword=niaben&page=1&limit=10"

# order-trade/running-trade/chart/{symbol}
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/running-trade/chart/{symbol}?broker_code=YP&to=2024-12-31&period=1&market_board=1&investor_type=1"

# charts/{symbol}/daily
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/charts/{symbol}/daily?timeframe=1D"

# chartbit/token/mobile
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/chartbit/token/mobile?theme=light&symbol=BBCA"

# fundachart/v2/{symbol}/financials
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/fundachart/v2/{symbol}/financials?data_type=1&report=1"

# findata-view/v2/financials/{symbol}
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/findata-view/v2/financials/{symbol}?data_type=1&report_type=1&statement_type=1&is_percentage=false"

# company-price-feed/prices
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/company-price-feed/prices?stock_code=BBCA"

# comparison/v2/ratios
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/comparison/v2/ratios?symbol=BBCA"

# corpaction/{symbol}/stock_conversion
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/corpaction/{symbol}/stock_conversion?page=1&limit=10"

# order-trade/running-trade
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/running-trade?symbols=BBCA&order_by=1&sort=1"

# seasonality/{company_symbol}
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/seasonality/{company_symbol}?year=2024"

# seasonality/{company_symbol}/years
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/seasonality/{company_symbol}/years"

# order-trade/trade-book
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/trade-book?symbol=BBCA&group_by=1&sort_by=1&sort_direction=1&time_interval=1&to=2024-12-31"

# order-trade/trade-book/chart
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/trade-book/chart?symbol=BBCA&time_interval=1m&to=2024-12-31"

# findata-view/marketdetectors/activity/{code}/detail  (⛓ {code}=kode broker valid dari GET findata-view/marketdetectors/brokers (field data[].code, mis. AD))
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/findata-view/marketdetectors/activity/{code}/detail?page=1&limit=10"

# findata-view/marketdetectors/brokers
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/findata-view/marketdetectors/brokers?limit=10&page=1"

# fundachart/{symbol}/financials
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/fundachart/{symbol}/financials?data_type=1&report=1"

# insider/majorholder/ownership  (⛓ insider_id dari GET insider/company/majorholder?symbol=BBCA (field movement[].id))
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/insider/majorholder/ownership?insider=1000000439&page=1"

# live-stream/event
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/live-stream/event?page=1&limit=10"

# notification/v2/push-notification/status
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" -H 'X-DeviceID: f4f20993837a2bbd61a2fec250553e93' \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/notification/v2/push-notification/status?device_id=2292f1cb-37ad-42c7-942e-fbd6c0f26669"

# order-trade/broker/distribution
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/broker/distribution?symbol=BBCA"

# order-trade/order-queue
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/order-trade/order-queue?stock_code=BBCA&board_type=1&data_type=1&market_board=1&investor_type=1&order_status=1&period=1&action_type=1&limit=10"

# company-price-feed/trade-book
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/company-price-feed/trade-book?symbol=BBCA&group_by=1&sort_by=1&sort_direction=1&time_interval=1&to=2024-12-31"

# company-price-feed/running-trade
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/company-price-feed/running-trade?symbol=BBCA&order_by=1"

# company-price-feed/v2/running-trade
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/company-price-feed/v2/running-trade?symbol=BBCA&order_by=1"

# request-verified/upload-token
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/request-verified/upload-token?type=1"

# screener/templates/{id}
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/screener/templates/{id}?type=1"

# watchlist/search/company
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/watchlist/search/company?keyword=BBCA&watchlist_id=7174647&page=1&limit=10"

# sharetrade/target
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/sharetrade/target?limit=10"

# watchlist/suggestion/company
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/watchlist/suggestion/company?watchlist_id=7174647"

# watchlist/{watchlist_id}
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/watchlist/{watchlist_id}?limit=10"

```
---

# Appendix D — Peta Ketergantungan Antar-Endpoint (Param Sourcing)

> Banyak endpoint butuh ID/kode yang **dihasilkan endpoint lain**. Tabel ini memetakan: param → endpoint penyedia → field response. ✅=terverifikasi live, ◽=inferred dari source.

| Param dibutuhkan | Dipakai oleh (contoh) | Endpoint penyedia (GET) | Field sumber | Status |
|---|---|---|---|---|
| `symbol` / `symbols` | charts, trade-book, running-trade, order-queue, financials, dst | `watchlist/{watchlist_id}/symbols` · `watchlist/search/company?keyword=` · `emitten/discover/{type}` | `data.symbols[]` / `data[].symbol` | ✅ |
| `watchlist_id` | `watchlist/{watchlist_id}`, `watchlist/search/company`, `watchlist/suggestion/company` | login response · `GET watchlist?category_types=1` | `user.watchlist_id` / `data[].watchlist_id` | ✅ |
| `insider` (insiderID) | `insider/majorholder/ownership` | `insider/company/majorholder?symbol=BBCA` | `data.movement[].id` | ✅ |
| `broker_code`/`broker_codes`/`brokers_code`/`{code}` | broker-activity(3), broker-flow, `marketdetectors/activity/{code}/detail` | `findata-view/marketdetectors/brokers` | `data[].code` (mis. `AD`) | ✅ |
| `room_id` (chat personal/broadcast) | `chat/v2/personal/{room_id}/messages`, `chat/v2/broadcast/{room_id}/messages` | `chat/v2/rooms` | `data.rooms[].id` | ✅ |
| `group_id` (chat group) | `chat/v2/groups/{group_id}/messages|members|settings` | `chat/v2/groups` (list grup user) | `data[].id` | ◽ |
| `{room_id}` (lawan personal) | `chat/v2/personal/room/{room_id}` | `chat/v3/user/search?keyword=` | `data[].id` (user id) | ◽ |
| `emiten_code` | `eipo/social/company/detail`, `eipo/company/unboxing` | `eipo/social/company/list` | `data[].emiten_code` | ◽ |
| `order_id` | order detail/amend/cancel (securities) | `order` list (TransactionService, host securities) | `data[].order_id` | ◽ |
| `X-DeviceID` (header) | `notification/v2/push-notification/status` | JWT `dvc` claim / login `token_data` | `dvc` | ✅ |
| `file_url` | `v1/oa-file-utility/file/presign-download` | response `*/upload/url` · `*/upload/presign` | `data.url` | ◽ |
| `source_type` (insider) | `insider/majorholder/ownership` | enum **INTEGER** (`1`) — bukan dari endpoint | — | ✅ |

## Contoh alur berantai (end-to-end)

```
login (player_id) ──> user.watchlist_id (7174647)
  └─> GET watchlist/{watchlist_id}/symbols ──> symbols[] (BBCA, BBRI, ...)
        └─> GET charts/{symbol}?timeframe=1d              (pakai symbol)
        └─> GET order-trade/trade-book?symbol=..&group_by=1&time_interval=1&to=..
        └─> GET insider/company/majorholder?symbol=..  ──> movement[].id
               └─> GET insider/majorholder/ownership?insider={id}&page=1
GET findata-view/marketdetectors/brokers ──> data[].code (AD)
  └─> GET findata-view/marketdetectors/activity/{code}/detail?page=1&limit=10
GET chat/v2/rooms ──> data.rooms[].id
  └─> GET chat/v2/personal/{room_id}/messages?limit=10
```

**Catatan nilai enum** (dipakai lintas endpoint market-data): `order_by/group_by/sort_by/sort_direction/board_type/market_board/investor_type/transaction_type/order_status/action_type/period/data_type/interval` = **integer** (mis. `1`); `timeframe`/`time_interval` = kode huruf-kecil (`1d`,`1w`,`1m`,`1h`).

---

# Appendix E — Candlestick / Historical OHLC (data >1 tahun, seperti Chartbit)

> Endpoint **`GET company-price-feed/historical/summary/{symbol}`** (host `exodus.stockbit.com`, `OrderBookApi.getHistoricalData`). Inilah sumber data OHLC harian "Historical Data"/Chartbit. Terverifikasi live.

**Field tiap candle:** `date`, `open`, `high`, `low`, `close`, `volume`, `value`, `frequency`, `average`, `change`, `change_percentage`, `foreign_buy`, `foreign_sell`, `net_foreign`.

**Query param (digali dari `RemoteOrderBookDataSourceImpl`):**
| key | arti | nilai |
|---|---|---|
| `period` | interval candle | `1` (harian) |
| `limit` | jumlah candle/halaman | **maks `50`** (>50 → `400`) |
| `page` | halaman | `1`, lalu ikuti `data.paginate.next_page` |
| `start_date` / `end_date` | filter rentang (opsional) | format `yyyy-MM-dd` |

Data **terbaru dulu** (descending). Untuk >1 tahun (~250+ hari bursa), **paginasi** sampai `next_page` habis.

## 1) Satu halaman (50 candle terbaru)
```bash
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/company-price-feed/historical/summary/BBCA?period=1&page=1&limit=50"
```

## 2) Loop ambil >1 tahun (paginasi otomatis) → simpan ke ohlc.json
```bash
SYMBOL=BBCA; TOKEN=$(cat StockbitData/stockbit_access_token.txt)
YEARS=5; STOP=$(date -v-${YEARS}y +%F)         # tanggal target (mis. 5 tahun lalu)
page=1; echo "[" > ohlc.json
while [ "$page" != "null" ] && [ "$page" -le 80 ]; do
  resp=$(curl -s -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
    -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
    "https://exodus.stockbit.com/company-price-feed/historical/summary/$SYMBOL?period=1&page=$page&limit=50")
  echo "$resp" | jq -c '.data.result[]' | sed 's/$/,/' >> ohlc.json
  oldest=$(echo "$resp" | jq -r '.data.result[-1].date')
  [ "$oldest" \< "$STOP" ] && break                      # berhenti saat sudah menutup target
  page=$(echo "$resp" | jq -r '.data.paginate.next_page // "null"')
done
sed -i '' '$ s/,$//' ohlc.json; echo "]" >> ohlc.json
echo "Tersimpan $(jq length ohlc.json) candle: $(jq -r '.[-1].date' ohlc.json) s/d $(jq -r '.[0].date' ohlc.json)"
```
> Ganti `YEARS=5` → `10` untuk 10 tahun. Histori tersedia **>8 tahun** (BBCA terverifikasi mundur s/d 2018). Tiap halaman 50 candle harian; `next_page` lanjut sampai data habis (tak ada batas kedalaman dari server).

## 3) Rentang tanggal spesifik (mis. 1 tahun penuh)
```bash
curl -A 'okhttp/4.12.0' -H "Authorization: Bearer $TOKEN" \
  -H 'X-AppVersion: 3.21.0' -H 'X-Platform: android' -H 'Accept-Language: id' \
  "https://exodus.stockbit.com/company-price-feed/historical/summary/BBCA?start_date=2025-01-01&end_date=2025-12-31&period=1&page=1&limit=50"
```
> Untuk menutup seluruh rentang, tetap paginasi `page` mengikuti `next_page` (50 candle/halaman).

**Terverifikasi (multi-tahun):**
- **5 tahun** → 24 halaman × 50 = **1.200 candle**, `2021-05-28` s/d `2026-05-29` (5.01 th).
- **8+ tahun** → 40+ halaman = **2.000+ candle**, mundur s/d `2018-02-05` (server belum mentok).
- Contoh candle: `{date:2026-05-29, open:5750, high:5875, low:5700, close:5700, volume:10152966}`.

**Alternatif chart lain:** `charts/{symbol}?timeframe=1d` (chart ringkas, timeframe `1d/1w/1m/1y/3y/5y/10y`) · `chartbit/token/mobile` (token untuk widget TradingView/Chartbit di `stockbit.com/chartbit.html`).
