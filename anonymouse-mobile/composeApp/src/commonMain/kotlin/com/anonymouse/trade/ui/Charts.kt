package com.anonymouse.trade.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.anonymouse.trade.theme.theme
import kotlin.math.max
import kotlin.math.min

/** Area chart dengan gradient fill + garis — meniru AreaChart prototype. */
@Composable
fun AreaChart(data: List<Float>, height: Dp = 150.dp, color: Color? = null) {
    val pal = theme
    val line = color ?: pal.accent
    Canvas(Modifier.fillMaxWidth().height(height)) {
        if (data.size < 2) return@Canvas
        val w = size.width; val h = size.height
        val lo = data.min(); val hi = data.max(); val span = (hi - lo).takeIf { it > 0 } ?: 1f
        val pad = h * 0.08f
        fun x(i: Int) = w * i / (data.size - 1)
        fun y(v: Float) = h - pad - (v - lo) / span * (h - pad * 2)
        val linePath = Path().apply {
            moveTo(0f, y(data[0]))
            for (i in 1 until data.size) lineTo(x(i), y(data[i]))
        }
        val fillPath = Path().apply {
            addPath(linePath); lineTo(w, h); lineTo(0f, h); close()
        }
        drawPath(fillPath, Brush.verticalGradient(listOf(line.copy(alpha = 0.28f), line.copy(alpha = 0f))))
        drawPath(linePath, line, style = Stroke(width = 2.4f.dp.toPx(), cap = StrokeCap.Round))
        // titik akhir
        drawCircle(line, 3.2f.dp.toPx(), Offset(w, y(data.last())))
        drawCircle(line.copy(alpha = 0.25f), 6f.dp.toPx(), Offset(w, y(data.last())))
    }
}

/** Sparkline kecil untuk baris sinyal. */
@Composable
fun Spark(data: List<Float>, up: Boolean, width: Dp = 52.dp, height: Dp = 26.dp) {
    val pal = theme
    val c = if (up) pal.up else pal.down
    Canvas(Modifier.width(width).height(height)) {
        if (data.size < 2) return@Canvas
        val lo = data.min(); val hi = data.max(); val span = (hi - lo).takeIf { it > 0 } ?: 1f
        val path = Path()
        data.forEachIndexed { i, v ->
            val px = size.width * i / (data.size - 1)
            val py = size.height - (v - lo) / span * size.height
            if (i == 0) path.moveTo(px, py) else path.lineTo(px, py)
        }
        drawPath(path, c, style = Stroke(width = 1.8f.dp.toPx(), cap = StrokeCap.Round))
    }
}

data class DonutSeg(val name: String, val pct: Float, val color: Color)

/** Donut allocation. */
@Composable
fun Donut(segments: List<DonutSeg>, size: Dp = 104.dp, stroke: Dp = 13.dp) {
    val pal = theme
    Canvas(Modifier.size(size)) {
        val sw = stroke.toPx()
        val inset = sw / 2
        val rect = androidx.compose.ui.geometry.Rect(inset, inset, this.size.width - inset, this.size.height - inset)
        // track
        drawArc(pal.surface3, 0f, 360f, false, topLeft = Offset(rect.left, rect.top),
            size = Size(rect.width, rect.height), style = Stroke(sw))
        var start = -90f
        val total = segments.sumOf { it.pct.toDouble() }.toFloat().takeIf { it > 0 } ?: 1f
        segments.forEach { seg ->
            val sweep = seg.pct / total * 360f
            drawArc(seg.color, start + 1.5f, sweep - 3f, false, topLeft = Offset(rect.left, rect.top),
                size = Size(rect.width, rect.height), style = Stroke(sw, cap = StrokeCap.Round))
            start += sweep
        }
    }
}

/** Candle chart sederhana (untuk FullChart). */
@Composable
fun CandleChart(data: List<Candle>, height: Dp = 200.dp) {
    val pal = theme
    Canvas(Modifier.fillMaxWidth().height(height)) {
        if (data.isEmpty()) return@Canvas
        val w = size.width; val h = size.height
        val lo = data.minOf { it.low }; val hi = data.maxOf { it.high }
        val span = (hi - lo).takeIf { it > 0 } ?: 1f
        val cw = w / data.size
        fun y(v: Float) = h - (v - lo) / span * h * 0.94f - h * 0.03f
        data.forEachIndexed { i, c ->
            val cx = cw * i + cw / 2
            val col = if (c.close >= c.open) pal.up else pal.down
            drawLine(col, Offset(cx, y(c.high)), Offset(cx, y(c.low)), 1.2f.dp.toPx())
            val top = min(y(c.open), y(c.close)); val bot = max(y(c.open), y(c.close))
            drawRect(col, Offset(cx - cw * 0.3f, top), Size(cw * 0.6f, (bot - top).coerceAtLeast(1f)))
        }
    }
}

data class Candle(val open: Float, val high: Float, val low: Float, val close: Float)
