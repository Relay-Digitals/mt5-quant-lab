package com.anonymouse.trade.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.anonymouse.trade.AppState
import com.anonymouse.trade.ToastData
import com.anonymouse.trade.data.DB
import com.anonymouse.trade.theme.Dimens
import com.anonymouse.trade.theme.theme
import com.anonymouse.trade.ui.*

@Composable
fun StudioScreen(st: AppState) {
    val pal = theme
    val earnings = remember { DB.series(2100.0, 60, 0.06, 0.02, 41) }
    data class S(val l: String, val v: String, val d: String, val icon: String, val col: androidx.compose.ui.graphics.Color)
    val stats = listOf(
        S("Subscribers", "1,842", "+64 this week", "user", pal.accent),
        S("Revenue 30d", "$5,210", "≈ 5,210 USDT", "wallet", pal.up),
        S("Win rate", "71%", "92d tracked", "trending", pal.violet),
        S("Avg rating", "4.9", "318 reviews", "star", pal.warn),
    )

    Box(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize()) {
            TopBar("Provider Studio", "Publish signals · get paid in crypto", big = true)
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp)) {
                // verified banner
                MCard(modifier = Modifier.background(
                    Brush.linearGradient(listOf(pal.accent.copy(alpha = 0.10f), pal.violet.copy(alpha = 0.09f))),
                    RoundedCornerShape(Dimens.radius))) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(13.dp)) {
                        Avatar("AW", 46.dp)
                        Column(Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                Head("@anonwhale", 15); Icon("checkCircle", 14.dp, pal.accent)
                            }
                            TextUi("Listed in marketplace · \$29/mo", 11, color = pal.textMute)
                        }
                        Badge("Verified", Tone.accent)
                    }
                }
                Spacer(Modifier.height(Dimens.gap))
                // stats 2x2
                stats.chunked(2).forEach { row ->
                    Row(Modifier.fillMaxWidth().padding(bottom = 12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        row.forEach { s ->
                            Box(Modifier.weight(1f)) {
                                MCard(pad = 14.dp) {
                                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(11.dp)) {
                                        Box(Modifier.size(38.dp).clip(RoundedCornerShape(11.dp)).background(s.col.copy(alpha = 0.15f)),
                                            contentAlignment = Alignment.Center) { Icon(s.icon, 18.dp, s.col) }
                                        Column { Mono(s.v, 17, FontWeight.Bold); TextUi(s.l, 11, color = pal.textMute) }
                                    }
                                }
                            }
                        }
                    }
                }
                // earnings
                MCard {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                        Column {
                            TextUi("Subscription earnings", 12, FontWeight.SemiBold, pal.textMute)
                            Row(verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                Mono("$5,210", 22, FontWeight.Bold); Mono("+18%", 13, FontWeight.Bold, pal.up)
                            }
                        }
                        Badge("Paid in USDT", Tone.up)
                    }
                    Spacer(Modifier.height(10.dp))
                    AreaChart(earnings, 140.dp)
                }
                Spacer(Modifier.height(Dimens.gap))
                // payout
                MCard {
                    Head("Payout", 15); Spacer(Modifier.height(12.dp))
                    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(13.dp)).background(pal.surface2).padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally) {
                        TextUi("Available balance", 12, color = pal.textMute)
                        Mono("1,284.50", 30, FontWeight.Bold, pal.accent)
                        Mono("USDT · TRC20", 11, FontWeight.Normal, pal.textMute)
                    }
                    Spacer(Modifier.height(13.dp))
                    listOf("Pending (escrow)" to "$420.00", "Next auto-payout" to "in 3 days", "Platform fee" to "15%").forEach { (l, v) ->
                        Row(Modifier.fillMaxWidth().padding(vertical = 3.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                            TextUi(l, 13, color = pal.textMute); Mono(v, 13, FontWeight.SemiBold)
                        }
                    }
                    Spacer(Modifier.height(13.dp))
                    Btn("Withdraw to wallet", BtnVariant.primary, full = true, icon = "wallet") {
                        st.push(ToastData("Withdrawal requested", "1,284.50 USDT → TRC20 wallet · ~1 min", "wallet"))
                    }
                }
                Spacer(Modifier.height(Dimens.gap))
                Head("My signals", 16, modifier = Modifier.padding(horizontal = 4.dp))
                Spacer(Modifier.height(8.dp))
                Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    DB.signals.take(3).forEach { s ->
                        MCard(pad = 13.dp) {
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                Column(Modifier.weight(1f)) {
                                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                        Mono(s.pair, 14, FontWeight.Bold); DirTag(s.dir)
                                        Badge(s.status, if (s.status == "active") Tone.accent else Tone.neutral)
                                    }
                                    Mono("entry ${s.entry}", 11, FontWeight.Normal, pal.textMute)
                                }
                                Mono((if (s.roi >= 0) "+" else "") + "${s.roi}%", 15, FontWeight.Bold, if (s.roi >= 0) pal.up else pal.down)
                            }
                        }
                    }
                }
                Spacer(Modifier.height(28.dp))
            }
        }
        Box(Modifier.align(Alignment.BottomEnd).padding(18.dp)) {
            FAB("plus") { st.push(ToastData("Publish a signal", "Form publish sinyal — coming next phase", "send")) }
        }
    }
}
