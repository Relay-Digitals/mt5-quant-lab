package com.relay.pantauidx.theme

import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import com.relay.pantauidx.resources.Res
import com.relay.pantauidx.resources.ibm_plex_mono_medium
import com.relay.pantauidx.resources.ibm_plex_mono_regular
import com.relay.pantauidx.resources.ibm_plex_mono_semibold
import com.relay.pantauidx.resources.ibm_plex_sans_bold
import com.relay.pantauidx.resources.ibm_plex_sans_medium
import com.relay.pantauidx.resources.ibm_plex_sans_regular
import com.relay.pantauidx.resources.ibm_plex_sans_semibold
import org.jetbrains.compose.resources.Font

/** IBM Plex Sans family from the bundled TTFs (composeResources/font). */
@Composable
fun plexSansFamily(): FontFamily = FontFamily(
    Font(Res.font.ibm_plex_sans_regular, FontWeight.Normal, FontStyle.Normal),
    Font(Res.font.ibm_plex_sans_medium, FontWeight.Medium, FontStyle.Normal),
    Font(Res.font.ibm_plex_sans_semibold, FontWeight.SemiBold, FontStyle.Normal),
    Font(Res.font.ibm_plex_sans_bold, FontWeight.Bold, FontStyle.Normal),
)

/** IBM Plex Mono family (numbers, tickers, prices). */
@Composable
fun plexMonoFamily(): FontFamily = FontFamily(
    Font(Res.font.ibm_plex_mono_regular, FontWeight.Normal, FontStyle.Normal),
    Font(Res.font.ibm_plex_mono_medium, FontWeight.Medium, FontStyle.Normal),
    Font(Res.font.ibm_plex_mono_semibold, FontWeight.SemiBold, FontStyle.Normal),
)
