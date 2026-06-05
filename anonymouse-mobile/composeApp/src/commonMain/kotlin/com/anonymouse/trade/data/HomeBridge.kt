package com.anonymouse.trade.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class AllocDto(val name: String = "", val pct: Int = 0)
@Serializable
data class ActivityDto(val kind: String = "signal", val txt: String = "", val t: String = "")
@Serializable
data class HomeDto(
    val balance: Double = 0.0, val currency: String = "USD",
    val pnlToday: Double = 0.0, val pnl30: Double = 0.0,
    val winRate: Int = 0, val openPositions: Int = 0,
    val equity: List<Double> = emptyList(),
    val allocation: List<AllocDto> = emptyList(),
    val activity: List<ActivityDto> = emptyList(),
    val signals: List<SignalDto> = emptyList(),
    val source: String = "",
)

private val homeJson = Json { ignoreUnknownKeys = true; isLenient = true }

fun buildHomePrompt(): String = """
    TUGAS: Ringkasan portfolio untuk dashboard. Keluarkan HANYA satu blok JSON.
    Sumber NYATA: forex MT5 API http://192.168.0.111:8000 (GET /api/account = balance/equity USD; GET /api/positions = posisi terbuka; GET /api/deals atau history utk win-rate ~60 deal terakhir + PnL hari ini & 30 hari). IDX /opt/idx-quant/data/ara_paper.json (modal+realized, posisi open).
    balance=equity akun MT5 (USD). pnlToday=% hari ini. pnl30=% 30 hari. winRate=% deal profit ~60 terakhir. openPositions=jumlah posisi terbuka (forex+IDX open). equity=~40 titik kurva (riwayat bila ada; jika tidak, susun konsisten dgn pnl30). allocation=alokasi per instrumen/aset (name+pct, total 100). activity=4-6 kejadian terbaru (kind: signal|backtest|win|loss|billing). signals=hingga 4 posisi terbuka teratas (pair,dir,entry,roi,status,market,strat).
    Skema: {"balance":9516.0,"currency":"USD","pnlToday":0.3,"pnl30":2.1,"winRate":58,"openPositions":2,"equity":[...],"allocation":[{"name":"XAUUSD","pct":40}],"activity":[{"kind":"win","txt":"...","t":"2h"}],"signals":[{"pair":"XAUUSD","dir":"LONG","entry":2654,"roi":0.6,"status":"active","market":"forex","strat":"TREND"}],"source":"live"}
    Angka HARUS nyata. Jawab HANYA blok ```json ... ```.
""".trimIndent()

fun parseHome(text: String): HomeDto? {
    val js = extractObj(text) ?: return null
    val d = runCatching { homeJson.decodeFromString<HomeDto>(js) }.getOrNull() ?: return null
    if (d.balance <= 0 && d.equity.isEmpty()) return null
    return d
}

fun mockHome(): HomeDto {
    val pf = DB.portfolio
    return HomeDto(
        balance = pf.balance, currency = "USD", pnlToday = pf.pnlToday, pnl30 = pf.pnl30,
        winRate = pf.winRate, openPositions = pf.openPositions,
        equity = pf.equity.map { it.toDouble() },
        allocation = pf.allocation.map { AllocDto(it.name, it.pct) },
        activity = pf.activity.map { ActivityDto(it.kind, it.txt, it.t) },
        signals = mockSignals().filter { it.status == "active" }.take(4),
        source = "mock",
    )
}
