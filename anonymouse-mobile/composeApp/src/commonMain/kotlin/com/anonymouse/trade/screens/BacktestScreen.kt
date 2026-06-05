package com.anonymouse.trade.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.anonymouse.trade.AppState
import com.anonymouse.trade.ToastData
import com.anonymouse.trade.data.*
import com.anonymouse.trade.theme.Dimens
import com.anonymouse.trade.theme.theme
import com.anonymouse.trade.ui.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@Composable
fun BacktestScreen(st: AppState) {
    val pal = theme
    var cfg by remember { mutableStateOf(BacktestCfg()) }
    var result by remember { mutableStateOf<BacktestResult?>(null) }
    var running by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    // (B) strategi + pair dari server
    var meta by remember { mutableStateOf<MetaDto?>(null) }
    LaunchedEffect(Unit) {
        bridgeApi()?.let { api ->
            runCatching { api.getMeta() }.getOrNull()?.let { meta = parseMeta(it) }
        }
    }
    val strategies = meta?.strategies?.map { Strategy(it.id, it.name, it.desc) } ?: DB.strategies
    val pairs = meta?.pairs ?: DB.pairsList

    // riwayat backtest (RAG) + chart full-screen
    var showRuns by remember { mutableStateOf(false) }
    var runs by remember { mutableStateOf<List<RunDto>>(emptyList()) }
    var fullChart by remember { mutableStateOf<List<Float>?>(null) }
    fun loadRuns() {
        scope.launch { bridgeApi()?.let { api -> runCatching { api.getRuns(40) }.getOrNull()?.let { runs = parseRuns(it) } } }
    }

    fun run() {
        scope.launch {
            running = true; result = null; status = "Menjalankan engine backtest…"
            val api = bridgeApi()
            if (api == null) {
                delay(700); result = DB.runBacktest(cfg); running = false
                st.push(ToastData("Backtest (estimasi)", "Bridge belum dikonfigurasi — pakai data dummy", "backtest")); return@launch
            }
            // (C) endpoint engine cepat (detik)
            val text = runCatching { api.getBacktest(cfg.strategy, cfg.pair, cfg.capital, cfg.riskPct, cfg.period) }.getOrNull()
            val parsed = text?.let { parseBacktest(it) }
            result = parsed ?: DB.runBacktest(cfg)
            running = false
            if (parsed == null) st.push(ToastData("Backtest", "Engine tak balas — tampil estimasi (cek bridge/symbol).", "backtest"))
            else st.push(ToastData("Backtest selesai · engine",
                "${if (parsed.stats.totalReturn >= 0) "+" else ""}${parsed.stats.totalReturn.round1()}% · PF ${parsed.stats.profitFactor.round2()} · ${cfg.period}d", "backtest"))
        }
    }

    Column(Modifier.fillMaxSize()) {
        TopBar("Backtest", "Replay a strategy on historical data", big = true,
            right = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    IconBtn("backtest") { showRuns = !showRuns; if (showRuns && runs.isEmpty()) loadRuns() }
                    IconBtn("chat") { st.showChat = true }
                }
            })
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp)) {
            if (showRuns) {
                MCard(pad = 0.dp) {
                    Row(Modifier.fillMaxWidth().padding(14.dp), horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically) {
                        Head("Past runs (RAG)", 15)
                        TextUi("${runs.size} riwayat", 11, color = pal.textMute)
                    }
                    if (runs.isEmpty()) Row(Modifier.padding(14.dp)) { TextUi("memuat riwayat…", 12, color = pal.textMute) }
                    runs.take(40).forEachIndexed { i, r ->
                        if (i > 0) Box(Modifier.fillMaxWidth().height(1.dp).background(pal.borderSoft))
                        Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 10.dp),
                            verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            Column(Modifier.weight(1f)) {
                                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                    Mono(r.symbol, 13, FontWeight.Bold); Badge(r.strategy, Tone.neutral)
                                }
                                TextUi("${r.tf} · ${r.trades} tr · WR ${r.winRate.round1()}% · DD ${r.maxDD.round1()}% · ${r.at}", 10, color = pal.textMute)
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Mono((if (r.ret >= 0) "+" else "") + "${r.ret.round1()}%", 13, FontWeight.Bold, if (r.ret >= 0) pal.up else pal.down)
                                Mono("PF ${r.pf.round2()}", 10, FontWeight.Normal, pal.textMute)
                            }
                        }
                    }
                }
                Spacer(Modifier.height(Dimens.gap))
            }
            TextUi("Strategy", 12, FontWeight.SemiBold, pal.textDim, modifier = Modifier.padding(start = 2.dp, bottom = 10.dp))
            // strategy grid 2 cols
            val rows = strategies.chunked(2)
            rows.forEach { rowItems ->
                Row(Modifier.fillMaxWidth().padding(bottom = 9.dp), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                    rowItems.forEach { sgy ->
                        val on = cfg.strategy == sgy.id
                        Column(Modifier.weight(1f).clip(RoundedCornerShape(12.dp))
                            .background(if (on) pal.accent.copy(alpha = 0.10f) else pal.surface)
                            .border(1.dp, if (on) pal.accent else pal.border, RoundedCornerShape(12.dp))
                            .clickable { cfg = cfg.copy(strategy = sgy.id) }.padding(12.dp)) {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically) {
                                TextUi(sgy.name, 13, FontWeight.Bold)
                                if (on) Icon("check", 15.dp, pal.accent)
                            }
                            Spacer(Modifier.height(4.dp))
                            TextUi(sgy.desc, 11, color = pal.textMute)
                        }
                    }
                    if (rowItems.size == 1) Spacer(Modifier.weight(1f))
                }
            }
            Spacer(Modifier.height(6.dp))

            MCard {
                TextUi("Pair", 12, FontWeight.SemiBold, pal.textDim, modifier = Modifier.padding(bottom = 9.dp))
                ChipRow {
                    pairs.forEach { pr -> Chip(pr, cfg.pair == pr) { cfg = cfg.copy(pair = pr) } }
                }
                Spacer(Modifier.height(16.dp))
                MSlider("Starting capital", cfg.capital.toFloat(), 1000f, 100000f, onChange = { cfg = cfg.copy(capital = it.toInt()) }, fmt = { "$" + it.toDouble().fmt0() })
                MSlider("Risk per trade", cfg.riskPct, 0.5f, 10f, onChange = { cfg = cfg.copy(riskPct = it) }, fmt = { "${it.round1()}%" })
                MSlider("Period", cfg.period.toFloat(), 30f, 365f, onChange = { cfg = cfg.copy(period = it.toInt()) }, fmt = { "${it.toInt()} days" })
                Btn(if (running) "Running…" else "Run backtest", BtnVariant.primary, full = true,
                    icon = if (running) null else "play", enabled = !running) { run() }
            }
            Spacer(Modifier.height(Dimens.gap))

            if (running) {
                MCard {
                    Column(Modifier.fillMaxWidth().padding(vertical = 24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Spinner(); Spacer(Modifier.height(16.dp))
                        Head("Backtest berjalan", 15)
                        Spacer(Modifier.height(6.dp))
                        Mono(status.ifEmpty { "menyiapkan…" }, 12, FontWeight.Normal, pal.textMute)
                        Spacer(Modifier.height(4.dp))
                        TextUi("dijalankan di CT108 (data nyata)", 11, color = pal.textMute)
                    }
                }
            } else if (result == null) {
                MCard {
                    Column(Modifier.fillMaxWidth().padding(vertical = 24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(Modifier.size(60.dp).clip(RoundedCornerShape(18.dp)).background(pal.accent.copy(alpha = 0.12f)),
                            contentAlignment = Alignment.Center) { Icon("backtest", 30.dp, pal.accent) }
                        Spacer(Modifier.height(16.dp))
                        Head("Configure & run", 17)
                        Spacer(Modifier.height(8.dp))
                        TextUi("Set strategy, capital and risk, then simulate against historical data.", 13, color = pal.textMute)
                    }
                }
            } else {
                BTResults(result!!, cfg, st, strategies) { fullChart = result!!.curve }
            }
            Spacer(Modifier.height(28.dp))
        }
    }
    // chart full-screen overlay
    fullChart?.let { curve ->
        Box(Modifier.fillMaxSize().background(pal.bg)) {
            Column(Modifier.fillMaxSize().padding(16.dp)) {
                Spacer(Modifier.windowInsetsTopHeight(WindowInsets.statusBars))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Head("${cfg.pair} · ${cfg.strategy}", 17)
                    IconBtn("x") { fullChart = null }
                }
                Spacer(Modifier.height(20.dp))
                Box(Modifier.weight(1f), contentAlignment = Alignment.Center) {
                    AreaChart(curve, 320.dp, if ((result?.stats?.totalReturn ?: 0.0) >= 0) pal.accent else pal.down)
                }
                TextUi("equity curve · ${curve.size} titik · tap ✕ untuk tutup", 11, color = pal.textMute,
                    modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp))
            }
        }
    }
}

