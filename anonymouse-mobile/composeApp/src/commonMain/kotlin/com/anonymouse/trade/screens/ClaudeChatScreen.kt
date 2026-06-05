package com.anonymouse.trade.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
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
import com.anonymouse.trade.data.BridgeEvent
import com.anonymouse.trade.data.bridgeApi
import com.anonymouse.trade.theme.Dimens
import com.anonymouse.trade.theme.fonts
import com.anonymouse.trade.theme.theme
import com.anonymouse.trade.ui.*
import kotlinx.coroutines.launch

data class ChatMsg(val role: String, var text: String, val kind: String = "text")

@Composable
fun ClaudeChatScreen(st: AppState) {
    val pal = theme
    val scope = rememberCoroutineScope()
    val msgs = remember { mutableStateListOf(
        ChatMsg("assistant", "Halo Ben 👋 Aku Claude Code di CT108. Minta backtest, cek forward-test, atau analisa saham/forex. Contoh: \"backtest regime AUDJPY 1 tahun\".")
    ) }
    var input by remember { mutableStateOf("") }
    var role by remember { mutableStateOf("research") }
    var sessionId by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val listState = rememberLazyListState()
    val api = remember { bridgeApi() }

    fun send() {
        val text = input.trim(); if (text.isEmpty() || busy) return
        input = ""; msgs.add(ChatMsg("user", text)); busy = true
        val assistant = ChatMsg("assistant", ""); msgs.add(assistant)
        scope.launch {
            if (api == null) {
                assistant.text = "⚠️ Bridge belum dikonfigurasi. Set Tailscale host + device token di BridgeConfig (Fase 2). " +
                    "Saat tersambung, pesan ini akan dijalankan oleh Claude Code di CT108."
                msgs[msgs.lastIndex] = assistant.copy(); busy = false; return@launch
            }
            try {
                val start = api.sendChat(text, sessionId, role); sessionId = start.sessionId
                api.streamJob(start.jobId).collect { ev ->
                    when (ev) {
                        is BridgeEvent.TextDelta -> { assistant.text += ev.delta; msgs[msgs.lastIndex] = assistant.copy() }
                        is BridgeEvent.ToolUse -> msgs.add(msgs.lastIndex, ChatMsg("tool", "▸ ${ev.name} ${ev.input}", "tool"))
                        is BridgeEvent.ToolResult -> {}
                        is BridgeEvent.Artifact -> msgs.add(ChatMsg("artifact", "📎 ${ev.name}", "artifact"))
                        is BridgeEvent.Done -> { if (assistant.text.isEmpty()) { assistant.text = ev.result; msgs[msgs.lastIndex] = assistant.copy() } }
                        is BridgeEvent.Err -> { assistant.text = "⚠️ ${ev.msg}"; msgs[msgs.lastIndex] = assistant.copy() }
                        is BridgeEvent.Ready -> {}
                    }
                }
            } catch (e: Throwable) {
                assistant.text = "⚠️ Gagal hubungi bridge: ${e.message?.take(120)}"
                msgs[msgs.lastIndex] = assistant.copy()
            }
            busy = false
        }
    }

    LaunchedEffect(msgs.size) { if (msgs.isNotEmpty()) listState.animateScrollToItem(msgs.size - 1) }

    Box(Modifier.fillMaxSize().background(pal.bg)) {
        Column(Modifier.fillMaxSize()) {
            Spacer(Modifier.windowInsetsTopHeight(WindowInsets.statusBars))
            // header
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Box(Modifier.size(38.dp).clip(RoundedCornerShape(11.dp)).background(pal.surface2)
                    .clickable { st.showChat = false }, contentAlignment = Alignment.Center) { Icon("x", 18.dp, pal.text) }
                Column(Modifier.weight(1f)) {
                    Head("Claude Code", 18)
                    TextUi("CT108 · ${if (api == null) "offline (set token)" else BridgeConfig.baseUrl}", 11, color = pal.textMute)
                }
                if (busy) Box(Modifier.size(18.dp)) { Icon("refresh", 18.dp, pal.accent) }
            }
            // role chips
            ChipRow {
                listOf("research" to "🔬 Research", "deploy" to "🛠️ Deploy", "live" to "🔴 Live").forEach { (id, lbl) ->
                    Chip(lbl, role == id) { role = id; scope.launch { runCatching { api?.setRole(sessionId ?: "", id) } } }
                }
            }
            Spacer(Modifier.height(6.dp))
            // messages
            LazyColumn(Modifier.weight(1f).fillMaxWidth(), state = listState,
                contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(msgs) { m -> ChatBubble(m) }
            }
            // input
            Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Box(Modifier.weight(1f).clip(RoundedCornerShape(Dimens.radiusSm)).background(pal.surface2)
                    .border(1.dp, pal.border, RoundedCornerShape(Dimens.radiusSm)).padding(horizontal = 14.dp, vertical = 12.dp)) {
                    if (input.isEmpty()) TextUi("Tanya / minta backtest…", 14, color = pal.textMute)
                    BasicTextField(input, { input = it }, textStyle = TextStyle(color = pal.text, fontSize = 14.sp, fontFamily = fonts.ui),
                        cursorBrush = SolidColor(pal.accent), modifier = Modifier.fillMaxWidth())
                }
                Box(Modifier.size(46.dp).clip(RoundedCornerShape(Dimens.radiusSm))
                    .background(if (busy) pal.surface3 else pal.accent).clickable(enabled = !busy) { send() },
                    contentAlignment = Alignment.Center) { Icon("send", 20.dp, pal.accentInk, 2.2f) }
            }
            Spacer(Modifier.windowInsetsBottomHeight(WindowInsets.ime.union(WindowInsets.navigationBars)))
        }
    }
}

@Composable
private fun ChatBubble(m: ChatMsg) {
    val pal = theme
    when (m.role) {
        "user" -> Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            Box(Modifier.widthIn(max = 300.dp).clip(RoundedCornerShape(16.dp)).background(pal.accent).padding(12.dp)) {
                TextUi(m.text, 14, color = pal.accentInk)
            }
        }
        "tool" -> Mono(m.text, 11, FontWeight.Normal, pal.textMute)
        "artifact" -> Row(Modifier.clip(RoundedCornerShape(10.dp)).background(pal.surface2)
            .border(1.dp, pal.border, RoundedCornerShape(10.dp)).padding(horizontal = 12.dp, vertical = 8.dp)) {
            TextUi(m.text, 13, FontWeight.SemiBold, pal.accent)
        }
        else -> Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Start) {
            Box(Modifier.widthIn(max = 320.dp).clip(RoundedCornerShape(16.dp)).background(pal.surface)
                .border(1.dp, pal.border, RoundedCornerShape(16.dp)).padding(12.dp)) {
                TextUi(if (m.text.isEmpty()) "…" else m.text, 14)
            }
        }
    }
}
