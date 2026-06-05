package com.anonymouse.trade

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import com.anonymouse.trade.data.Settings
import com.anonymouse.trade.theme.*
import com.anonymouse.trade.ui.*
import com.anonymouse.trade.screens.*

/** state navigasi + tema, dibagikan ke screen lewat [AppState]. */
class AppState {
    var tab by mutableStateOf("home")
    var dark by mutableStateOf(Settings.loadDark(true))
    var accent by mutableStateOf(AccentPresets[0].first)
    var accentGlow by mutableStateOf(AccentPresets[0].second)
    var showChat by mutableStateOf(false)
    var showSettings by mutableStateOf(false)
    var toast by mutableStateOf<ToastData?>(null)

    fun go(t: String) { tab = t }
    fun push(t: ToastData) { toast = t }
}

data class ToastData(val title: String, val body: String, val icon: String = "bell", val app: String = "Anonymouse Trade")

@Composable
fun App() {
    val st = remember { AppState() }
    val base = if (st.dark) DarkPalette else LightPalette
    val palette = base.copy(accent = st.accent, accentGlow = st.accentGlow,
        accentInk = if (st.dark) Color(0xFF04130D) else Color(0xFFFFFFFF))

    AnonymouseTheme(palette) {
        Box(Modifier.fillMaxSize().background(palette.bg)) {
            Column(Modifier.fillMaxSize().widthIn(max = Dimens.deviceMaxWidth).align(androidx.compose.ui.Alignment.TopCenter)) {
                Spacer(Modifier.windowInsetsTopHeight(WindowInsets.statusBars))
                Box(Modifier.weight(1f).fillMaxWidth()) {
                    when (st.tab) {
                        "home" -> HomeScreen(st)
                        "signals" -> SignalsScreen(st)
                        "backtest" -> BacktestScreen(st)
                        "forward" -> ForwardScreen(st)
                        else -> StudioScreen(st)
                    }
                }
                BottomNav(st.tab) { st.go(it) }
                Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
            }

            // overlay: Claude chat
            if (st.showChat) ClaudeChatScreen(st)

            // overlay: settings
            if (st.showSettings) SettingsScreen(st)

            // overlay: push toast
            st.toast?.let { ToastHost(it) { st.toast = null } }
        }
    }
}
