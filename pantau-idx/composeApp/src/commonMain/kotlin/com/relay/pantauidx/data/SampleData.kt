package com.relay.pantauidx.data

import kotlin.math.sin

/**
 * Fallback dataset used when no live token is present (env token expired 2026-05-31).
 * Values mirror the design mock + real IDX blue chips so screens look correct offline.
 * Marked clearly in the UI as "SIMULATED DATA · DELAYED".
 */
object SampleData {

    private fun spark(seed: Int, up: Boolean, n: Int = 24): List<Double> =
        List(n) { i ->
            val base = sin((i + seed) * 0.6) * 6 + sin((i + seed) * 0.17) * 10
            base + (if (up) i * 0.9 else -i * 0.7)
        }

    val watchlist = listOf(
        StockRow("BBCA", "Bank Central Asia", 9_650.0, 125.0, 1.31, "RG", spark(1, true)),
        StockRow("BBRI", "Bank Rakyat Indonesia", 4_180.0, -30.0, -0.71, "RG", spark(3, false)),
        StockRow("BMRI", "Bank Mandiri", 6_275.0, 75.0, 1.21, "RG", spark(5, true)),
        StockRow("TLKM", "Telkom Indonesia", 2_710.0, -20.0, -0.73, "RG", spark(7, false)),
        StockRow("ASII", "Astra International", 4_890.0, 40.0, 0.82, "RG", spark(9, true)),
        StockRow("ANTM", "Aneka Tambang", 1_585.0, 55.0, 3.59, "RG", spark(11, true)),
        StockRow("ADRO", "Adaro Energy", 2_460.0, -35.0, -1.40, "RG", spark(13, false)),
        StockRow("GOTO", "GoTo Gojek Tokopedia", 74.0, 3.0, 4.23, "RG", spark(15, true)),
        StockRow("UNTR", "United Tractors", 26_150.0, 300.0, 1.16, "RG", spark(17, true)),
        StockRow("ICBP", "Indofood CBP", 11_200.0, -75.0, -0.67, "RG", spark(19, false)),
        StockRow("MEDC", "Medco Energi", 1_215.0, 25.0, 2.10, "RG", spark(21, true)),
        StockRow("INCO", "Vale Indonesia", 3_640.0, -40.0, -1.09, "RG", spark(23, false)),
    )

    val trending = listOf(
        watchlist[7], watchlist[5], watchlist[10], watchlist[0], watchlist[8],
    )

    val presets = listOf(
        ScreenPreset("deep-value", "Deep Value", "PBV < 1 · PER < 10 · ROE > 12%", 34),
        ScreenPreset("momentum", "Momentum Breakout", "Harga > MA50 · Vol > 2× avg", 21),
        ScreenPreset("dividend", "High Dividend", "Yield > 5% · payout stabil 3thn", 18),
        ScreenPreset("foreign-flow", "Foreign Accumulation", "Net foreign buy 5D > 0", 27),
        ScreenPreset("oversold", "Oversold Reversal", "RSI < 30 · dekat support", 12),
        ScreenPreset("growth", "Earnings Growth", "EPS growth YoY > 20%", 29),
    )

    val insiders = listOf(
        InsiderTx("BBCA", "Robert Budi Hartono", "27 Jul 26", "BUY", 54_120_000.0, 53_980_000.0, 9_650.0, "Direct", "IDX"),
        InsiderTx("ADRO", "Garibaldi Thohir", "26 Jul 26", "SELL", 1_240_000.0, 1_460_000.0, 2_460.0, "Direct", "IDX"),
        InsiderTx("ANTM", "Inalum (Persero)", "25 Jul 26", "BUY", 65_000_000.0, 64_500_000.0, 1_585.0, "Corp", "IDX"),
        InsiderTx("GOTO", "SoftBank Vision Fund", "24 Jul 26", "SELL", 8_900_000_000.0, 9_100_000_000.0, 74.0, "Fund", "IDX"),
    )

    fun candles(symbol: String): List<Candle> {
        val base = watchlist.firstOrNull { it.code == symbol.uppercase() }?.price ?: 5_000.0
        val months = listOf("Feb", "Mar", "Apr", "May", "Jun", "Jul")
        return List(92) { i ->
            val drift = sin(i * 0.22) * base * 0.04 + i * base * 0.0006
            val close = base * 0.9 + drift
            val open = close - sin(i * 0.5) * base * 0.01
            val hi = maxOf(open, close) + base * 0.008
            val lo = minOf(open, close) - base * 0.008
            Candle(
                timeSec = 1_760_000_000L + i * 86_400L,
                date = "${(i % 28) + 1} ${months[i / 16 % months.size]}",
                open = open, high = hi, low = lo, close = close,
                volume = 1_000_000.0 + i * 25_000.0,
            )
        }
    }

    // IHSG header
    const val IHSG_PRICE = 7_432.18
    const val IHSG_CHG = 45.62
    const val IHSG_PCT = 0.62
}
