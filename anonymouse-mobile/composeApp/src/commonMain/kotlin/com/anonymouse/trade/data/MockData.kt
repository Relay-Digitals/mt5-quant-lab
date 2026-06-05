package com.anonymouse.trade.data

import androidx.compose.ui.graphics.Color
import kotlin.math.abs
import kotlin.random.Random

/**
 * DB — sumber data dummy (setara data.js). Akan diganti BridgeRepository (data quant asli)
 * begitu bridge API + endpoint quant tersambung. Disimpan deterministik (seed) agar stabil.
 */
object DB {
    /** deret equity acak-tapi-stabil (mirip DB.series(start, n, drift, vol, seed)). */
    fun series(start: Double, n: Int, drift: Double, vol: Double, seed: Int): List<Float> {
        val rnd = Random(seed)
        var v = start
        return List(n) {
            v *= (1 + drift / n + (rnd.nextDouble() - 0.5) * vol)
            v.toFloat()
        }
    }

    val portfolio = Portfolio(
        balance = 48230.0,
        pnlToday = 2.4,
        pnl30 = 18.6,
        winRate = 68,
        openPositions = 4,
        equity = series(40000.0, 60, 0.2, 0.012, 7),
        allocation = listOf(
            AllocSeg("BTC", 42, Color(0xFFF7931A)),
            AllocSeg("ETH", 28, Color(0xFF7A5AE0)),
            AllocSeg("IDX", 18, Color(0xFF00E5A0)),
            AllocSeg("Cash", 12, Color(0xFF5F6B7A)),
        ),
        activity = listOf(
            Activity("signal", "New BTC/USDT LONG from AlphaQuant", "2m"),
            Activity("backtest", "Backtest TREND EUR/USD completed (+12.3%)", "1h"),
            Activity("win", "SOL/USDT closed +6.1%", "3h"),
            Activity("loss", "ADA/USDT stopped -2.4%", "5h"),
            Activity("billing", "Subscription renewed · AlphaQuant", "1d"),
        ),
    )

    val providers = listOf(
        Provider("p1", "AlphaQuant", "AQ"),
        Provider("p2", "WhaleSignals", "WS"),
        Provider("p3", "RegimeBot", "RB"),
    )
    fun providerById(id: String) = providers.find { it.id == id } ?: providers[0]

    val signals = listOf(
        Signal("s1", "BTC/USDT", "LONG", 67420.0, 3.42, series(100.0, 24, 0.1, 0.03, 11), "active", "p1"),
        Signal("s2", "ETH/USDT", "LONG", 3540.0, 1.98, series(100.0, 24, 0.08, 0.03, 12), "active", "p2"),
        Signal("s3", "SOL/USDT", "SHORT", 178.4, -1.2, series(100.0, 24, -0.05, 0.04, 13), "active", "p3"),
        Signal("s4", "EUR/USD", "LONG", 1.0842, 0.6, series(100.0, 24, 0.03, 0.01, 14), "active", "p3"),
        Signal("s5", "XAU/USD", "LONG", 2654.0, 2.1, series(100.0, 24, 0.07, 0.02, 15), "active", "p1"),
        Signal("s6", "BBRI", "SHORT", 4080.0, 4.0, series(100.0, 24, -0.08, 0.03, 16), "closed", "p2"),
    )

    val strategies = listOf(
        Strategy("trend", "Trend / Donchian", "Donchian20 + SMA50 breakout"),
        Strategy("meanrev", "Mean Reversion", "Bollinger + RSI oversold"),
        Strategy("regime", "Regime-aware", "TREND@ADX≥25 + MR@ADX<20"),
        Strategy("ara", "ARA Hunter", "Gorengan momentum day-trade"),
    )

    val pairsList = listOf("BTC/USDT", "ETH/USDT", "SOL/USDT", "EUR/USD", "USD/JPY", "XAU/USD", "BBRI", "BMRI")