@Composable
private fun BTResults(result: BacktestResult, cfg: BacktestCfg, st: AppState, strategies: List<Strategy>, onExpand: () -> Unit) {
    val pal = theme
    val scope = rememberCoroutineScope()
    val s = result.stats
    val good = s.totalReturn >= 0
    MCard {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                    Head((strategies.firstOrNull { it.id == cfg.strategy }?.name ?: cfg.strategy), 15)
                    Badge(cfg.pair, Tone.neutral, mono = true)
                }
                TextUi("$${cfg.capital.toDouble().fmt0()} · ${cfg.riskPct.round1()}% risk · ${cfg.period}d · M15", 11, color = pal.textMute)
            }
            IconBtn("layers") { onExpand() }
        }
        Spacer(Modifier.height(12.dp))
        Box(Modifier.clickable { onExpand() }) { AreaChart(result.curve, 170.dp, if (good) pal.accent else pal.down) }
    }
    Spacer(Modifier.height(Dimens.gap))
    val tiles = listOf(
        Triple("Total return", (if (good) "+" else "") + "${s.totalReturn.round1()}%", if (good) pal.up else pal.down),
        Triple("Final equity", "$${s.finalEquity.toDouble().fmt0()}", pal.text),
        Triple("Win rate", "${s.winRate}%", pal.text),
        Triple("Profit factor", s.profitFactor.round2(), if (s.profitFactor >= 1) pal.up else pal.down),
        Triple("Max drawdown", "-${s.maxDD.round1()}%", pal.down),
        Triple("Sharpe", s.sharpe.round2(), pal.text),
    )
    tiles.chunked(3).forEach { row ->
        Row(Modifier.fillMaxWidth().padding(bottom = 9.dp), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            row.forEach { (l, v, c) ->
                Box(Modifier.weight(1f)) {
                    MCard(pad = 13.dp) { TextUi(l, 10, FontWeight.SemiBold, pal.textMute); Spacer(Modifier.height(6.dp)); Mono(v, 16, FontWeight.Bold, c) }
                }
            }
        }
    }
    MCard(pad = 0.dp) {
        Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically) {
            Head("Trade log", 15)
            Btn("CSV", BtnVariant.soft, icon = "download") {
                scope.launch {
                    val msg = shareCsv("backtest_${cfg.strategy}_${cfg.pair}_${cfg.period}d.csv", tradesToCsv(cfg, result))
                    st.push(ToastData("Export CSV", msg, "download"))
                }
            }
        }
        result.trades.take(14).forEachIndexed { i, t ->
            if (i > 0) Box(Modifier.fillMaxWidth().height(1.dp).background(pal.borderSoft))
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 11.dp),
                verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(11.dp)) {
                Mono("#${t.n}", 11, FontWeight.Normal, pal.textMute)
                DirTag(t.dir)
                Mono("D${t.day}", 12, FontWeight.Normal, pal.textMute, Modifier.weight(1f))
                Mono((if (t.pnl >= 0) "+" else "-") + "$" + kotlin.math.abs(t.pnl).fmt0(), 13, FontWeight.Bold, if (t.win) pal.up else pal.down)
                Badge(if (t.win) "WIN" else "LOSS", if (t.win) Tone.up else Tone.down)
            }
        }
    }
}

@Composable
fun Spinner() {
    val pal = theme
    Box(Modifier.size(50.dp).clip(RoundedCornerShape(99.dp)).border(3.dp, pal.surface3, RoundedCornerShape(99.dp)),
        contentAlignment = Alignment.Center) { Icon("refresh", 26.dp, pal.accent) }
}

fun Double.round1(): String { val r = kotlin.math.round(this * 10) / 10.0; return r.toString() }
fun Double.round2(): String { val r = kotlin.math.round(this * 100) / 100.0; return r.toString() }
fun Float.round1(): String = this.toDouble().round1()
