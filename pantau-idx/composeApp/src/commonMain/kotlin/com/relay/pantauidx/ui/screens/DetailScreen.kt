package com.relay.pantauidx.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
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
import com.relay.pantauidx.theme.LocalPlexMono
import com.relay.pantauidx.theme.Pantau
import com.relay.pantauidx.ui.AreaChart
import com.relay.pantauidx.ui.clickableNoRipple

@Composable
fun DetailScreen(state: AppState) {
    val d = state.detailSymbol ?: return
    var range by remember { mutableStateOf("1D") }
    var dTab by remember { mutableStateOf("KEYSTATS") }
    val ranges = listOf("1D", "1W", "1M", "3M", "YTD", "1Y", "3Y", "5Y")
    val tabs = listOf("STREAM", "KEYSTATS", "ORDERBOOK", "ANALYSIS")

    Column(Modifier.fillMaxWidth()) {
        // top bar
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("‹", color = Pantau.TextMut, fontSize = 20.sp, modifier = Modifier.clickableNoRipple { state.closeDetail() })
            Row(horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                Text("✎", color = Pantau.TextDim, fontSize = 15.sp)
                Text("◷", color = Pantau.TextDim, fontSize = 15.sp)
                Text("★", color = Pantau.Amber, fontSize = 17.sp)
            }
        }

        LazyColumn(Modifier.fillMaxWidth()) {
            item {
                Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(d.code, color = Pantau.Text, fontSize = 21.sp, fontWeight = FontWeight.Bold)
                    Text(d.name, color = Pantau.TextDim, fontSize = 12.sp)
                    Text(Fmt.price(d.price), color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 34.sp, fontWeight = FontWeight.SemiBold)
                    Row(verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("${Fmt.signed(d.change)} (${Fmt.signedPct(d.changePct)})", color = Pantau.trend(d.up), fontFamily = LocalPlexMono.current, fontSize = 13.sp)
                        Text("Hari Ini", color = Pantau.TextDim, fontSize = 12.sp)
                    }
                }
            }
            item {
                val series = state.detailCandles.map { it.close }.ifEmpty { d.spark }
                AreaChart(series, Pantau.trend(d.up), Modifier.fillMaxWidth().height(180.dp).padding(horizontal = 12.dp, vertical = 14.dp))
            }
            item {
                Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 20.dp), horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                    ranges.forEach { r ->
                        Text(r, color = if (range == r) Pantau.Green else Pantau.TextDim, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
                            modifier = Modifier.clickableNoRipple { range = r }.padding(vertical = 6.dp))
                    }
                }
            }
            item {
                Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 6.dp).height(40.dp), horizontalArrangement = Arrangement.spacedBy(22.dp), verticalAlignment = Alignment.CenterVertically) {
                    tabs.forEach { t ->
                        Text(t, color = if (dTab == t) Pantau.Green else Pantau.TextDim, fontSize = 12.sp, fontWeight = FontWeight.Bold,
                            modifier = Modifier.clickableNoRipple { dTab = t })
                    }
                }
                Box(Modifier.fillMaxWidth().height(1.dp).background(Pantau.LineSoft))
            }
            item { DetailTab(dTab, d.up) }
            item {
                // buy CTA
                Row(Modifier.fillMaxWidth().padding(20.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Box(
                        Modifier.weight(1f).height(50.dp).clip(RoundedCornerShape(13.dp)).border(1.dp, Pantau.Amber, RoundedCornerShape(13.dp)),
                        contentAlignment = Alignment.Center,
                    ) { Text("+ Watchlist", color = Pantau.Amber, fontWeight = FontWeight.Bold, fontSize = 15.sp) }
                    Box(
                        Modifier.weight(1f).height(50.dp).clip(RoundedCornerShape(13.dp)).background(Pantau.Green),
                        contentAlignment = Alignment.Center,
                    ) { Text("Trade", color = Pantau.Surface, fontWeight = FontWeight.Bold, fontSize = 15.sp) }
                }
            }
        }
    }
}

@Composable
private fun DetailTab(tab: String, up: Boolean) {
    when (tab) {
        "KEYSTATS" -> KeyStats()
        "ANALYSIS" -> Analysis(up)
        "ORDERBOOK" -> OrderBook()
        else -> Box(Modifier.fillMaxWidth().padding(30.dp), contentAlignment = Alignment.Center) {
            Text("Stream · notes, berita, riset", color = Pantau.TextDim, fontSize = 13.sp)
        }
    }
}

@Composable
private fun KeyStats() {
    val stats = listOf(
        "Prev Close" to "9,525", "Open" to "9,550", "Day High" to "9,675", "Day Low" to "9,500",
        "Volume" to "42.1 M", "Value" to "405 B", "Market Cap" to "1,189 T", "PER" to "22.4",
        "PBV" to "4.8", "EPS" to "430", "Dividend Yield" to "2.6%", "52W High" to "10,950",
    )
    Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp)) {
        stats.chunked(2).forEach { pair ->
            Row(Modifier.fillMaxWidth().padding(vertical = 10.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                pair.forEach { (k, v) ->
                    Row(Modifier.weight(1f).padding(end = 12.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(k, color = Pantau.TextDim, fontSize = 12.sp)
                        Text(v, color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
                    }
                }
            }
        }
    }
}

@Composable
private fun Analysis(up: Boolean) {
    val rows = listOf(
        Triple("Foreign flow (5D)", if (up) "+Rp 184 M" else "-Rp 184 M", 0.68f),
        Triple("Broker accumulation", "62% buy", 0.62f),
        Triple("Volatility vs sector", "1.4x", 0.74f),
        Triple("Analyst consensus", "Buy 7 · Hold 3", 0.70f),
    )
    Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        rows.forEach { (label, value, pct) ->
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(label, color = Pantau.TextMut, fontSize = 12.sp)
                    Text(value, color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                }
                Box(Modifier.fillMaxWidth().height(4.dp).clip(RoundedCornerShape(999.dp)).background(Pantau.Line)) {
                    Box(Modifier.fillMaxWidth(pct).height(4.dp).clip(RoundedCornerShape(999.dp)).background(Pantau.trend(up)))
                }
            }
        }
    }
}

@Composable
private fun OrderBook() {
    val bids = listOf("9,650" to "1,204", "9,625" to "3,410", "9,600" to "5,120", "9,575" to "2,880", "9,550" to "6,240")
    val asks = listOf("9,675" to "980", "9,700" to "2,110", "9,725" to "4,050", "9,750" to "1,760", "9,775" to "3,900")
    Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 10.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("BID", color = Pantau.Green, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            bids.forEach { (p, q) ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(q, color = Pantau.TextDim, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
                    Text(p, color = Pantau.Green, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
                }
            }
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("ASK", color = Pantau.Red, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            asks.forEach { (p, q) ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(p, color = Pantau.Red, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
                    Text(q, color = Pantau.TextDim, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
                }
            }
        }
    }
}
