package com.relay.pantauidx.data

import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO

actual fun platformHttpClient(): HttpClient = HttpClient(CIO)
