package com.relay.pantauidx

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.material3.Text
import com.relay.pantauidx.theme.LocalPlexMono
import com.relay.pantauidx.theme.Pantau
import com.relay.pantauidx.theme.PantauTheme
import com.relay.pantauidx.ui.Dot
import com.relay.pantauidx.ui.clickableNoRipple
import com.relay.pantauidx.ui.screens.AuthScreen
import com.relay.pantauidx.ui.screens.DetailScreen
import com.relay.pantauidx.ui.screens.InsiderScreen
import com.relay.pantauidx.ui.screens.MarketScreen
import com.relay.pantauidx.ui.screens.PortfolioScreen
import com.relay.pantauidx.ui.screens.SplashScreen
import com.relay.pantauidx.ui.screens.WatchlistScreen

@Composable
fun App() {
    PantauTheme {
        val scope = rememberCoroutineScope()
        val state = remember { AppState(scope).also { it.start() } }

        Box(
            Modifier.fillMaxSize().background(Pantau.Bg),
            contentAlignment = Alignment.Center,
        ) {
            // Phone-framed canvas (keeps the 390-wide design centered on tablets/desktop).
            Column(
                Modifier
                    .fillMaxSize()
                    .background(Pantau.Surface)
                    .windowInsetsPadding(WindowInsets.safeDrawing),
            ) {
                when (state.root) {
                    Root.SPLASH -> SplashScreen(onContinue = state::skipSplash)
                    Root.AUTH -> AuthScreen(state)
                    Root.DETAIL -> {
                        StatusBar(state.isLive)
                        DetailScreen(state)
                    }
                    Root.MAIN -> {
                        StatusBar(state.isLive)
                        Box(Modifier.weight(1f)) {
                            when (state.tab) {
                                Tab.WATCHLIST -> WatchlistScreen(state)
                                Tab.MARKET -> MarketScreen(state)
                                Tab.INSIDER -> InsiderScreen(state)
                                Tab.PORTFOLIO -> PortfolioScreen(state)
                            }
                        }
                        BottomNav(state)
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusBar(live: Boolean) {
    Row(
        Modifier.fillMaxWidth().height(44.dp).background(Pantau.Surface).padding(horizontal = 20.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text("09:14", color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Dot(if (live) Pantau.Green else Pantau.Amber)
            Text(if (live) "LIVE · IDX" else "SIM · IDX", color = Pantau.TextDim, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
            Text("76%", color = Pantau.Text, fontFamily = LocalPlexMono.current, fontSize = 12.sp)
        }
    }
}

private data class NavItem(val tab: Tab, val glyph: String, val label: String)

@Composable
private fun BottomNav(state: AppState) {
    val items = listOf(
        NavItem(Tab.WATCHLIST, "★", "Watchlist"),
        NavItem(Tab.MARKET, "⌕", "Market"),
        NavItem(Tab.INSIDER, "⇄", "Insider"),
        NavItem(Tab.PORTFOLIO, "▦", "Portfolio"),
    )
    Row(
        Modifier.fillMaxWidth().background(Pantau.Surface).height(64.dp).padding(horizontal = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        items.forEach { item ->
            val active = state.tab == item.tab
            Column(
                Modifier.weight(1f).clickableNoRipple { state.select(item.tab) },
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                Text(item.glyph, color = if (active) Pantau.Green else Pantau.TextDim, fontSize = 18.sp)
                Text(
                    item.label,
                    color = if (active) Pantau.Text else Pantau.TextDim,
                    fontSize = 10.sp,
                    fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal,
                )
            }
        }
    }
}
