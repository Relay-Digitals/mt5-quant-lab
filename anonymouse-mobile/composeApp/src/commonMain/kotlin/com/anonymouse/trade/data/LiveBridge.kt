package com.anonymouse.trade.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class LivePos(
    val sym: String = "", val side: String = "LONG", val qty: String = "",
    val entry: Double = 0.0, val mark: Double = 0.0,
    val pnl: Double = 0.0, val pnlPct: Double = 0.0, val strat: String = "",
)
@Serializable
data class LiveForex(
    val balance: Double = 0.0, val currency: String = "USD", val profit: Double = 0.0,
    val openPnlPct: Double = 0.0, val positions: List<LivePos> = emptyList(), val ts: Long = 0L,
)

private val liveJson = Json { ignoreUnknownKeys = true; isLenient = true }

fun parseLiveForex(text: String): LiveForex? {
    val js = extractObj(text) ?: return null
    return runCatching { liveJson.decodeFromString<LiveForex>(js) }.getOrNull()
}
