package com.relay.pantauidx.data

/**
 * Single source of truth for the UI. Attempts live Stockbit calls; if the token is
 * missing/expired (exodus returns 401) it degrades to [SampleData] so the app is always
 * demoable. Every list method reports which path it used via [DataResult.live].
 */
class IdxRepository(
    private val api: StockbitApi,
    private val tokens: TokenProvider,
) {
    data class DataResult<T>(val value: T, val live: Boolean, val error: String? = null)

    private suspend fun <T> guarded(sample: T, block: suspend () -> T): DataResult<T> {
        if (!tokens.isAuthenticated) return DataResult(sample, live = false)
        return try {
            val v = block()
            // Some screens legitimately return empty; treat empty as a soft miss → sample.
            if (v is List<*> && v.isEmpty()) DataResult(sample, live = false, error = "empty")
            else DataResult(v, live = true)
        } catch (t: Throwable) {
            DataResult(sample, live = false, error = t.message ?: "network error")
        }
    }

    suspend fun watchlistRows(): DataResult<List<StockRow>> =
        guarded(SampleData.watchlist) { api.screenerUniverse().ifEmpty { api.trending() } }

    suspend fun screens(): DataResult<List<ScreenPreset>> =
        guarded(SampleData.presets) { api.screenerPresets() }

    suspend fun runScreen(id: String): DataResult<List<StockRow>> =
        guarded(SampleData.watchlist) { api.runScreen(id) }

    suspend fun trending(): DataResult<List<StockRow>> =
        guarded(SampleData.trending) { api.trending() }

    suspend fun insiders(symbols: List<String>): DataResult<List<InsiderTx>> =
        guarded(SampleData.insiders) { api.insider(symbols) }

    suspend fun candles(symbol: String): DataResult<List<Candle>> =
        guarded(SampleData.candles(symbol)) { api.candles(symbol) }
}
