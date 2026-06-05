package com.anonymouse.trade.data

/** key-value persisten per-platform. */
expect fun prefGet(key: String): String?
expect fun prefPut(key: String, value: String)

/** sinkron BridgeConfig ↔ storage. Panggil load() saat app start. */
object Settings {
    private const val K_URL = "bridge_url"
    private const val K_TOKEN = "bridge_token"
    private const val K_THEME = "theme_dark"

    fun load() {
        prefGet(K_URL)?.takeIf { it.isNotBlank() }?.let { BridgeConfig.baseUrl = it }
        prefGet(K_TOKEN)?.let { BridgeConfig.token = it }
    }

    fun saveBridge(url: String, token: String) {
        BridgeConfig.baseUrl = url.trim()
        BridgeConfig.token = token.trim()
        prefPut(K_URL, BridgeConfig.baseUrl)
        prefPut(K_TOKEN, BridgeConfig.token)
    }

    fun loadDark(default: Boolean): Boolean = prefGet(K_THEME)?.let { it == "1" } ?: default
    fun saveDark(dark: Boolean) = prefPut(K_THEME, if (dark) "1" else "0")
}
