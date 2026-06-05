package com.anonymouse.trade.data

import androidx.compose.ui.graphics.Color

data class AllocSeg(val name: String, val pct: Int, val color: Color)
data class Activity(val kind: String, val txt: String, val t: String)

data class Portfolio(
    val balance: Double,
    val pnlToday: Double,
    val pnl30: Double,
    val winRate: Int,
    val openPositions: Int,
    val equity: List<Float>,
    val allocation: List<AllocSeg>,
    val activity: List<Activity>,
)

data class Provider(val id: String, val name: String, val initials: String)

data class Signal(
    val id: String,
    val pair: String,
    val dir: String,       // LONG / SHORT
    val entry: Double,
    val roi: Double,
    val spark: List<Float>,
    val status: String,    // active / closed
    val provider: String,
)

data class Strategy(val id: String, val name: String, val desc: String)

data class BacktestCfg(
    val pair: String = "XAUUSD",
    val strategy: String = "trend",
    val capital: Int = 10000,
    val riskPct: Float = 2f,
    val period: Int = 90,
    val leverage: Int = 5,
)

data class BacktestStats(
    val totalReturn: Double,
    val finalEquity: Int,
    val winRate: Int,
    val profitFactor: Double,
    val maxDD: Double,
    val sharpe: Double,
)

data class BacktestTrade(val n: Int, val dir: String, val day: Int, val pnl: Double, val win: Boolean)
data class BacktestResult(val stats: BacktestStats, val curve: List<Float>, val trades: List<BacktestTrade>)

data class Instrument(val sym: String)
data class Market(val key: String, val label: String, val glyph: String, val color: Color, val venue: String, val instruments: List<Instrument>)

data class PaperPosition(val sym: String, val side: String, val qty: String, val entry: Double, val mark: Double, val pnlPct: Double)

data class NotifChannel(val id: String, val name: String, val target: String, val color: Color, val connected: Boolean)
data class NotifEvent(val id: String, val label: String, val on: Boolean)
