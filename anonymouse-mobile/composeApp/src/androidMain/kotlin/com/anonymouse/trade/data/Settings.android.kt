package com.anonymouse.trade.data

import android.content.Context

/** di-set di MainActivity.onCreate sebelum Settings.load(). */
lateinit var appContext: Context

private val sp by lazy { appContext.getSharedPreferences("anonymouse", Context.MODE_PRIVATE) }

actual fun prefGet(key: String): String? = sp.getString(key, null)
actual fun prefPut(key: String, value: String) { sp.edit().putString(key, value).apply() }
