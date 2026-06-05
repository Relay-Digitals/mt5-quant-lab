package com.anonymouse.trade.data

import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.HttpTimeout

actual fun createHttpClient(): HttpClient = HttpClient(CIO) {
    install(HttpTimeout) {
        // backtest/forward bisa lama → stream tak boleh timeout cepat
        requestTimeoutMillis = 15 * 60 * 1000
        socketTimeoutMillis = 15 * 60 * 1000
        connectTimeoutMillis = 20_000
    }
}
