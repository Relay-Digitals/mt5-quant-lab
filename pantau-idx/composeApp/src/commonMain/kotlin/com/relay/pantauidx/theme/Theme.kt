package com.relay.pantauidx.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * StockPick / Pantau IDX palette — lifted verbatim from the design (`Pantau IDX.dc.html`).
 * The app is dark-only by design (radial #16202B → #05070A backgrounds).
 */
object Pantau {
    val Bg = Color(0xFF05070A)          // app root
    val Surface = Color(0xFF0B0E13)     // phone frame / bars
    val SurfaceAlt = Color(0xFF101620)  // hover / section header
    val Card = Color(0xFF141A22)        // cards, inputs
    val Line = Color(0xFF1F2733)        // borders / dividers
    val LineSoft = Color(0xFF141A22)    // row dividers
    val Bar = Color(0xFF2A3646)         // logo bar / muted fill

    val Text = Color(0xFFE6EAF0)        // primary
    val TextMut = Color(0xFFA7B0BF)     // secondary
    val TextDim = Color(0xFF7C8798)     // labels
    val TextFaint = Color(0xFF47505F)   // faint / mono captions

    val Green = Color(0xFF2FD07A)       // up / brand accent
    val GreenSoft = Color(0xFF9BD46A)
    val Amber = Color(0xFFFFB020)       // CTA / highlight
    val AmberHi = Color(0xFFFFC64F)
    val Red = Color(0xFFFF5A6E)         // down
    val Blue = Color(0xFF7FB4FF)
    val Purple = Color(0xFFC79BFF)
    val Cyan = Color(0xFF6FD8E8)

    /** Avatar tints used for symbol chips (bg, text). */
    val Tints = listOf(
        Color(0xFF14261C) to Color(0xFF6FE0A6),
        Color(0xFF1B2A3D) to Color(0xFF7FB4FF),
        Color(0xFF2A1F14) to Color(0xFFFFB878),
        Color(0xFF241A2E) to Color(0xFFC79BFF),
        Color(0xFF2A1414) to Color(0xFFFF8A9A),
        Color(0xFF13242A) to Color(0xFF6FD8E8),
    )

    fun tintFor(seed: String): Pair<Color, Color> {
        var h = 0
        for (c in seed) h = (h * 31 + c.code) and 0x7fffffff
        return Tints[h % Tints.size]
    }

    /** up/down helper. */
    fun trend(up: Boolean): Color = if (up) Green else Red
}

/**
 * IBM Plex families exposed via CompositionLocals — populated by [PantauTheme] from the
 * bundled TTFs, so any composable can read `LocalPlexMono.current` for exact type.
 * Defaults fall back to platform Sans/Mono before the theme provides the real families.
 */
val LocalPlexSans = staticCompositionLocalOf { FontFamily.Default }
val LocalPlexMono = staticCompositionLocalOf { FontFamily.Monospace }

private fun pantauTypography(sans: FontFamily) = Typography(
    titleLarge = TextStyle(fontFamily = sans, fontWeight = FontWeight.Bold, fontSize = 26.sp, letterSpacing = (-0.5).sp),
    titleMedium = TextStyle(fontFamily = sans, fontWeight = FontWeight.Bold, fontSize = 22.sp, letterSpacing = (-0.4).sp),
    bodyLarge = TextStyle(fontFamily = sans, fontWeight = FontWeight.Normal, fontSize = 15.sp),
    bodyMedium = TextStyle(fontFamily = sans, fontWeight = FontWeight.Normal, fontSize = 13.sp),
    labelSmall = TextStyle(fontFamily = sans, fontWeight = FontWeight.SemiBold, fontSize = 11.sp, letterSpacing = 1.2.sp),
)

private val PantauColors = darkColorScheme(
    primary = Pantau.Green,
    onPrimary = Pantau.Surface,
    secondary = Pantau.Amber,
    background = Pantau.Bg,
    onBackground = Pantau.Text,
    surface = Pantau.Surface,
    onSurface = Pantau.Text,
    error = Pantau.Red,
)

@Composable
fun PantauTheme(content: @Composable () -> Unit) {
    // Dark-only regardless of system, matching the design intent.
    val sans = plexSansFamily()
    val mono = plexMonoFamily()
    CompositionLocalProvider(
        LocalPlexSans provides sans,
        LocalPlexMono provides mono,
    ) {
        MaterialTheme(
            colorScheme = PantauColors,
            typography = pantauTypography(sans),
            content = content,
        )
    }
}
