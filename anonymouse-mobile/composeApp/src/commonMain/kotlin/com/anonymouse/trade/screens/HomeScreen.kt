package com.anonymouse.trade.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.anonymouse.trade.AppState
import com.anonymouse.trade.ToastData
import com.anonymouse.trade.data.*
import com.anonymouse.trade.theme.Dimens
import com.anonymouse.trade.theme.theme
import com.anonymouse.trade.ui.*

@Composable
fun HomeScreen(st: AppState) {
    val pal = theme
    val ranges = listOf("24h", "7d", "30d", "All")
    var range by remember { mutableStateOf("30d") }
    var refreshKey by remember { mutableStateOf(0) }
    var home by remember { mutableStateOf(mockHome()) }
    var loading by remember { mutableStateOf(false) }

    LaunchedEffect(refreshKey) {
        val api = bridgeApi() ?: return@LaunchedEffect
        loading = true
        val text = runCatching { api.getCache("home") }.getOrNull()
        home = text?.let { parseHome(it) } ?: home
        loading = false
    }

    // PnL forex REAL-TIME (poll 4 detik) → overlay portfolio value + active signals
    var liveFx by remember { mutableStateOf<LiveForex?>(null) }
    LaunchedEffect(Unit) {
        val api = bridgeApi() ?: return@LaunchedEffect
        while (true) {
            runCatching { api.getLiveForex() }.getOrNull()?.let { parseLiveForex(it) }?.let { liveFx = it }
            kotlinx.coroutines.delay(4000)
        }
    }
    val liveSig = liveFx?.positions?.map { lp ->
        SignalDto(pair = lp.sym, dir = lp.side, entry = lp.entry, roi = lp.pnlPct, status = "active",
            market = "forex", strat = lp.strat, type = "position",
            note = (if (lp.pnl >= 0) "+$" else "-$") + kotlin.math.abs(lp.pnl).round2() + " · live")
    } ?: emptyList()
    val activeSignals = (liveSig + home.signals.filter { !(it.type == "position" && it.market == "forex") }).take(4)
    val balanceLive = liveFx?.balance ?: home.balance

    val curr = home.currency
    fun money(n: Double) = if (curr == "IDR") "Rp " + n.fmt0() else "$" + n.fmt0()
    val equity = home.equity.map { it.toFloat() }.ifEmpty { listOf(home.balance.toFloat(), home.balance.toFloat()) }
    val allocColors = listOf(pal.warn, pal.violet, pal.accent, pal.up, pal.down, pal.textMute)

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp)) {
        TopBar(
            title = "Good morning", sub = "@anonwhale · ${if (home.source == "mock") "demo data" else "live · CT108"}", big = true,
            right = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    IconBtn(if (loading) "refresh" else "refresh") { if (!loading) refreshKey++ }
                    IconBtn("chat") { st.showChat = true }
                    Box(Modifier.clickable { st.showSettings = true }) { Avatar("A", 40.dp) }
                }
            }
        )

        // portfolio hero
        MCard(glow = true, modifier = Modifier.background(
            Brush.linearGradient(listOf(pal.accent.copy(alpha = 0.08f), pal.violet.copy(alpha = 0.07f))),
            RoundedCornerShape(Dimens.radius))) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Icon("wallet", 14.dp, pal.accent); TextUi("Portfolio value", 12, FontWeight.SemiBold, pal.textMute)
                    }
                    Spacer(Modifier.height(6.dp))
                    Mono(money(balanceLive), 34, FontWeight.Bold)
                }
                Badge((if (home.pnlToday >= 0) "▲ " else "▼ ") + "${home.pnlToday.round2()}% today",
                    if (home.pnlToday >= 0) Tone.up else Tone.down, mono = true)
            }
            Spacer(Modifier.height(14.dp))
            Row(Modifier.clip(RoundedCornerShape(10.dp)).background(pal.surface2).padding(4.dp),
                horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                ranges.forEach { x ->
                    val on = range == x
                    Box(Modifier.clip(RoundedCornerShape(7.dp)).background(if (on) pal.accent else Color.Transparent)
                        .clickable { range = x }.padding(horizontal = 13.dp, vertical = 6.dp)) {
                        Mono(x, 12, FontWeight.Bold, if (on) pal.accentInk else pal.textDim)
                    }
                }
            }
            Spacer(Modifier.height(10.dp))
            AreaChart(equity, 150.dp)
            Row(Modifier.fillMaxWidth().padding(top = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                TextUi("30d change", 12, color = pal.textMute)
                Mono("${if (home.pnl30 >= 0) "+" else ""}${home.pnl30.round2()}% · ${if (home.pnl30 >= 0) "+" else "-"}${money(kotlin.math.abs(home.balance * home.pnl30 / 100))}",
                    12, FontWeight.Bold, if (home.pnl30 >= 0) pal.up else pal.down)
            }
        }
        Spacer(Modifier.height(Dimens.gap))

        // quick stats
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Box(Modifier.weight(1f)) { MStat("Win rate", "${home.winRate}%", "recent trades", icon = "chart") }
            Box(Modifier.weight(1f)) { MStat("Open positions", "${home.openPositions}", if (home.source == "mock") "demo" else "live", icon = "layers") }
        }
        Spacer(Modifier.height(Dimens.gap))

        // allocation
        if (home.allocation.isNotEmpty()) {
            MCard {
                TextUi("Allocation", 13, FontWeight.SemiBold, pal.textMute)
                Spacer(Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Donut(home.allocation.mapIndexed { i, a -> DonutSeg(a.name, a.pct.toFloat(), allocColors[i % allocColors.size]) }, 104.dp)
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Mono("${home.allocation.size}", 17, FontWeight.Bold); TextUi("assets", 9, color = pal.textMute)
                        }
                    }
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        home.allocation.forEachIndexed { i, a ->
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                                Box(Modifier.size(9.dp).clip(RoundedCornerShape(3.dp)).background(allocColors[i % allocColors.size]))
                                TextUi(a.name, 13, FontWeight.SemiBold, modifier = Modifier.weight(1f))
                                Mono("${a.pct}%", 13, FontWeight.SemiBold, pal.textDim)
                            }
                        }
                    }
                }
            }
            Spacer(Modifier.height(Dimens.gap))
        }

        // active signals (dari data nyata)
        Row(Modifier.fillMaxWidth().padding(horizontal = 4.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Head("Active signals", 17)
            Row(Modifier.clickable { st.go("signals") }, verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                TextUi("View all", 13, FontWeight.Bold, pal.accent); Icon("arrowRight", 14.dp, pal.accent)
            }
        }
        Spacer(Modifier.height(8.dp))
        if (activeSignals.isEmpty()) {
            MCard { TextUi("Tidak ada posisi/sinyal aktif.", 13, color = pal.textMute) }
        } else Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            activeSignals.forEach { s -> SignalRow(s) }
        }
        Spacer(Modifier.height(Dimens.gap))

        // recent activity
        if (home.activity.isNotEmpty()) {
            Head("Recent activity", 17, modifier = Modifier.padding(horizontal = 4.dp))
            Spacer(Modifier.height(8.dp))
            MCard(pad = 0.dp) {
                home.activity.forEachIndexed { i, a ->
                    val tone = when (a.kind) {
                        "signal" -> pal.accent; "backtest" -> pal.violet; "win" -> pal.up; "loss" -> pal.down; else -> pal.warn
                    }
                    val ic = when (a.kind) {
                        "signal" -> "signals"; "backtest" -> "backtest"; "win" -> "arrowUp"; "loss" -> "arrowDown"; else -> "wallet"
                    }
                    if (i > 0) Box(Modifier.fillMaxWidth().height(1.dp).background(pal.borderSoft))
                    Row(Modifier.padding(horizontal = 15.dp, vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Box(Modifier.size(30.dp).clip(RoundedCornerShape(9.dp)).background(tone.copy(alpha = 0.15f)),
                            contentAlignment = Alignment.Center) { Icon(ic, 15.dp, tone) }
                        Column(Modifier.weight(1f)) { TextUi(a.txt, 13); Mono(a.t, 11, FontWeight.Normal, pal.textMute) }
                    }
                }
            }
        }
        Spacer(Modifier.height(24.dp))
    }
}

