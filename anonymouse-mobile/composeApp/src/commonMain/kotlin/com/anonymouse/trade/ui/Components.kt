package com.anonymouse.trade.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.anonymouse.trade.theme.Dimens
import com.anonymouse.trade.theme.fonts
import com.anonymouse.trade.theme.theme

// ---- bottom nav tab def (m-ui M_TABS) ----
data class MTab(val id: String, val label: String, val icon: String)
val M_TABS = listOf(
    MTab("home", "Home", "dashboard"),
    MTab("signals", "Signals", "signals"),
    MTab("backtest", "Backtest", "backtest"),
    MTab("forward", "Forward", "forward"),
    MTab("studio", "Studio", "chart"),
)

@Composable
fun TextUi(text: String, size: Int = 14, weight: FontWeight = FontWeight.Normal,
           color: Color? = null, family: FontFamily? = null, letterSpacing: Double = 0.0,
           modifier: Modifier = Modifier) {
    Text(text, modifier = modifier, color = color ?: theme.text, fontSize = size.sp,
        fontWeight = weight, fontFamily = family ?: fonts.ui, letterSpacing = letterSpacing.sp, lineHeight = (size * 1.3).sp)
}

@Composable
fun Mono(text: String, size: Int = 13, weight: FontWeight = FontWeight.Bold, color: Color? = null, modifier: Modifier = Modifier) =
    TextUi(text, size, weight, color, fonts.mono, modifier = modifier)

@Composable
fun Head(text: String, size: Int = 17, weight: FontWeight = FontWeight.Bold, color: Color? = null, modifier: Modifier = Modifier) =
    TextUi(text, size, weight, color, fonts.head, -0.02, modifier)

// ---- card ----
@Composable
fun MCard(modifier: Modifier = Modifier, pad: Dp = 16.dp, glow: Boolean = false,
          onClick: (() -> Unit)? = null, content: @Composable ColumnScope.() -> Unit) {
    val pal = theme
    var m = modifier
        .clip(RoundedCornerShape(Dimens.radius))
        .background(pal.surface)
        .border(1.dp, if (glow) pal.accentGlow else pal.border, RoundedCornerShape(Dimens.radius))
    if (onClick != null) m = m.clickable { onClick() }
    Column(m.padding(pad), content = content)
}

@Composable
fun MStat(label: String, value: String, delta: String? = null, deltaDown: Boolean = false,
          icon: String? = null, iconColor: Color? = null) {
    val pal = theme
    MCard(pad = 14.dp) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(7.dp)) {
            if (icon != null) Icon(icon, 13.dp, iconColor ?: pal.textMute)
            TextUi(label, 11, FontWeight.SemiBold, pal.textMute)
        }
        Spacer(Modifier.height(7.dp))
        Mono(value, 21, FontWeight.Bold)
        if (delta != null) {
            Spacer(Modifier.height(3.dp))
            Mono((if (deltaDown) "▼ " else "▲ ") + delta, 11, FontWeight.SemiBold, if (deltaDown) pal.down else pal.up)
        }
    }
}

// ---- badge ----
enum class Tone { up, down, accent, violet, neutral, warn }

@Composable
fun Badge(text: String, tone: Tone = Tone.neutral, mono: Boolean = false, leading: @Composable (() -> Unit)? = null) {
    val pal = theme
    val c = when (tone) {
        Tone.up -> pal.up; Tone.down -> pal.down; Tone.accent -> pal.accent
        Tone.violet -> pal.violet; Tone.warn -> pal.warn; Tone.neutral -> pal.textDim
    }
    Row(
        Modifier.clip(RoundedCornerShape(99.dp)).background(c.copy(alpha = 0.15f))
            .padding(horizontal = 9.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        leading?.invoke()
        TextUi(text, 11, FontWeight.Bold, c, if (mono) fonts.mono else fonts.ui)
    }
}

@Composable
fun DirTag(dir: String) {
    val pal = theme
    val long = dir.equals("LONG", true)
    Badge(dir.uppercase(), if (long) Tone.up else Tone.down, mono = true)
}

// ---- chips ----
@Composable
fun Chip(text: String, active: Boolean, tone: Color? = null, onClick: () -> Unit) {
    val pal = theme
    val t = tone ?: pal.accent
    Row(
        Modifier.clip(RoundedCornerShape(99.dp))
            .background(if (active) t.copy(alpha = 0.16f) else pal.surface2)
            .border(1.dp, if (active) t else pal.border, RoundedCornerShape(99.dp))
            .clickable { onClick() }.padding(horizontal = 14.dp, vertical = 8.dp)
    ) { TextUi(text, 13, FontWeight.SemiBold, if (active) t else pal.textDim) }
}

@Composable
fun ChipRow(content: @Composable RowScope.() -> Unit) {
    Row(
        Modifier.fillMaxWidth().horizontalScroll(androidx.compose.foundation.rememberScrollState())
            .padding(horizontal = 20.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp), content = content
    )
}

// ---- toggle ----
@Composable
fun MToggle(on: Boolean, onClick: () -> Unit) {
    val pal = theme
    Box(
        Modifier.width(46.dp).height(27.dp).clip(RoundedCornerShape(99.dp))
            .background(if (on) pal.accent else pal.surface3).clickable { onClick() }.padding(3.dp),
        contentAlignment = if (on) Alignment.CenterEnd else Alignment.CenterStart
    ) {
        Box(Modifier.size(21.dp).clip(CircleShape).background(if (on) pal.accentInk else pal.textMute))
    }
}

// ---- slider row ----
@Composable
fun MSlider(label: String, value: Float, min: Float, max: Float, step: Int = 0,
            onChange: (Float) -> Unit, fmt: (Float) -> String) {
    val pal = theme
    Column(Modifier.fillMaxWidth().padding(bottom = 18.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            TextUi(label, 13, FontWeight.SemiBold, pal.textDim)
            Mono(fmt(value), 13, FontWeight.Bold, pal.accent)
        }
        Spacer(Modifier.height(6.dp))
        Slider(
            value = value, onValueChange = onChange, valueRange = min..max,
            steps = if (step > 0) step - 1 else 0,
            colors = SliderDefaults.colors(
                thumbColor = pal.accent, activeTrackColor = pal.accent, inactiveTrackColor = pal.surface3
            )
        )
    }
}

// ---- button ----
enum class BtnVariant { primary, soft, ghost }

@Composable
fun Btn(text: String, variant: BtnVariant = BtnVariant.primary, full: Boolean = false,
        icon: String? = null, enabled: Boolean = true, onClick: () -> Unit) {
    val pal = theme
    val bg = when (variant) {
        BtnVariant.primary -> pal.accent
        BtnVariant.soft -> pal.surface2
        BtnVariant.ghost -> Color.Transparent
    }
    val fg = when (variant) {
        BtnVariant.primary -> pal.accentInk
        else -> pal.text
    }
    var m = Modifier.clip(RoundedCornerShape(Dimens.radiusSm)).background(bg.copy(alpha = if (enabled) 1f else 0.4f))
    if (variant != BtnVariant.primary) m = m.border(1.dp, pal.border, RoundedCornerShape(Dimens.radiusSm))
    if (full) m = m.fillMaxWidth()
    m = m.clickable(enabled = enabled) { onClick() }.padding(horizontal = 16.dp, vertical = 13.dp)
    Row(m, horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally),
        verticalAlignment = Alignment.CenterVertically) {
        if (icon != null) Icon(icon, 18.dp, fg)
        TextUi(text, 14, FontWeight.Bold, fg)
    }
}

