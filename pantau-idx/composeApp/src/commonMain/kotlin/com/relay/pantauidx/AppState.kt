package com.relay.pantauidx

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.relay.pantauidx.data.Candle
import com.relay.pantauidx.data.IdxRepository
import com.relay.pantauidx.data.InsiderTx
import com.relay.pantauidx.data.ScreenPreset
import com.relay.pantauidx.data.StockRow
import com.relay.pantauidx.data.StockbitApi
import com.relay.pantauidx.data.StockbitAuth
import com.relay.pantauidx.data.TokenProvider
import com.relay.pantauidx.data.TokenStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

enum class Tab { WATCHLIST, MARKET, INSIDER, PORTFOLIO }
enum class Root { SPLASH, AUTH, MAIN, DETAIL }
enum class AuthStep { CREDENTIALS, OTP }

/**
 * Holds navigation + all screen data + the Stockbit login flow.
 * Framework-light observable state so it works on every KMP target.
 */
class AppState(private val scope: CoroutineScope) {

    private val store = TokenStore()
    val tokens = TokenProvider(store.load() ?: "")
    private val api = StockbitApi(tokens)
    private val repo = IdxRepository(api, tokens)
    private val auth = StockbitAuth(api, tokens)

    var root by mutableStateOf(Root.SPLASH)
        private set
    var tab by mutableStateOf(Tab.WATCHLIST)
        private set
    var isLive by mutableStateOf(false)
        private set

    // ---- auth state ----
    var authStep by mutableStateOf(AuthStep.CREDENTIALS)
        private set
    var authBusy by mutableStateOf(false)
        private set
    var authError by mutableStateOf<String?>(null)
        private set
    var authInfo by mutableStateOf<String?>(null)
        private set
    private var otpSession: String = ""

    val watchlist = mutableStateListOf<StockRow>()
    val screens = mutableStateListOf<ScreenPreset>()
    val trending = mutableStateListOf<StockRow>()
    val insiders = mutableStateListOf<InsiderTx>()

    var detailSymbol by mutableStateOf<StockRow?>(null)
        private set
    val detailCandles = mutableStateListOf<Candle>()
    var loading by mutableStateOf(false)
        private set

    fun start() = loadAll()

    /** Splash tap: go straight to the app if we already hold a token, else to login. */
    fun skipSplash() { root = if (tokens.isAuthenticated) Root.MAIN else Root.AUTH }
    fun continueAsGuest() { root = Root.MAIN } // browse with SampleData
    fun select(t: Tab) { tab = t }

    fun login(username: String, password: String) {
        if (authBusy) return
        authBusy = true; authError = null; authInfo = null
        scope.launch {
            when (val r = auth.login(username.trim(), password)) {
                is StockbitAuth.Result.Success -> onAuthSuccess()
                is StockbitAuth.Result.NeedsOtp -> {
                    otpSession = r.session; authStep = AuthStep.OTP; authInfo = r.message
                }
                is StockbitAuth.Result.Error -> authError = r.message
            }
            authBusy = false
        }
    }

    fun verifyOtp(code: String) {
        if (authBusy) return
        authBusy = true; authError = null
        scope.launch {
            when (val r = auth.verifyOtp(code.trim(), otpSession)) {
                is StockbitAuth.Result.Success -> onAuthSuccess()
                is StockbitAuth.Result.NeedsOtp -> authError = "Kode salah, coba lagi"
                is StockbitAuth.Result.Error -> authError = r.message
            }
            authBusy = false
        }
    }

    private fun onAuthSuccess() {
        store.save(tokens.current)
        authStep = AuthStep.CREDENTIALS
        root = Root.MAIN
        loadAll()
    }

    fun logout() {
        store.clear(); tokens.clear(); isLive = false
        root = Root.AUTH
    }

    fun openDetail(row: StockRow) {
        detailSymbol = row
        root = Root.DETAIL
        detailCandles.clear()
        scope.launch {
            val c = repo.candles(row.code)
            detailCandles.addAll(c.value)
            isLive = isLive || c.live
        }
    }

    fun closeDetail() { root = Root.MAIN; detailSymbol = null }

    private fun loadAll() {
        loading = true
        scope.launch {
            val wl = repo.watchlistRows(); watchlist.clear(); watchlist.addAll(wl.value)
            val sc = repo.screens(); screens.clear(); screens.addAll(sc.value)
            val tr = repo.trending(); trending.clear(); trending.addAll(tr.value)
            val ins = repo.insiders(listOf("BBCA", "ADRO", "ANTM", "GOTO")); insiders.clear(); insiders.addAll(ins.value)
            isLive = wl.live || sc.live || tr.live || ins.live
            loading = false
        }
    }
}
