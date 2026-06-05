package com.anonymouse.trade.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class FwdPosDto(val sym: String = "", val side: String = "LONG", val qty: String = "",
                     val entry: Double = 0.0, val mark: Double = 0.0, val pnlPct: Double = 0.0,
                     val pnl: Double = 0.0)
@Serializable
data class FwdFeedDto(val t: String = "", val kind: String = "scan", val txt: String = "")
@Serializable
data class FwdDto(
    val balance: Double = 0.0, val currency: String = "USD",
    val equity: List<Double> = emptyList(), val openPnlPct: Double = 0.0, val winRate: Int = 0,
    val positions: List<FwdPosDto> = emptyList(), val feed: List<FwdFeedDto> = emptyList(),
    val source: String = "",
)

private val fwdJson = Json { ignoreUnknownKeys = true; isLenient = true }

fun buildForwardPrompt(market: String): String = when (market) {
    "forex" -> """
        TUGAS: Ambil status forward-test FOREX LIVE dari MT5 API http://192.168.0.111:8000 lalu keluarkan HANYA satu blok JSON.
        Langkah: GET /api/positions (posisi terbuka) & /api/account (saldo/equity) via curl. Hitung pnlPct tiap posisi.
        Skema: {"balance":<float>,"currency":"USD","equity":[<~40 float bila ada riwayat; bila tidak, ulangi balance>],"openPnlPct":<float>,"winRate":<int>,"positions":[{"sym":"AUDJPY","side":"LONG|SHORT","qty":"0.5","entry":<float>,"mark":<float>,"pnlPct":<float>}],"feed":[{"t":"now","kind":"entry|tp|sl|scan","txt":"..."}],"source":"mt5-live"}
        Angka HARUS nyata dari API. Jawab HANYA blok ```json ... ```.
    """.trimIndent()
    "idx" -> """
        TUGAS: Baca portfolio paper-trade IDX di /opt/idx-quant/data/ara_paper.json lalu keluarkan HANYA satu blok JSON.
        Ambil capital0, realized (jumlah net posisi closed), dan posisi status=="open" (gunakan field entry, cur sbg mark, shares sbg qty). balance = capital0 + total net closed. openPnlPct = rata2 ((cur/entry-1)*100) posisi open. winRate = % posisi closed yg net>0.
        Skema: {"balance":<float>,"currency":"IDR","equity":[],"openPnlPct":<float>,"winRate":<int>,"positions":[{"sym":"BBRI","side":"LONG","qty":"<shares> lot","entry":<float>,"mark":<float>,"pnlPct":<float>}],"feed":[{"t":"today","kind":"entry","txt":"<kode> dibuka"}],"source":"ara-paper"}
        Jawab HANYA blok ```json ... ```.
    """.trimIndent()
    else -> ""
}

fun parseForward(text: String): FwdDto? {
    val js = extractJsonObj(text) ?: return null
    val d = runCatching { fwdJson.decodeFromString<FwdDto>(js) }.getOrNull() ?: return null
    return d
}

private fun extractJsonObj(text: String): String? {
    val fence = Regex("```(?:json)?\\s*([\\s\\S]*?)```").find(text)?.groupValues?.getOrNull(1)?.trim()
    val src = fence ?: text
    val start = src.indexOf('{'); if (start < 0) return null
    var depth = 0
    for (i in start until src.length) when (src[i]) {
        '{' -> depth++
        '}' -> { depth--; if (depth == 0) return src.substring(start, i + 1) }
    }
    return null
}

/** fallback dari MockData → FwdDto (untuk crypto / offline). */
fun mockForward(market: String): FwdDto {
    val pos = DB.paperPositions(market).map { FwdPosDto(it.sym, it.side, it.qty, it.entry, it.mark, it.pnlPct) }
    val eq = DB.series(10000.0, 70, 0.05, if (market == "idx") 0.006 else 0.011, market.length * 13 + 5).map { it.toDouble() }
    return FwdDto(
        balance = eq.last(), currency = if (market == "idx") "IDR" else if (market == "forex") "USD" else "USD",
        equity = eq, openPnlPct = pos.sumOf { it.pnlPct }, winRate = if (pos.isEmpty()) 0 else pos.count { it.pnlPct >= 0 } * 100 / pos.size,
        positions = pos, feed = emptyList(), source = "mock",
    )
}