/** baris sinyal/posisi (dipakai Home & Signals). */
@Composable
fun SignalRow(s: SignalDto, onClick: (() -> Unit)? = null) {
    val pal = theme
    val initials = (s.strat.ifEmpty { s.market }).take(2).uppercase()
    fun price(n: Double) = if (s.market == "idx") "Rp" + n.fmt0() else if (n < 1000) (kotlin.math.round(n * 10000) / 10000.0).toString() else "$" + n.fmt0()
    val tag: Pair<String, Tone>? = when (s.status) {
        "candidate" -> "kandidat" to Tone.accent
        "watch" -> "ignition" to Tone.warn
        "closed" -> "closed" to Tone.neutral
        else -> null
    }
    val vd: Pair<String, Tone>? = when (s.verdict) {
        "green" -> "🟢 aman" to Tone.up
        "amber" -> "🟡 hati2" to Tone.warn
        "red" -> "🔴 risiko" to Tone.down
        else -> null
    }
    val sub = s.note.ifEmpty { "${s.strat.ifEmpty { s.market }} · entry ${price(s.entry)}" }
    MCard(pad = 13.dp, onClick = onClick) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Avatar(initials, 38.dp)
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Mono(s.pair, 14, FontWeight.Bold); DirTag(s.dir)
                    if (tag != null) Badge(tag.first, tag.second)
                    if (vd != null) Badge(vd.first, vd.second)
                }
                TextUi(sub, 11, color = pal.textMute)
            }
            Mono((if (s.roi >= 0) "+" else "") + "${s.roi.round2()}%", 14, FontWeight.Bold, if (s.roi >= 0) pal.up else pal.down)
        }
    }
}

@Composable
fun IconBtn(icon: String, dot: Boolean = false, onClick: () -> Unit) {
    val pal = theme
    Box(Modifier.size(40.dp).clip(RoundedCornerShape(12.dp)).background(pal.surface2)
        .clickable { onClick() }, contentAlignment = Alignment.Center) {
        Icon(icon, 19.dp, pal.textDim)
        if (dot) Box(Modifier.align(Alignment.TopEnd).padding(9.dp).size(7.dp)
            .clip(RoundedCornerShape(99.dp)).background(pal.down))
    }
}

fun Double.fmt0(): String {
    val n = this.toLong()
    val s = n.toString()
    val sb = StringBuilder()
    val neg = s.startsWith("-")
    val digits = if (neg) s.drop(1) else s
    for ((idx, c) in digits.withIndex()) {
        if (idx > 0 && (digits.length - idx) % 3 == 0) sb.append(',')
        sb.append(c)
    }
    return (if (neg) "-" else "") + sb.toString()
}