// ---- avatar ----
@Composable
fun Avatar(initials: String, size: Dp = 38.dp, gradient: Boolean = true) {
    val pal = theme
    Box(
        Modifier.size(size).clip(RoundedCornerShape(size / 3))
            .background(if (gradient)
                androidx.compose.ui.graphics.Brush.linearGradient(listOf(pal.accent, pal.violet))
            else androidx.compose.ui.graphics.SolidColor(pal.surface3)),
        contentAlignment = Alignment.Center
    ) { Head(initials.take(2), (size.value / 2.4).toInt(), FontWeight.ExtraBold, Color(0xFF06120D)) }
}

// ---- top bar ----
@Composable
fun TopBar(title: String, sub: String? = null, big: Boolean = false,
           onBack: (() -> Unit)? = null, right: @Composable (() -> Unit)? = null) {
    val pal = theme
    Row(
        Modifier.fillMaxWidth().padding(start = 20.dp, end = 20.dp, top = if (big) 4.dp else 6.dp, bottom = 12.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        if (onBack != null) {
            Box(Modifier.size(38.dp).clip(RoundedCornerShape(Dimens.radiusSm)).background(pal.surface2)
                .border(1.dp, pal.border, RoundedCornerShape(Dimens.radiusSm)).clickable { onBack() },
                contentAlignment = Alignment.Center) { Icon("arrowRight", 18.dp, pal.text) }
        }
        Column(Modifier.weight(1f)) {
            Head(title, if (big) 25 else 21, FontWeight.Bold)
            if (sub != null) { Spacer(Modifier.height(4.dp)); TextUi(sub, 13, color = pal.textMute) }
        }
        right?.invoke()
    }
}

// ---- bottom nav ----
@Composable
fun BottomNav(active: String, onNav: (String) -> Unit) {
    val pal = theme
    Column(Modifier.fillMaxWidth().background(pal.surface)) {
    Box(Modifier.fillMaxWidth().height(1.dp).background(pal.border))
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 6.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceEvenly
    ) {
        M_TABS.forEach { tb ->
            val on = active == tb.id
            Column(
                Modifier.weight(1f).clip(RoundedCornerShape(9.dp)).clickable { onNav(tb.id) }.padding(vertical = 4.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Box(Modifier.size(width = 30.dp, height = 26.dp).clip(RoundedCornerShape(9.dp))
                    .background(if (on) pal.accent.copy(alpha = 0.14f) else Color.Transparent),
                    contentAlignment = Alignment.Center) {
                    Icon(tb.icon, 20.dp, if (on) pal.accent else pal.textMute, if (on) 2.2f else 1.9f)
                }
                TextUi(tb.label, 10, if (on) FontWeight.Bold else FontWeight.SemiBold, if (on) pal.accent else pal.textMute)
            }
        }
    }
    }
}

// ---- FAB ----
@Composable
fun FAB(icon: String = "plus", onClick: () -> Unit) {
    val pal = theme
    Box(
        Modifier.size(56.dp).clip(RoundedCornerShape(18.dp)).background(pal.accent).clickable { onClick() },
        contentAlignment = Alignment.Center
    ) { Icon(icon, 26.dp, pal.accentInk, 2.4f) }
}

// ---- live dot ----
@Composable
fun LiveDot(size: Dp = 7.dp, color: Color? = null) {
    val pal = theme
    Box(Modifier.size(size).clip(CircleShape).background(color ?: pal.up))
}
