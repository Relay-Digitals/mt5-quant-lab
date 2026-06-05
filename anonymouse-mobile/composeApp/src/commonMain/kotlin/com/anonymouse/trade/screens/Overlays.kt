package com.anonymouse.trade.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.anonymouse.trade.ToastData
import com.anonymouse.trade.theme.theme
import com.anonymouse.trade.ui.Icon
import com.anonymouse.trade.ui.Mono
import com.anonymouse.trade.ui.TextUi
import kotlinx.coroutines.delay

@Composable
fun ToastHost(notif: ToastData, onClose: () -> Unit) {
    val pal = theme
    LaunchedEffect(notif) { delay(4200); onClose() }
    Box(Modifier.fillMaxWidth().padding(12.dp)) {
        Row(
            Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp))
                .background(pal.surface.copy(alpha = 0.92f)).clickable { onClose() }.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically
        ) {
            Box(Modifier.size(38.dp).clip(RoundedCornerShape(10.dp))
                .background(Brush.linearGradient(listOf(pal.accent, pal.violet))), contentAlignment = Alignment.Center) {
                Icon(notif.icon, 20.dp, Color(0xFF06120D), 2.2f)
            }
            Column(Modifier.weight(1f)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    TextUi(notif.app, 13, FontWeight.Bold)
                    Mono("now", 10, FontWeight.Normal, pal.textMute)
                }
                TextUi(notif.title, 13, FontWeight.SemiBold)
                if (notif.body.isNotEmpty()) TextUi(notif.body, 12, color = pal.textDim)
            }
        }
    }
}