    val markets = linkedMapOf(
        "crypto" to Market("crypto", "Crypto", "₿", Color(0xFFF7931A), "Binance · USDT-M", listOf(Instrument("BTC/USDT"), Instrument("ETH/USDT"), Instrument("SOL/USDT"))),
        "forex" to Market("forex", "Forex", "$", Color(0xFF2A9FFF), "Exness · MT5", listOf(Instrument("EUR/USD"), Instrument("USD/JPY"), Instrument("XAU/USD"))),
        "idx" to Market("idx", "IDX", "Rp", Color(0xFF00E5A0), "Stockbit · IDX", listOf(Instrument("BBRI"), Instrument("BMRI"), Instrument("BBCA"))),
    )

    fun paperPositions(mk: String): List<PaperPosition> = when (mk) {
        "idx" -> listOf(
            PaperPosition("BBRI", "LONG", "12 lot", 4080.0, 4180.0, 2.45),
            PaperPosition("BMRI", "LONG", "8 lot", 4080.0, 4040.0, -0.98),
            PaperPosition("ANTM", "LONG", "20 lot", 1620.0, 1685.0, 4.01),
        )
        "forex" -> listOf(
            PaperPosition("AUDJPY", "LONG", "0.5", 97.42, 97.88, 1.12),
            PaperPosition("XAUUSD", "LONG", "0.1", 2654.0, 2671.0, 0.64),
            PaperPosition("CHFJPY", "SHORT", "0.3", 168.2, 167.6, 0.36),
        )
        else -> listOf(
            PaperPosition("BTC/USDT", "LONG", "0.12", 67420.0, 68900.0, 2.19),
            PaperPosition("ETH/USDT", "LONG", "1.4", 3540.0, 3612.0, 2.03),
            PaperPosition("SOL/USDT", "SHORT", "18", 178.4, 174.1, 2.41),
        )
    }

    val notifChannels = listOf(
        NotifChannel("wa", "WhatsApp", "+62 896···294", Color(0xFF25D366), true),
        NotifChannel("tg", "Telegram", "@anon_alerts", Color(0xFF2A9FFF), true),
        NotifChannel("dc", "Discord", "not linked", Color(0xFF7A5AE0), false),
    )
    val notifEvents = listOf(
        NotifEvent("entry", "New entry signal", true),
        NotifEvent("tp", "Take-profit hit", true),
        NotifEvent("sl", "Stop-loss / ignition exit", true),
        NotifEvent("daily", "Daily summary", false),
    )
    val vpsId = "ct108 · proxmox"

    /** simulasi backtest (akan diganti panggilan bridge → skrip quant). */
    fun runBacktest(cfg: BacktestCfg): BacktestResult {
        val rnd = Random(cfg.pair.hashCode() + cfg.strategy.hashCode() + cfg.period)
        val ret = (rnd.nextDouble() * 60 - 15)
        val curve = series(cfg.capital.toDouble(), cfg.period.coerceAtMost(120), ret / 100, 0.02, rnd.nextInt(999))
        val nTrades = 14 + rnd.nextInt(40)
        val trades = List(nTrades) { i ->
            val win = rnd.nextDouble() < 0.55
            val pnl = (if (win) 1 else -1) * (cfg.capital * cfg.riskPct / 100) * (0.4 + rnd.nextDouble() * 1.6)
            BacktestTrade(i + 1, if (rnd.nextBoolean()) "LONG" else "SHORT", rnd.nextInt(cfg.period) + 1, pnl, win)
        }
        val wins = trades.count { it.win }
        val gp = trades.filter { it.win }.sumOf { it.pnl }
        val gl = abs(trades.filter { !it.win }.sumOf { it.pnl }).takeIf { it > 0 } ?: 1.0
        return BacktestResult(
            stats = BacktestStats(
                totalReturn = (curve.last() / cfg.capital - 1) * 100.0,
                finalEquity = curve.last().toInt(),
                winRate = (wins * 100 / nTrades),
                profitFactor = (gp / gl),
                maxDD = (4 + rnd.nextDouble() * 16),
                sharpe = (0.4 + rnd.nextDouble() * 2.2),
            ),
            curve = curve, trades = trades
        )
    }
}

fun Double.r2(): String {
    val r = (this * 100).toLong() / 100.0
    return r.toString()
}
