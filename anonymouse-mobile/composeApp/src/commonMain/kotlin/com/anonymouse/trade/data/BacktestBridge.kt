package com.anonymouse.trade.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class BtStatsDto(
    val totalReturn: Double = 0.0, val finalEquity: Double = 0.0, val winRate: Int = 0,
    val profitFactor: Double = 0.0, val maxDD: Double = 0.0, val sharpe: Double = 0.0,
)
@Serializable
data class BtTradeDto(val n: Int = 0, val dir: String = "LONG", val day: Int = 0, val pnl: Double = 0.0, val win: Boolean = false)
@Serializable
data class BtDto(val stats: BtStatsDto = BtStatsDto(), val curve: List<Double> = emptyList(), val trades: List<BtTradeDto> = emptyList())

private val btJson = Json { ignoreUnknownKeys = true; isLenient = true }

@Serializable
data class StrategyMeta(val id: String = "", val name: String = "", val desc: String = "")
@Serializable
data class MetaDto(val strategies: List<StrategyMeta> = emptyList(), val pairs: List<String> = emptyList(), val tfs: List<String> = emptyList())

fun parseMeta(text: String): MetaDto? = runCatching { btJson.decodeFromString<MetaDto>(text) }.getOrNull()?.takeIf { it.strategies.isNotEmpty() }

@Serializable
data class RunDto(
    val run_id: String = "", val source: String = "", val strategy: String = "", val symbol: String = "",
    val tf: String = "", val ret: Double = 0.0, val trades: Int = 0, val winRate: Double = 0.0,
    val pf: Double = 0.0, val maxDD: Double = 0.0, val at: String = "",
)
@Serializable
data class RunsResp(val runs: List<RunDto> = emptyList())

fun parseRuns(text: String): List<RunDto> = runCatching { btJson.decodeFromString<RunsResp>(text).runs }.getOrDefault(emptyList())

/** prompt minta Claude jalankan backtest ASLI di CT108 lalu balas HANYA blok JSON. */
fun buildBacktestPrompt(cfg: BacktestCfg): String = """
TUGAS: Jalankan backtest NYATA di server, lalu keluarkan HANYA satu blok JSON (tanpa kalimat lain) dengan skema persis:
{"stats":{"totalReturn":<persen,float>,"finalEquity":<int>,"winRate":<int 0-100>,"profitFactor":<float>,"maxDD":<persen positif,float>,"sharpe":<float>},"curve":[<~60 nilai equity float dari awal ke akhir>],"trades":[{"n":1,"dir":"LONG|SHORT","day":<int>,"pnl":<float>,"win":<bool>}]}
Parameter: strategy=${cfg.strategy}, pair=${cfg.pair}, capital=${cfg.capital}, risk=${cfg.riskPct}%, period=${cfg.period} hari, leverage=${cfg.leverage}x.
Gunakan skrip backtest ASLI: forex → /opt/mt5-quant (regime_scan.py / engine backtest); saham IDX → /opt/idx-quant (idx_backtest.py / bt_*.py). Jalankan python dgn PYTHONPATH yang sesuai. Angka HARUS dari hasil backtest nyata (bukan karangan). Jika equity curve penuh tak tersedia, susun ~60 titik yang konsisten dgn totalReturn & maxDD. Jawab: HANYA satu blok ```json ... ```.
""".trimIndent()

/** parse teks balasan Claude → BacktestResult; null kalau gagal. */
fun parseBacktest(text: String): BacktestResult? {
    val js = extractJson(text) ?: return null
    val d = runCatching { btJson.decodeFromString<BtDto>(js) }.getOrNull() ?: return null
    if (d.curve.isEmpty() && d.trades.isEmpty()) return null
    val curve = d.curve.map { it.toFloat() }.ifEmpty { listOf(d.stats.finalEquity.toFloat(), d.stats.finalEquity.toFloat()) }
    return BacktestResult(
        stats = BacktestStats(d.stats.totalReturn, d.stats.finalEquity.toInt(), d.stats.winRate,
            d.stats.profitFactor, d.stats.maxDD, d.stats.sharpe),
        curve = curve,
        trades = d.trades.map { BacktestTrade(it.n, it.dir, it.day, it.pnl, it.win) },
    )
}

/** ekstrak objek JSON dari teks: dari blok ```json``` atau {...} pertama yang seimbang. */
private fun extractJson(text: String): String? {
    val fence = Regex("```(?:json)?\\s*([\\s\\S]*?)```").find(text)?.groupValues?.getOrNull(1)?.trim()
    val src = fence ?: text
    val start = src.indexOf('{'); if (start < 0) return null
    var depth = 0
    for (i in start until src.length) {
        when (src[i]) {
            '{' -> depth++
            '}' -> { depth--; if (depth == 0) return src.substring(start, i + 1) }
        }
    }
    return null
}
