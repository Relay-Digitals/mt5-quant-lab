package com.relay.pantauidx.data

/**
 * Static Stockbit config. Mirrors `stockbit-quant/stockbit_client.py`:
 *   base = exodus.stockbit.com, Bearer JWT + the mandatory okhttp/app headers
 *   (without User-Agent okhttp Cloudflare returns 1010).
 *
 * The access token is short-lived — in production inject it from secure storage / a
 * refresh flow. For dev, [TokenProvider] reads a build-time value or an in-memory token
 * set after login. Do NOT commit a real token here.
 */
object StockbitConfig {
    const val BASE_URL = "https://exodus.stockbit.com"
    const val CARINA_URL = "https://carina.stockbit.com" // trading (order/*) — separate Authorization-Carina token
    const val APP_VERSION = "3.21.0"
    const val PLATFORM = "android"
    const val USER_AGENT = "okhttp/4.12.0"
    const val ACCEPT_LANGUAGE = "id"
}

/** Supplies the current access token. Replace [current] via login/refresh. */
class TokenProvider(initial: String = "") {
    var current: String = initial
        private set

    fun set(token: String) { current = token }
    fun clear() { current = "" }
    val isAuthenticated: Boolean get() = current.isNotBlank()
}
