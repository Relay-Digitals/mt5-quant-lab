package com.relay.pantauidx.ui.screens

import androidx.compose.foundation.background
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
import com.relay.pantauidx.data.InsiderTx
import com.relay.pantauidx.theme.LocalPlexMono
import com.relay.pantauidx.theme.Pantau
import com.relay.pantauidx.ui.Pill

private enum class Side { ALL, BUY, SELL }

@Composable
fun InsiderScreen(state: AppState) {
    var side by remember { mutableStateOf(Side.ALL) }
    val list = remember(side, state.insiders.size) {
        when (side) {
            Side.ALL -> state.insiders.toList()
            Side.BUY -> state.insiders.filter { it.isBuy }
            Side.SELL -> state.insiders.filter { !it.isBuy }
        }
    }

    Column(Modifier.fillMaxWidth()) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.Center,
        ) {
            Text("Insider Activity", color = Pantau.Text, fontSize = 15.sp, fontWeight = FontWeight.Bold)
        }
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Pill("All", side == Side.ALL) { side = Side.ALL }
            Pill("Buy", side == Side.BUY) { side = Side.BUY }
            Pill("Sell", side == Side.SELL) { side = Side.SELL }
            Box(Modifier.weight(1f))
            Text("${list.size} tx", color = Pantau.TextFaint, fontFamily = LocalPlexMono.current, fontSize = 11.sp)
        }
        LazyColumn(Modifier.fillMaxWidth()) {
            items(list) { tx -> InsiderCard(tx) }
        }
    }
}

@Composable
private fun InsiderCard(tx: InsiderTx) {
    val c = Pantau.trend(tx.isBuy)
    Column(
        Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(tx.date, color = Pantau.TextDim, fontFamily = LocalPlexMono.current, fontSize = 11.sp)
            Text("${tx.action} ${tx.code}", color = c, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            Box(Modifier.weight(1f))
            Box(Modifier.clip(RoundedCornerShape(5.dp)).background(Pantau.Line).padding(horizontal = 6.dp, vertical = 2.dp)) {
                Text(tx.source, color = Pantau.TextDim, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Bottom) {
            Text(tx.holder, color = c, fontSize = 12.sp, fontWeight = FontWeight.Bold, maxLines = 1, modifier = Modifier.weight(1f))
            Text(
                "${if (tx.isBuy) "▲" else "▼"} ${Fmt.compact(tx.delta)}",
                color = c, fontFamily = LocalPlexMono.current, fontSize = 13.sp, fontWeight = FontWeight.SemiBold,
            )
        }
        kv("Current", Fmt.compact(tx.current), c)
        kv("Previous", Fmt.compact(tx.previous), Pantau.TextMut)
        kv("Price", Fmt.price(tx.price), Pantau.Text)
        if (tx.type.isNotBlank()) kv("Type", tx.type, Pantau.Purple)
    }
    Box(Modifier.fillMaxWidth().height(1.dp).background(Pantau.LineSoft))
}

@Composable
private fun kv(k: String, v: String, color: androidx.compose.ui.graphics.Color) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(k, color = Pantau.TextDim, fontSize = 12.sp)
        Text(v, color = color, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
    }
}
