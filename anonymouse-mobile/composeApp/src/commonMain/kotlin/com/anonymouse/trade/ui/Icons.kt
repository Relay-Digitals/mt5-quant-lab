package com.anonymouse.trade.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.anonymouse.trade.theme.theme

/**
 * Icon ringan berbasis Canvas (stroke 24x24-ish). Nama mengikuti m-ui.jsx Icon names.
 * Bentuk sebagian disederhanakan dari SVG asli; cukup untuk fidelity visual nav/aksi.
 */
@Composable
fun Icon(name: String, size: Dp = 20.dp, color: Color = theme.text, strokeWidth: Float = 1.9f) {
    Canvas(Modifier.size(size)) {
        val w = this.size.width
        val s = w / 24f
        val sw = strokeWidth * s
        val stroke = Stroke(width = sw, cap = StrokeCap.Round, join = StrokeJoin.Round)
        fun p(block: Path.() -> Unit) = drawPath(Path().apply(block), color, style = stroke)
        fun line(x1: Float, y1: Float, x2: Float, y2: Float) =
            drawLine(color, Offset(x1 * s, y1 * s), Offset(x2 * s, y2 * s), sw, StrokeCap.Round)
        fun circle(cx: Float, cy: Float, r: Float, fill: Boolean = false) {
            if (fill) drawCircle(color, r * s, Offset(cx * s, cy * s))
            else drawCircle(color, r * s, Offset(cx * s, cy * s), style = stroke)
        }
        when (name) {
            "dashboard" -> { rectS(s, sw, color, 4f, 4f, 7f, 7f); rectS(s, sw, color, 13f, 4f, 7f, 7f); rectS(s, sw, color, 4f, 13f, 7f, 7f); rectS(s, sw, color, 13f, 13f, 7f, 7f) }
            "signals" -> { p { moveTo(3f * s, 14f * s); lineTo(8f * s, 9f * s); lineTo(12f * s, 13f * s); lineTo(21f * s, 4f * s) }; line(21f, 4f, 16f, 4f); line(21f, 4f, 21f, 9f) }
            "backtest" -> { rectS(s, sw, color, 3f, 4f, 18f, 16f, 2f); line(3f, 9f, 21f, 9f); line(8f, 13f, 8f, 17f); line(12f, 12f, 12f, 17f); line(16f, 14f, 16f, 17f) }
            "forward" -> { p { moveTo(5f * s, 4f * s); lineTo(15f * s, 12f * s); lineTo(5f * s, 20f * s); close() }; line(19f, 4f, 19f, 20f) }
            "chart", "trending" -> { p { moveTo(3f * s, 17f * s); lineTo(9f * s, 11f * s); lineTo(13f * s, 15f * s); lineTo(21f * s, 7f * s) } }
            "bell" -> { p { moveTo(6f * s, 16f * s); cubicTo(6f * s, 10f * s, 7f * s, 6f * s, 12f * s, 6f * s); cubicTo(17f * s, 6f * s, 18f * s, 10f * s, 18f * s, 16f * s) }; line(4f, 17f, 20f, 17f); circle(12f, 20f, 1.6f) }
            "wallet" -> { rectS(s, sw, color, 3f, 6f, 18f, 13f, 3f); line(3f, 10f, 21f, 10f); circle(17f, 14f, 1.2f, true) }
            "plus" -> { line(12f, 5f, 12f, 19f); line(5f, 12f, 19f, 12f) }
            "x" -> { line(6f, 6f, 18f, 18f); line(18f, 6f, 6f, 18f) }
            "check" -> { p { moveTo(5f * s, 12.5f * s); lineTo(10f * s, 17f * s); lineTo(19f * s, 6.5f * s) } }
            "checkCircle" -> { circle(12f, 12f, 9f); p { moveTo(8f * s, 12.5f * s); lineTo(11f * s, 15.5f * s); lineTo(16f * s, 8.5f * s) } }
            "arrowRight" -> { line(4f, 12f, 20f, 12f); p { moveTo(14f * s, 6f * s); lineTo(20f * s, 12f * s); lineTo(14f * s, 18f * s) } }
            "arrowUp" -> { line(12f, 20f, 12f, 5f); p { moveTo(6f * s, 11f * s); lineTo(12f * s, 5f * s); lineTo(18f * s, 11f * s) } }
            "arrowDown" -> { line(12f, 4f, 12f, 19f); p { moveTo(6f * s, 13f * s); lineTo(12f * s, 19f * s); lineTo(18f * s, 13f * s) } }
            "refresh" -> { p { moveTo(20f * s, 8f * s); arcTo(androidx.compose.ui.geometry.Rect(4f * s, 4f * s, 20f * s, 20f * s), -60f, -250f, false) }; p { moveTo(20f * s, 4f * s); lineTo(20f * s, 8f * s); lineTo(16f * s, 8f * s) } }
            "send" -> { p { moveTo(21f * s, 4f * s); lineTo(3f * s, 11f * s); lineTo(10f * s, 13f * s); lineTo(12f * s, 20f * s); close() }; line(21f, 4f, 10f, 13f) }
            "download" -> { line(12f, 4f, 12f, 15f); p { moveTo(7f * s, 11f * s); lineTo(12f * s, 16f * s); lineTo(17f * s, 11f * s) }; line(5f, 19f, 19f, 19f) }
            "link" -> { p { moveTo(9f * s, 15f * s); lineTo(15f * s, 9f * s) }; p { moveTo(10f * s, 7f * s); lineTo(13f * s, 4f * s); arcTo(androidx.compose.ui.geometry.Rect(13f * s, 4f * s, 21f * s, 12f * s), 180f, 180f, false); lineTo(17f * s, 14f * s) }; p { moveTo(14f * s, 17f * s); lineTo(11f * s, 20f * s); arcTo(androidx.compose.ui.geometry.Rect(3f * s, 12f * s, 11f * s, 20f * s), 0f, 180f, false); lineTo(7f * s, 10f * s) } }
            "search" -> { circle(11f, 11f, 6f); line(15.5f, 15.5f, 20f, 20f) }
            "user" -> { circle(12f, 8f, 4f); p { moveTo(5f * s, 20f * s); cubicTo(5f * s, 15f * s, 8f * s, 14f * s, 12f * s, 14f * s); cubicTo(16f * s, 14f * s, 19f * s, 15f * s, 19f * s, 20f * s) } }
            "star" -> { p { moveTo(12f * s, 3f * s); lineTo(14.6f * s, 9f * s); lineTo(21f * s, 9.6f * s); lineTo(16f * s, 14f * s); lineTo(17.6f * s, 20.5f * s); lineTo(12f * s, 17f * s); lineTo(6.4f * s, 20.5f * s); lineTo(8f * s, 14f * s); lineTo(3f * s, 9.6f * s); lineTo(9.4f * s, 9f * s); close() } }
            "globe" -> { circle(12f, 12f, 9f); circle(12f, 12f, 4f); line(3f, 12f, 21f, 12f); line(12f, 3f, 12f, 21f) }
            "layers" -> { p { moveTo(12f * s, 3f * s); lineTo(21f * s, 8f * s); lineTo(12f * s, 13f * s); lineTo(3f * s, 8f * s); close() }; p { moveTo(3f * s, 13f * s); lineTo(12f * s, 18f * s); lineTo(21f * s, 13f * s) } }
            "play" -> drawPath(Path().apply { moveTo(7f * s, 5f * s); lineTo(19f * s, 12f * s); lineTo(7f * s, 19f * s); close() }, color)
            "chat" -> { rectS(s, sw, color, 3f, 4f, 18f, 14f, 4f); p { moveTo(8f * s, 18f * s); lineTo(8f * s, 22f * s); lineTo(13f * s, 18f * s) } }
            "settings" -> { circle(12f, 12f, 3f); circle(12f, 12f, 8.5f) }
            else -> circle(12f, 12f, 8f)
        }
    }
}

private fun DrawScope.rectS(s: Float, sw: Float, color: Color, x: Float, y: Float, w: Float, h: Float, r: Float = 1.5f) {
    drawRoundRect(color, Offset(x * s, y * s), Size(w * s, h * s),
        androidx.compose.ui.geometry.CornerRadius(r * s, r * s),
        style = Stroke(width = sw, cap = StrokeCap.Round, join = StrokeJoin.Round))
}
