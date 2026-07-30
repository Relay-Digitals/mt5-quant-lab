package com.relay.pantauidx.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.relay.pantauidx.theme.LocalPlexMono
import com.relay.pantauidx.theme.Pantau
import androidx.compose.foundation.Canvas
import androidx.compose.ui.graphics.Path

/** Symbol avatar chip (initials on a tinted rounded square). */
@Composable
fun SymbolBadge(code: String, size: Int = 40) {
    val (bg, fg) = Pantau.tintFor(code)
    Box(
        Modifier.size(size.dp).clip(RoundedCornerShape((size * 0.3).dp)).background(bg),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            code.take(2),
            color = fg,
            fontFamily = LocalPlexMono.current,
            fontSize = (size * 0.32).sp,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

/** Tiny line sparkline; auto-scales to its min/max. */
@Composable
fun Sparkline(
    points: List<Double>,
    color: Color,
    modifier: Modifier = Modifier,
    strokeWidth: Float = 1.5f,
) {
    if (points.size < 2) return
    Canvas(modifier) {
        val min = points.min()
        val max = points.max()
        val span = (max - min).takeIf { it != 0.0 } ?: 1.0
        val dx = size.width / (points.size - 1)
        val path = Path()
        points.forEachIndexed { i, v ->
            val x = i * dx
            val y = size.height - ((v - min) / span).toFloat() * size.height
            if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
        }
        drawPath(path, color, style = Stroke(width = strokeWidth * density))
    }
}

/** Filled area chart for the index detail (line + gradient). */
@Composable
fun AreaChart(points: List<Double>, color: Color, modifier: Modifier) {
    if (points.size < 2) return
    Canvas(modifier) {
        val min = points.min()
        val max = points.max()
        val span = (max - min).takeIf { it != 0.0 } ?: 1.0
        val dx = size.width / (points.size - 1)
        val line = Path()
        val area = Path()
        points.forEachIndexed { i, v ->
            val x = i * dx
            val y = size.height - ((v - min) / span).toFloat() * size.height
            if (i == 0) { line.moveTo(x, y); area.moveTo(x, size.height); area.lineTo(x, y) }
            else { line.lineTo(x, y); area.lineTo(x, y) }
        }
        area.lineTo(size.width, size.height)
        area.close()
        drawPath(area, color.copy(alpha = 0.20f))
        drawPath(line, color, style = Stroke(width = 1.8f * density))
    }
}

/** Pill chip used across sort/filter rows. */
@Composable
fun Pill(
    text: String,
    active: Boolean,
    onClick: () -> Unit,
) {
    val fg = if (active) Pantau.Surface else Pantau.TextDim
    val bg = if (active) Pantau.Amber else Color.Transparent
    val border = if (active) Pantau.Amber else Pantau.Line
    Box(
        Modifier
            .clip(RoundedCornerShape(999.dp))
            .background(bg)
            .border(1.dp, border, RoundedCornerShape(999.dp))
            .clickableNoRipple(onClick)
            .padding(horizontal = 14.dp, vertical = 8.dp),
    ) {
        Text(text, color = fg, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun Dot(color: Color, size: Int = 6) {
    Box(Modifier.size(size.dp).clip(RoundedCornerShape(999.dp)).background(color))
}

/** Label + mono value stat cell used in cards. */
@Composable
fun StatCell(label: String, value: String, color: Color = Pantau.Text, align: Alignment.Horizontal = Alignment.Start) {
    Column(horizontalAlignment = align) {
        Text(value, color = color, fontFamily = LocalPlexMono.current, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
        Text(label, color = Pantau.TextDim, fontSize = 11.sp)
    }
}
