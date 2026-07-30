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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
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
import com.relay.pantauidx.data.SampleData
import com.relay.pantauidx.data.StockRow
import com.relay.pantauidx.theme.LocalPlexMono
import com.relay.pantauidx.theme.Pantau
import com.relay.pantauidx.ui.Sparkline
import com.relay.pantauidx.ui.SymbolBadge
import com.relay.pantauidx.ui.Pill
import com.relay.pantauidx.ui.clickableNoRipple

private enum class Sort { CODE, GAIN, LOSS, VALUE }

@Composable
fun WatchlistScreen(state: AppState) {
    var sort by remember { mutableStateOf(Sort.CODE) }
    val rows = remember(sort, state.watchlist.size) {
        when (sort) {
            Sort.CODE -> state.watchlist.sortedBy { it.code }
            Sort.GAIN -> state.watchlist.sortedByDescending { it.changePct }
            Sort.LOSS -> state.watchlist.sortedBy { it.changePct }
            Sort.VALUE -> state.watchlist.sortedByDescending { it.price }
        }
    }

    Column(Modifier.fillMaxWidth()) {
        // header
        Row(
            Modifier.fillMaxWidth().padding(start = 20.dp, end = 20.dp, top = 6.dp, bottom = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column {
                Text("STOCKPICK", color = Pantau.TextDim, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
                Text("Watchlist", color = Pantau.Text, fontSize = 22.sp, fontWeight = FontWeight.Bold)
            }
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Box(
                    Modifier.size(38.dp).clip(RoundedCornerShape(12.dp)).border(1.dp, Pantau.Line, RoundedCornerShape(12.dp)),
                    contentAlignment = Alignment.Center,
                ) { Text("${state.watchlist.size}", color = Pantau.Amber, fontFamily = LocalPlexMono.current, fontSize = 13.sp) }
                Box(
                    Modifier.size(38.dp).clip(RoundedCornerShape(12.dp)).background(Pantau.Amber)
                        .clickableNoRipple { state.select(com.relay.pantauidx.Tab.MARKET) },
                    contentAlignment = Alignment.Center,
                ) { Text("+", color = Pantau.Surface, fontSize = 20.sp, fontWeight = FontWeight.SemiBold) }
            }
        }

        // sort pills
        Row(
            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 20.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Pill("A–Z", sort == Sort.CODE) { sort = Sort.CODE }
            Pill("Top gain", sort == Sort.GAIN) { sort = Sort.GAIN }
            Pill("Top loss", sort == Sort.LOSS) { sort = Sort.LOSS }
            Pill("Value", sort == Sort.VALUE) { sort = Sort.VALUE }
        }

        IhsgCard()

        LazyColumn(Modifier.fillMaxWidth()) {
            items(rows) { row -> StockRowItem(row) { state.openDetail(row) } }
            item {
                Text(
                    if (state.isLive) "LIVE · STOCKBIT EXODUS" else "DELAYED · SIMULATED DATA",
                    color = Pantau.TextFaint, fontFamily = LocalPlexMono.current, fontSize = 11.sp,
                    modifier = Modifier.padding(20.dp),
                )
            }
        }
    }
}

@Composable
fun IhsgCard() {
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 10.dp)
            .clip(RoundedCornerShape(14.dp)).background(Pantau.Card)
            .border(1.dp, Pantau.Line, RoundedCornerShape(14.dp))
            .padding(horizontal = 14.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column {
            Text("IHSG", color = Pantau.TextDim, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
            Text(Fmt.thousands(SampleData.IHSG_PRICE, 2), color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
        }
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Sparkline(
                SampleData.watchlist[0].spark, Pantau.Green,
                Modifier.size(width = 86.dp, height = 30.dp),
            )
            Column(horizontalAlignment = Alignment.End) {
                Text(Fmt.signed(SampleData.IHSG_CHG, 2), color = Pantau.Green, fontFamily = LocalPlexMono.current, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                Text(Fmt.signedPct(SampleData.IHSG_PCT), color = Pantau.Green, fontFamily = LocalPlexMono.current, fontSize = 11.sp)
            }
        }
    }
}

@Composable
fun StockRowItem(row: StockRow, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clickableNoRipple(onClick).padding(horizontal = 20.dp, vertical = 13.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SymbolBadge(row.code)
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(row.code, color = Pantau.Text, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                Box(
                    Modifier.clip(RoundedCornerShape(4.dp)).background(Pantau.Line).padding(horizontal = 5.dp, vertical = 1.dp),
                ) { Text(row.board, color = Pantau.TextDim, fontSize = 9.sp, fontWeight = FontWeight.SemiBold) }
            }
            Text(row.name, color = Pantau.TextDim, fontSize = 11.sp, maxLines = 1)
        }
        if (row.spark.isNotEmpty()) {
            Sparkline(row.spark, Pantau.trend(row.up), Modifier.size(width = 76.dp, height = 26.dp))
        }
        Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(Fmt.price(row.price), color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 15.sp, fontWeight = FontWeight.SemiBold)
            Text(Fmt.signedPct(row.changePct), color = Pantau.trend(row.up), fontFamily = LocalPlexMono.current, fontSize = 11.sp)
        }
    }
    Box(Modifier.fillMaxWidth().height(1.dp).background(Pantau.LineSoft))
}
