package com.anonymouse.trade.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.anonymouse.trade.AppState
import com.anonymouse.trade.data.BridgeApi
import com.anonymouse.trade.data.BridgeConfig
import com.anonymouse.trade.data.Settings
import com.anonymouse.trade.theme.Dimens
import com.anonymouse.trade.theme.fonts
import com.anonymouse.trade.theme.theme
import com.anonymouse.trade.ui.*
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(st: AppState) {
    val pal = theme
    val scope = rememberCoroutineScope()
    var url by remember { mutableStateOf(BridgeConfig.baseUrl) }
    var token by remember { mutableStateOf(BridgeConfig.token) }
    var testMsg by remember { mutableStateOf("") }
    var testing by remember { mutableStateOf(false) }

    fun test() {
        scope.launch {
            testing = true; testMsg = "menguji…"
            testMsg = runCatching { BridgeApi(url.trim(), token.trim()).health() }
                .map { "✅ OK · $it" }.getOrElse { "❌ gagal: ${it.message?.take(80)}" }
            testing = false
        }
    }

    Box(Modifier.fillMaxSize().background(pal.bg)) {
        Column(Modifier.fillMaxSize()) {
            Spacer(Modifier.windowInsetsTopHeight(WindowInsets.statusBars))
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Box(Modifier.size(38.dp).clip(RoundedCornerShape(11.dp)).background(pal.surface2)
                    .clickable { st.showSettings = false }, contentAlignment = Alignment.Center) { Icon("x", 18.dp, pal.text) }
                Head("Settings", 18, modifier = Modifier.weight(1f))
            }
            Column(Modifier.padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(Dimens.gap)) {
                MCard {
                    Head("Bridge (Claude Code)", 15)
                    Spacer(Modifier.height(12.dp))
                    Field("Server URL", url, { url = it }, "http://192.168.0.220:8090 / host Tailscale", pal)
                    Spacer(Modifier.height(12.dp))
                    Field("Device token", token, { token = it }, "DEVICE_TOKENS di .env", pal, mono = true)
                    Spacer(Modifier.height(14.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Btn(if (testing) "…" else "Test koneksi", BtnVariant.soft, icon = "link", enabled = !testing) { test() }
                        Btn("Simpan", BtnVariant.primary, icon = "check") {
                            Settings.saveBridge(url, token)
                            st.push(com.anonymouse.trade.ToastData("Tersimpan", "Konfigurasi bridge disimpan.", "check"))
                            st.showSettings = false
                        }
                    }
                    if (testMsg.isNotEmpty()) { Spacer(Modifier.height(10.dp)); Mono(testMsg, 12, FontWeight.Normal, pal.textDim) }
                }
                MCard {
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
                        Column { Head("Tampilan", 15); TextUi("Mode gelap", 12, color = pal.textMute) }
                        MToggle(st.dark) { st.dark = !st.dark; Settings.saveDark(st.dark) }
                    }
                }
                TextUi("Akses dari luar rumah: aktifkan Tailscale di HP, server tetap http://192.168.0.220:8090 (lewat subnet-route).", 11, color = pal.textMute)
            }
        }
    }
}

@Composable
private fun Field(label: String, value: String, onChange: (String) -> Unit, hint: String, pal: com.anonymouse.trade.theme.Palette, mono: Boolean = false) {
    TextUi(label, 12, FontWeight.SemiBold, pal.textDim)
    Spacer(Modifier.height(6.dp))
    Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(Dimens.radiusSm)).background(pal.surface2)
        .border(1.dp, pal.border, RoundedCornerShape(Dimens.radiusSm)).padding(horizontal = 13.dp, vertical = 12.dp)) {
        if (value.isEmpty()) TextUi(hint, 13, color = pal.textMute)
        BasicTextField(value, onChange,
            textStyle = TextStyle(color = pal.text, fontSize = 14.sp, fontFamily = if (mono) fonts.mono else fonts.ui),
            cursorBrush = SolidColor(pal.accent), modifier = Modifier.fillMaxWidth())
    }
}
