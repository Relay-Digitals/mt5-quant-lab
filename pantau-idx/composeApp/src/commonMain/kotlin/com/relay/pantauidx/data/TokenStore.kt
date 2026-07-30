package com.relay.pantauidx.data

/** Persists the Stockbit access token across launches. Platform-backed. */
expect class TokenStore() {
    fun load(): String?
    fun save(token: String)
    fun clear()
}
