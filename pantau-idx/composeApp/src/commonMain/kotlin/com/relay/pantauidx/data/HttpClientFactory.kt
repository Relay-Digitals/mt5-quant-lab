package com.relay.pantauidx.data

import io.ktor.client.HttpClient

/**
 * Platform-provided Ktor engine:
 *  - Android → CIO
 *  - iOS     → Darwin
 * The common [StockbitApi] configures plugins on top of this base client.
 */
expect fun platformHttpClient(): HttpClient
