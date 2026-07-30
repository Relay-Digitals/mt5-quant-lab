package com.relay.pantauidx.data

import platform.Foundation.NSUserDefaults

actual class TokenStore actual constructor() {
    private val defaults = NSUserDefaults.standardUserDefaults

    actual fun load(): String? = defaults.stringForKey(KEY)
    actual fun save(token: String) { defaults.setObject(token, KEY) }
    actual fun clear() { defaults.removeObjectForKey(KEY) }

    private companion object { const val KEY = "sb_access_token" }
}
