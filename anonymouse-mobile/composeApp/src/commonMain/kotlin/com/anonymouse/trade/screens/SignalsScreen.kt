package com.anonymouse.trade.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.anonymouse.trade.AppState
import com.anonymouse.trade.data.*
import com.anonymouse.trade.theme.theme
import com.anonymouse.trade.ui.*

@Composable
fun SignalsScreen(st: AppState) {
    val pal = theme
    val filters = listOf("All", "Posisi", "Kandidat", "Forex", "IDX")
    var filter by remember { mutableStateOf("All") }
    var refreshKey by remember { mutableStateOf(0) }
    var sigs by remember { mutableStateOf(mockSignals()) }
    var loading by remember { mutableStateOf(false) }
    var live by remember { mutableStateOf(false) }

    LaunchedEffect(refreshKey) {
        val api = bridgeApi() ?: return@LaunchedEffect
        loading = true
        val text = runCatching { api.getCache("signals") }.getOrNull()
        val parsed = text?.let { parseSignals(it) }
        if (parsed != null) { sigs = parsed; live = true }
        loading = false
    }

    // PnL forex REAL-TIME (overlay ke posisi forex tiap 4 detik)
    var liveFx by remember { mutableStateOf<LiveForex?>(null) }
    LaunchedEffect(Unit) {
        val api = bridgeApi() ?: return@LaunchedEffect
        while (true) {
            runCatching { api.getLiveForex() }.getOrNull()?.let { parseLiveForex(it) }?.let { liveFx = it }
            kotlinx.coroutines.delay(4000)
        }
    }
    // posisi forex SELALU dari live (real Exness .111), bukan snapshot (yg bisa basi/0)
    val liveSignals = liveFx?.positions?.map { lp ->
        SignalDto(pair = lp.sym, dir = lp.side, entry = lp.entry, roi = lp.pnlPct, status = "active",
            market = "forex", strat = lp.strat, type = "position",
            note = (if (lp.pnl >= 0) "+$" else "-$") + kotlin.math.abs(lp.pnl).round2() + " · live")
    } ?: emptyList()
    val baseNoForexPos = sigs.filter { !(it.type == "position" && it.market == "forex") }
    val merged = liveSignals + baseNoForexPos

    val list = merged.filter {
        when (filter) {
            "Posisi" -> it.type == "position"
            "Kandidat" -> it.type == "ara" || it.type == "ignition" || it.status == "candidate" || it.status == "watch"
            "Forex" -> it.market == "forex"
            "IDX" -> it.market == "idx"
            else -> true
        }
    }

    Column(Modifier.fillMaxSize()) {
        TopBar("Signals", if (live) "Sinyal live dari strategimu · CT108" else "Sinyal dari strategimu", big = true,
            right = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    IconBtn("refresh") { if (!loading) refreshKey++ }
                    IconBtn("chat") { st.showChat = true }
                }
            })
        ChipRow { filters.forEach { f -> Chip(f, filter == f) { filter = f } } }
        Spacer(Modifier.height(10.dp))
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)) {
            if (loading) MCard {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Icon("refresh", 20.dp, pal.accent); TextUi("Mengambil sinyal dari server…", 13, color = pal.textDim)
                }
            }
            if (list.isEmpty() && !loading) MCard {
                TextUi("Tidak ada sinyal untuk filter ini.", 13, color = pal.textMute)
            }
            list.forEach { s -> SignalRow(s) { st.showChat = true } }
            Spacer(Modifier.height(28.dp))
        }
    }
}
