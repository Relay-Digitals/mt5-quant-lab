package com.relay.pantauidx.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.relay.pantauidx.theme.LocalPlexMono
import com.relay.pantauidx.theme.Pantau
import com.relay.pantauidx.ui.clickableNoRipple

@Composable
fun SplashScreen(onContinue: () -> Unit) {
    Box(
        Modifier.fillMaxSize().background(Pantau.Bg).clickableNoRipple(onContinue),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(26.dp),
        ) {
            // candlestick logo mark
            Row(verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                bar(34, Pantau.Line); bar(58, Pantau.Bar); bar(44, Pantau.Line)
                bar(82, Pantau.Green); bar(62, Pantau.Bar)
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    buildAnnotatedString {
                        append("Stock")
                        withStyle(SpanStyle(color = Pantau.Green)) { append("Pick") }
                    },
                    color = Pantau.Text, fontSize = 34.sp, fontWeight = FontWeight.Bold,
                )
                Text("MONITORING SAHAM IDX", color = Pantau.TextDim, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
            }
            Text("TAP TO CONTINUE", color = Pantau.TextFaint, fontFamily = LocalPlexMono.current, fontSize = 10.sp)
        }
    }
}

@Composable
private fun bar(h: Int, color: androidx.compose.ui.graphics.Color) {
    Box(Modifier.width(16.dp).height(h.dp).clip(RoundedCornerShape(4.dp)).background(color))
}
