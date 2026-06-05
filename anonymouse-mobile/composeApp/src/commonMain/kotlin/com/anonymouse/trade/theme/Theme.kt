package com.anonymouse.trade.theme

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.jetbrains.compose.resources.Font
import com.anonymouse.trade.resources.Res
import com.anonymouse.trade.resources.manrope_regular
import com.anonymouse.trade.resources.manrope_semibold
import com.anonymouse.trade.resources.manrope_bold
import com.anonymouse.trade.resources.manrope_extrabold
import com.anonymouse.trade.resources.space_grotesk_medium
import com.anonymouse.trade.resources.space_grotesk_bold
import com.anonymouse.trade.resources.jetbrains_mono_regular
import com.anonymouse.trade.resources.jetbrains_mono_bold

/**
 * Design tokens dipetakan 1:1 dari :root CSS vars di "Anonymouse Mobile.html".
 * Dark = default; Light = [data-theme="light"]. Accent bisa di-override (tweaks panel).
 */
@Immutable
data class Palette(
    val bg: Color,
    val surface: Color,
    val surface2: Color,
    val surface3: Color,
    val border: Color,
    val borderSoft: Color,
    val text: Color,
    val textDim: Color,
    val textMute: Color,
    val accent: Color,
    val accentInk: Color,
    val accentGlow: Color,
    val violet: Color,
    val up: Color,
    val down: Color,
    val warn: Color,
    val isLight: Boolean,
)

val DarkPalette = Palette(
    bg = Color(0xFF07090D),
    surface = Color(0xFF0D1117),
    surface2 = Color(0xFF141A22),
    surface3 = Color(0xFF1A212B),
    border = Color(0xFF1E2730),
    borderSoft = Color(0xFF19212A),
    text = Color(0xFFE9EDF3),
    textDim = Color(0xFF97A3B4),
    textMute = Color(0xFF5F6B7A),
    accent = Color(0xFF00E5A0),
    accentInk = Color(0xFF04130D),
    accentGlow = Color(0x4000E5A0),
    violet = Color(0xFF7A5AE0),
    up = Color(0xFF16C784),
    down = Color(0xFFF6465D),
    warn = Color(0xFFF7931A),
    isLight = false,
)

val LightPalette = Palette(
    bg = Color(0xFFEEF1F6),
    surface = Color(0xFFFFFFFF),
    surface2 = Color(0xFFF5F7FB),
    surface3 = Color(0xFFEAEFF6),
    border = Color(0xFFE2E8F1),
    borderSoft = Color(0xFFEDF1F7),
    text = Color(0xFF0C121B),
    textDim = Color(0xFF51607A),
    textMute = Color(0xFF8593A8),
    accent = Color(0xFF06B981),
    accentInk = Color(0xFFFFFFFF),
    accentGlow = Color(0x3806B981),
    violet = Color(0xFF7A5AE0),
    up = Color(0xFF16C784),
    down = Color(0xFFF6465D),
    warn = Color(0xFFF7931A),
    isLight = true,
)

/** Accent presets (m-app.jsx M_ACCENTS). */
val AccentPresets = listOf(
    Color(0xFF00E5A0) to Color(0x4000E5A0),
    Color(0xFF2A9FFF) to Color(0x402A9FFF),
    Color(0xFF7A5AE0) to Color(0x477A5AE0),
    Color(0xFFF7931A) to Color(0x42F7931A),
)

object Dimens {
    val radius = 16.dp
    val radiusSm = 11.dp
    val radiusLg = 24.dp
    val gap = 16.dp
    val screenPad = 16.dp
    val deviceMaxWidth = 430.dp
}

/** Font: Manrope (UI), Space Grotesk (heading), JetBrains Mono (angka) — dari composeResources/font. */
data class AppFonts(val ui: FontFamily, val head: FontFamily, val mono: FontFamily)

val LocalFonts = staticCompositionLocalOf {
    AppFonts(FontFamily.Default, FontFamily.Default, FontFamily.Monospace)
}

@Composable
fun appFonts(): AppFonts = AppFonts(
    ui = FontFamily(
        Font(Res.font.manrope_regular, FontWeight.Normal),
        Font(Res.font.manrope_semibold, FontWeight.SemiBold),
        Font(Res.font.manrope_bold, FontWeight.Bold),
        Font(Res.font.manrope_extrabold, FontWeight.ExtraBold),
    ),
    head = FontFamily(
        Font(Res.font.space_grotesk_medium, FontWeight.Medium),
        Font(Res.font.space_grotesk_bold, FontWeight.Bold),
    ),
    mono = FontFamily(
        Font(Res.font.jetbrains_mono_regular, FontWeight.Normal),
        Font(Res.font.jetbrains_mono_bold, FontWeight.Bold),
    ),
)

val LocalPalette = staticCompositionLocalOf { DarkPalette }

@Composable
fun AnonymouseTheme(palette: Palette, content: @Composable () -> Unit) {
    CompositionLocalProvider(LocalPalette provides palette, LocalFonts provides appFonts(), content = content)
}

/** akses cepat dalam composable. */
val theme: Palette
    @Composable get() = LocalPalette.current
val fonts: AppFonts
    @Composable get() = LocalFonts.current
