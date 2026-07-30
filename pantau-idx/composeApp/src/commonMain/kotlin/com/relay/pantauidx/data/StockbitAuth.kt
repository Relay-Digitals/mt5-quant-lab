package com.relay.pantauidx.data

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

/**
 * Stockbit exodus data-token login flow (powers screener / charts / watchlist / insider).
 *
 *   login/v6/username  { username, password }        → tokens  OR  new-device challenge
 *   login/v6/new-device/verify  { otp, session, ... } → tokens
 *
 * Field names for the request bodies are not exhaustively documented (docs show
 * `LoginUserNamePasswordDataParam`), so we send the conventional keys and parse the
 * response tolerantly (search for the first access/refresh token anywhere in the tree).
 * The securities/trading (carina) token + PIN is a SEPARATE flow — see [PortfolioApi].
 */
class StockbitAuth(
    private val api: StockbitApi,
    private val tokens: TokenProvider,
    private val json: Json = Json { ignoreUnknownKeys = true; isLenient = true },
) {
    sealed interface Result {
        data class Success(val access: String, val refresh: String?) : Result
        /** New device: an OTP has been sent; call [verifyOtp] with [session]. */
        data class NeedsOtp(val session: String, val message: String) : Result
        data class Error(val message: String) : Result
    }

    suspend fun login(username: String, password: String, deviceId: String = DEVICE_ID): Result {
        val body = buildJsonObject {
            put("username", username)
            put("password", password)
            put("device_id", deviceId)
            put("player_id", PLAYER_ID)
        }.toString()
        return runCatching { api.postText("login/v6/username", body, auth = false) }
            .fold({ parseLogin(it) }, { Result.Error(it.message ?: "network error") })
    }

    suspend fun verifyOtp(otp: String, session: String, deviceId: String = DEVICE_ID): Result {
        val body = buildJsonObject {
            put("otp", otp)
            put("session", session)
            put("device_id", deviceId)
            put("player_id", PLAYER_ID)
        }.toString()
        return runCatching { api.postText("login/v6/new-device/verify", body, auth = false) }
            .fold({ parseLogin(it) }, { Result.Error(it.message ?: "network error") })
    }

    private fun parseLogin(raw: String): Result {
        val root = runCatching { json.parseToJsonElement(raw) }.getOrNull()
            ?: return Result.Error("bad response")
        val access = root.findString("access_token", "accessToken", "token")
        if (access != null) {
            val refresh = root.findString("refresh_token", "refreshToken")
            tokens.set(access)
            return Result.Success(access, refresh)
        }
        val session = root.findString("session", "challenge_token", "session_id")
        val msg = root.findString("message") ?: "Verifikasi perangkat baru diperlukan"
        if (session != null) return Result.NeedsOtp(session, msg)
        return Result.Error(root.findString("message") ?: "Login gagal")
    }

    /** DFS for the first string value under any of [keys] (skips obvious non-token fields). */
    private fun JsonElement.findString(vararg keys: String): String? {
        when (this) {
            is JsonObject -> {
                for ((k, v) in this) {
                    if (k in keys && v is JsonPrimitive && v.isString && v.content.isNotBlank()) return v.content
                }
                for ((_, v) in this) v.findString(*keys)?.let { return it }
            }
            is JsonArray -> for (v in this) v.findString(*keys)?.let { return it }
            else -> {}
        }
        return null
    }

    companion object {
        // From stockbit-docs/stockbit_token.env — replace per install.
        const val DEVICE_ID = "f4f20993837a2bbd61a2fec250553e93"
        const val PLAYER_ID = "2292F1CB-37AD-42C7-942E-FBD6C0F26669"
    }
}
