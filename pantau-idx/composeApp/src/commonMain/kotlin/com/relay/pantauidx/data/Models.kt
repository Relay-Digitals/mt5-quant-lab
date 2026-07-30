package com.relay.pantauidx.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject

/* ------------------------------------------------------------------ *
 *  Wire DTOs (Stockbit exodus).  Only candles have a documented body; *
 *  the rest are parsed tolerantly (ignoreUnknownKeys) with the fields *
 *  we actually render — extend as real payloads are confirmed.        *
 * ------------------------------------------------------------------ */

@Serializable
data class Envelope<T>(
    val data: T? = null,
    val message: String? = null,
)

/* ---- charts/{symbol}/daily ---- */
@Serializable
data class CandlesData(val prices: List<PricePoint> = emptyList())

@Serializable
data class PricePoint(
    val date: String? = null,               // unix ms as string
    @SerialName("formatted_date") val formattedDate: String? = null,
    val open: String? = null,
    val high: String? = null,
    val low: String? = null,
    val value: String? = null,              // = close
    val volume: String? = null,
)

/* ---- screener/universe · screener/preset · screener/templates/{id} ---- */
@Serializable
data class ScreenerUniverseData(
    @SerialName("total") val total: Int? = null,
    @SerialName("companies") val companies: List<ScreenerRowDto> = emptyList(),
    @SerialName("results") val results: List<ScreenerRowDto> = emptyList(),
) {
    val rows: List<ScreenerRowDto> get() = companies.ifEmpty { results }
}

@Serializable
data class ScreenerRowDto(
    val symbol: String? = null,
    val name: String? = null,
    @SerialName("company_name") val companyName: String? = null,
    val last: JsonElement? = null,
    val price: JsonElement? = null,
    val change: JsonElement? = null,
    @SerialName("percentage_change") val percentageChange: JsonElement? = null,
    @SerialName("change_percentage") val changePercentage: JsonElement? = null,
    val volume: JsonElement? = null,
    val value: JsonElement? = null,
    /** any extra screener metrics keyed by metric id. */
    val metrics: JsonObject? = null,
)

@Serializable
data class ScreenerPresetData(
    val presets: List<ScreenerPreset> = emptyList(),
    val data: List<ScreenerPreset> = emptyList(),
) {
    val all: List<ScreenerPreset> get() = presets.ifEmpty { data }
}

@Serializable
data class ScreenerPreset(
    val id: String? = null,
    val name: String? = null,
    val title: String? = null,
    val description: String? = null,
    @SerialName("total_result") val totalResult: Int? = null,
)

/* ---- watchlist ---- */
@Serializable
data class WatchlistData(
    val watchlist: List<WatchlistDto> = emptyList(),
    val data: List<WatchlistDto> = emptyList(),
) {
    val all: List<WatchlistDto> get() = watchlist.ifEmpty { data }
}

@Serializable
data class WatchlistDto(
    val id: JsonElement? = null,
    val name: String? = null,
    @SerialName("total_symbol") val totalSymbol: Int? = null,
)

/* ---- insider/company/majorholder ---- */
@Serializable
data class InsiderData(val movement: List<InsiderMovementDto> = emptyList())

@Serializable
data class InsiderMovementDto(
    val id: JsonElement? = null,
    val name: String? = null,
    @SerialName("holder_name") val holderName: String? = null,
    val date: String? = null,
    val action: String? = null,        // BUY / SELL
    val current: JsonElement? = null,
    val previous: JsonElement? = null,
    val price: JsonElement? = null,
    val type: String? = null,
    val source: String? = null,
)

/* ---- research/company/{symbol} (detail header + keystats) ---- */
@Serializable
data class CompanyResearchData(
    val symbol: String? = null,
    val name: String? = null,
    @SerialName("company_name") val companyName: String? = null,
    val last: JsonElement? = null,
    val change: JsonElement? = null,
    @SerialName("percentage_change") val percentageChange: JsonElement? = null,
    val keystats: JsonObject? = null,
)

/* ------------------------------------------------------------------ *
 *  Domain models the UI actually renders                              *
 * ------------------------------------------------------------------ */

data class Candle(
    val timeSec: Long,
    val date: String,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val volume: Double,
)

data class StockRow(
    val code: String,
    val name: String,
    val price: Double,
    val change: Double,       // absolute
    val changePct: Double,    // %
    val board: String = "RG",
    val spark: List<Double> = emptyList(),
) {
    val up: Boolean get() = changePct >= 0
}

data class InsiderTx(
    val code: String,
    val holder: String,
    val date: String,
    val action: String,       // BUY / SELL
    val current: Double,
    val previous: Double,
    val price: Double,
    val type: String,
    val source: String,
) {
    val isBuy: Boolean get() = action.equals("BUY", ignoreCase = true)
    val delta: Double get() = current - previous
}

data class ScreenPreset(
    val id: String,
    val title: String,
    val description: String,
    val count: Int,
)
