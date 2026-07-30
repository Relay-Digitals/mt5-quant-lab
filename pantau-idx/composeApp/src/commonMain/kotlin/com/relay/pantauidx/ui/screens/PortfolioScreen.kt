package com.relay.pantauidx.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.relay.pantauidx.AppState
import com.relay.pantauidx.data.Fmt
import com.relay.pantauidx.data.StockRow
import com.relay.pantauidx.theme.LocalPlexMono
import com.relay.pantauidx.theme.Pantau
import com.relay.pantauidx.ui.StatCell
import com.relay.pantauidx.ui.clickableNoRipple

@Composable
fun PortfolioScreen(state: AppState) {
    var tab by remember { mutableStateOf(0) }
    val holdings = state.watchlist.take(4)
    val invested = holdings.sumOf { it.price * 100 }
    val pl = holdings.sumOf { it.change * 100 }

    LazyColumn(Modifier.fillMaxWidth()) {
        item {
            // summary card
            Column(
                Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 16.dp)
                    .clip(RoundedCornerShape(16.dp)).background(Pantau.Card).border(1.dp, Pantau.Line, RoundedCornerShape(16.dp))
                    .padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(18.dp),
            ) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    StatCell("Trading Balance", "Rp " + Fmt.compact(24_500_000.0))
                    StatCell("Invested", "Rp " + Fmt.compact(invested), align = Alignment.CenterHorizontally)
                    StatCell("Open", "${holdings.size}", align = Alignment.End)
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    StatCell("P&L", Fmt.signed(pl), Pantau.trend(pl >= 0))
                    StatCell("Return", Fmt.signedPct(if (invested > 0) pl / invested * 100 else 0.0), Pantau.trend(pl >= 0), Alignment.CenterHorizontally)
                    StatCell("Total Equity", "Rp " + Fmt.compact(24_500_000.0 + invested + pl), align = Alignment.End)
                }
            }
        }
        item {
            Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp)) {
                listOf("STOCKS", "ORDER", "HISTORY").forEachIndexed { i, label ->
                    Column(
                        Modifier.weight(1f).clickableNoRipple { tab = i },
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Text(label, color = if (tab == i) Pantau.Green else Pantau.TextDim, fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 10.dp))
                        Box(Modifier.fillMaxWidth().height(2.dp).background(if (tab == i) Pantau.Green else Pantau.LineSoft))
                    }
                }
            }
        }
        when (tab) {
            0 -> items(holdings) { h -> HoldingRow(h) { state.openDetail(h) } }
            1 -> item { EmptyState("Belum ada order aktif") }
            else -> items(holdings) { h -> HistoryRow(h) }
        }
    }
}

@Composable
private fun HoldingRow(h: StockRow, onClick: () -> Unit) {
    val pl = h.change * 100
    Row(
        Modifier.fillMaxWidth().clickableNoRipple(onClick).padding(horizontal = 20.dp, vertical = 15.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(h.code, color = Pantau.Text, fontSize = 14.sp, fontWeight = FontWeight.Bold)
            Text(Fmt.compact(h.price * 100), color = Pantau.TextMut, fontFamily = LocalPlexMono.current, fontSize = 13.sp)
            Text("Invested", color = Pantau.TextDim, fontSize = 11.sp)
        }
        StatCell("P&L", Fmt.signed(pl), Pantau.trend(pl >= 0), Alignment.CenterHorizontally)
        Box(Modifier.weight(1f))
        StatCell(if (pl >= 0) "Profit" else "Loss", Fmt.signedPct(h.changePct), Pantau.trend(pl >= 0), Alignment.End)
    }
    Box(Modifier.fillMaxWidth().height(1.dp).background(Pantau.LineSoft))
}

@Composable
private fun HistoryRow(h: StockRow) {
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 14.dp),
        horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            val buy = h.up
            Box(Modifier.clip(RoundedCornerShape(5.dp)).background(if (buy) Pantau.Green.copy(alpha = 0.15f) else Pantau.Red.copy(alpha = 0.15f)).padding(horizontal = 7.dp, vertical = 2.dp)) {
                Text(if (buy) "BUY" else "SELL", color = Pantau.trend(buy), fontSize = 11.sp, fontWeight = FontWeight.Bold)
            }
            Text(h.code, color = Pantau.Text, fontSize = 14.sp, fontWeight = FontWeight.Bold)
        }
        Text(Fmt.price(h.price), color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 13.sp)
    }
    Box(Modifier.fillMaxWidth().height(1.dp).background(Pantau.LineSoft))
}

@Composable
private fun EmptyState(msg: String) {
    Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) {
        Text(msg, color = Pantau.TextDim, fontSize = 13.sp)
    }
}
