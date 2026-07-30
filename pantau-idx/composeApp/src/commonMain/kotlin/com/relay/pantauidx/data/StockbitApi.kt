package com.relay.pantauidx.data

import io.ktor.client.HttpClient
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.defaultRequest
import io.ktor.client.request.get
import io.ktor.client.request.header
import io.ktor.client.request.parameter
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.jsonPrimitive

/**
 * Thin Stockbit exodus client. Every request carries the mandatory headers
 * (okhttp UA is required or Cloudflare returns 1010) and the Bearer token from [tokens].
 */
class StockbitApi(
    private val tokens: TokenProvider,
    engine: HttpClient = platformHttpClient(),
) {
    val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        coerceInputValues = true
        explicitNulls = false
    }

    private val client = engine.config {
        install(ContentNegotiation) { json(json) }
        defaultRequest {
            header("User-Agent", StockbitConfig.USER_AGENT)
            header("X-AppVersion", StockbitConfig.APP_VERSION)
            header("X-Platform", StockbitConfig.PLATFORM)
            header("Accept-Language", StockbitConfig.ACCEPT_LANGUAGE)
        }
    }

    private suspend fun getText(path: String, params: Map<String, String> = emptyMap()): String {
        return client.get("${StockbitConfig.BASE_URL}/$path") {
            header(HttpHeaders.Authorization, "Bearer ${tokens.current}")
            params.forEach { (k, v) -> parameter(k, v) }
        }.bodyAsText()
    }

    /** POST helper (login flow etc.). [auth] false skips the bearer for pre-login calls. */
    suspend fun postText(path: String, body: String, auth: Boolean = true): String {
        return client.post("${StockbitConfig.BASE_URL}/$path") {
            if (auth && tokens.current.isNotBlank()) header(HttpHeaders.Authorization, "Bearer ${tokens.current}")
            contentType(ContentType.Application.Json)
            setBody(body)
        }.bodyAsText()
    }

    /* -------- charts/{symbol}/daily -------- */
    suspend fun candles(symbol: String, timeframe: String = "1Y"): List<Candle> {
        val raw = getText(
            "charts/${symbol.uppercase()}/daily",
            mapOf("timeframe" to timeframe, "chart_type" to "PRICE_CHART_TYPE_CANDLE"),
        )
        val env = json.decodeFromString(Envelope.serializer(CandlesData.serializer()), raw)
        return env.data?.prices.orEmpty().mapNotNull { p ->
            val o = p.open?.toDoubleOrNull() ?: return@mapNotNull null
            val c = p.value?.toDoubleOrNull() ?: return@mapNotNull null
            Candle(
                timeSec = (p.date?.toLongOrNull() ?: 0L) / 1000,
                date = p.formattedDate ?: "",
                open = o,
                high = p.high?.toDoubleOrNull() ?: o,
                low = p.low?.toDoubleOrNull() ?: o,
                close = c,
                volume = p.volume?.toDoubleOrNull() ?: 0.0,
            )
        }
    }

    /* -------- screener/universe : the master "screens" list -------- */
    suspend fun screenerUniverse(): List<StockRow> {
        val raw = getText("screener/universe")
        val env = json.decodeFromString(Envelope.serializer(ScreenerUniverseData.serializer()), raw)
        return env.data?.rows.orEmpty().map { it.toStockRow() }
    }

    /* -------- screener/preset : predefined screens (guru / preset) -------- */
    suspend fun screenerPresets(): List<ScreenPreset> {
        val raw = getText("screener/preset", mapOf("page" to "1"))
        val env = json.decodeFromString(Envelope.serializer(ScreenerPresetData.serializer()), raw)
        return env.data?.all.orEmpty().map {
            ScreenPreset(
                id = it.id ?: "",
                title = it.title ?: it.name ?: "Screen",
                description = it.description ?: "",
                count = it.totalResult ?: 0,
            )
        }
    }

    /* -------- screener/templates/{id} : run a saved/guru screen -------- */
    suspend fun runScreen(id: String, type: String = "guru"): List<StockRow> {
        val raw = getText("screener/templates/$id", mapOf("type" to type))
        val env = json.decodeFromString(Envelope.serializer(ScreenerUniverseData.serializer()), raw)
        return env.data?.rows.orEmpty().map { it.toStockRow() }
    }

    /* -------- watchlist -------- */
    suspend fun watchlists(): List<WatchlistDto> {
        val raw = getText("watchlist")
        val env = json.decodeFromString(Envelope.serializer(WatchlistData.serializer()), raw)
        return env.data?.all.orEmpty()
    }

    /* -------- emitten/trending : Market screen "Trending" -------- */
    suspend fun trending(): List<StockRow> {
        val raw = getText("emitten/trending", mapOf("page" to "1", "limit" to "20"))
        val env = json.decodeFromString(Envelope.serializer(ScreenerUniverseData.serializer()), raw)
        return env.data?.rows.orEmpty().map { it.toStockRow() }
    }

    /* -------- insider/company/majorholder?symbols= -------- */
    suspend fun insider(symbols: List<String>): List<InsiderTx> {
        val raw = getText("insider/company/majorholder", mapOf("symbols" to symbols.joinToString(",")))
        val env = json.decodeFromString(Envelope.serializer(InsiderData.serializer()), raw)
        return env.data?.movement.orEmpty().map { m ->
            InsiderTx(
                code = symbols.firstOrNull() ?: "",
                holder = m.holderName ?: m.name ?: "—",
                date = m.date ?: "",
                action = m.action ?: "BUY",
                current = m.current.num(),
                previous = m.previous.num(),
                price = m.price.num(),
                type = m.type ?: "",
                source = m.source ?: "SB",
            )
        }
    }

    /* -------- research/company/{symbol} : detail header -------- */
    suspend fun company(symbol: String): CompanyResearchData? {
        val raw = getText("research/company/${symbol.uppercase()}")
        return json.decodeFromString(Envelope.serializer(CompanyResearchData.serializer()), raw).data
    }

    /* -------- carina portfolio (needs SECURITIES token via Authorization-Carina) --------
     * Separate PIN-gated trading login; the exodus data token does NOT authorize these.
     * Returns raw JSON so the caller can parse whatever the securities backend sends. */
    suspend fun portfolioSummary(carinaToken: String): String {
        return client.get("${StockbitConfig.CARINA_URL}/portfolio/v2/summary") {
            header(HttpHeaders.Authorization, "Bearer ${tokens.current}")
            header("Authorization-Carina", "Bearer $carinaToken")
        }.bodyAsText()
    }
}

/* ---- JsonElement → number coercion (fields arrive as string or number) ---- */
internal fun JsonElement?.num(): Double =
    this?.jsonPrimitive?.content?.replace(",", "")?.toDoubleOrNull() ?: 0.0

private fun ScreenerRowDto.toStockRow(): StockRow {
    val px = (last ?: price).num()
    val pct = (percentageChange ?: changePercentage).num()
    val chg = change.num()
    return StockRow(
        code = symbol ?: "—",
        name = name ?: companyName ?: "",
        price = px,
        change = chg,
        changePct = pct,
    )
}
