package com.relay.pantauidx.data

import android.annotation.SuppressLint
import android.content.Context

/** Holds the app Context for platform storage. Set once in MainActivity.onCreate. */
@SuppressLint("StaticFieldLeak")
object AppContextHolder {
    lateinit var context: Context
}

actual class TokenStore actual constructor() {
    private val prefs by lazy {
        AppContextHolder.context.getSharedPreferences("pantau_idx", Context.MODE_PRIVATE)
    }

    actual fun load(): String? = prefs.getString(KEY, null)
    actual fun save(token: String) { prefs.edit().putString(KEY, token).apply() }
    actual fun clear() { prefs.edit().remove(KEY).apply() }

    private companion object { const val KEY = "sb_access_token" }
}
