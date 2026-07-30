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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.relay.pantauidx.AppState
import com.relay.pantauidx.data.Fmt
import com.relay.pantauidx.data.SampleData
import com.relay.pantauidx.data.ScreenPreset
import com.relay.pantauidx.theme.LocalPlexMono
import com.relay.pantauidx.theme.Pantau
import com.relay.pantauidx.ui.AreaChart
import com.relay.pantauidx.ui.StatCell
import com.relay.pantauidx.ui.SymbolBadge
import com.relay.pantauidx.ui.clickableNoRipple

@Composable
fun MarketScreen(state: AppState) {
    LazyColumn(Modifier.fillMaxWidth()) {
        item { SearchBar() }
        item { IndexBlock() }
        item {
            SectionHeader("Screens · Stockbit Screener")
        }
        items(state.screens) { preset -> ScreenPresetCard(preset) }
        item { SectionHeader("Trending") }
        items(state.trending) { row -> StockRowItem(row) { state.openDetail(row) } }
        item {
            Text(
                if (state.isLive) "SOURCE: exodus.stockbit.com/screener" else "SIMULATED · screener/preset offline",
                color = Pantau.TextFaint, fontFamily = LocalPlexMono.current, fontSize = 11.sp, modifier = Modifier.padding(20.dp),
            )
        }
    }
}

@Composable
private fun SearchBar() {
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SymbolBadge("DK", 36)
        Row(
            Modifier.weight(1f).height(40.dp).clip(RoundedCornerShape(999.dp)).background(Pantau.Card)
                .border(1.dp, Pantau.Line, RoundedCornerShape(999.dp)).padding(horizontal = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("⌕", color = Pantau.TextDim, fontSize = 14.sp)
            Text("Search symbol or screen", color = Pantau.TextDim, fontSize = 13.sp)
        }
    }
}

@Composable
private fun IndexBlock() {
    Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Box(Modifier.clip(RoundedCornerShape(4.dp)).background(Pantau.Text).padding(horizontal = 7.dp, vertical = 3.dp)) {
                Text("IHSG", color = Pantau.Surface, fontFamily = LocalPlexMono.current, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
            }
            Text(Fmt.thousands(SampleData.IHSG_PRICE, 2), color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 19.sp, fontWeight = FontWeight.SemiBold)
            Text(Fmt.signedPct(SampleData.IHSG_PCT), color = Pantau.Green, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
        }
        AreaChart(
            SampleData.candles("BBCA").map { it.close },
            Pantau.Green,
            Modifier.fillMaxWidth().height(150.dp).padding(top = 12.dp),
        )
        Row(Modifier.fillMaxWidth().padding(top = 14.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            InfoCard("Intraday", listOf("Open" to "7,386.20", "High" to "7,441.05", "Low" to "7,362.44"), Modifier.weight(1f))
            InfoCard("Regular", listOf("Lot" to "18.4 M", "Value" to "11.2 T", "Freq" to "1.31 M"), Modifier.weight(1f))
        }
    }
}

@Composable
private fun InfoCard(title: String, rows: List<Pair<String, String>>, modifier: Modifier) {
    Column(
        modifier.clip(RoundedCornerShape(14.dp)).background(Pantau.Card).border(1.dp, Pantau.Line, RoundedCornerShape(14.dp))
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(title.uppercase(), color = Pantau.TextDim, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
        rows.forEach { (k, v) ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(k, color = Pantau.TextDim, fontSize = 12.sp)
                Text(v, color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
            }
        }
    }
}

@Composable
fun SectionHeader(text: String) {
    Text(
        text, color = Pantau.Text, fontSize = 14.sp, fontWeight = FontWeight.Bold,
        modifier = Modifier.fillMaxWidth().background(Pantau.SurfaceAlt).padding(horizontal = 20.dp, vertical = 14.dp),
    )
}

@Composable
private fun ScreenPresetCard(preset: ScreenPreset) {
    Row(
        Modifier.fillMaxWidth().clickableNoRipple { }.padding(horizontal = 20.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(
            Modifier.width(46.dp).height(46.dp).clip(RoundedCornerShape(12.dp))
                .background(Pantau.tintFor(preset.id).first),
            contentAlignment = Alignment.Center,
        ) { Text("⧉", color = Pantau.tintFor(preset.id).second, fontSize = 18.sp) }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(preset.title, color = Pantau.Text, fontSize = 14.sp, fontWeight = FontWeight.Bold)
            Text(preset.description, color = Pantau.TextDim, fontSize = 11.sp, maxLines = 1)
        }
        StatCell("hasil", "${preset.count}", Pantau.Amber, Alignment.End)
    }
    Box(Modifier.fillMaxWidth().height(1.dp).background(Pantau.LineSoft))
}
