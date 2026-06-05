package com.anonymouse.trade

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import com.anonymouse.trade.data.BridgeConfig
import com.anonymouse.trade.data.Settings
import com.anonymouse.trade.data.appContext
import com.anonymouse.trade.data.bridgeApi
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlin.math.abs

const val CHANNEL_ID = "anon_alerts"

private fun ensureChannel(ctx: Context) {
    val mgr = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
    if (mgr.getNotificationChannel(CHANNEL_ID) == null) {
        mgr.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Anonymouse Alerts", NotificationManager.IMPORTANCE_HIGH)
                .apply { description = "Backtest selesai, ignition exit, sinyal" }
        )
    }
}

private fun registerToken(token: String) {
    CoroutineScope(Dispatchers.IO).launch { runCatching { bridgeApi()?.registerPush(token) } }
}

/** dipanggil dari MainActivity: buat channel + ambil token + daftarkan ke bridge. */
fun initFcm(ctx: Context) {
    ensureChannel(ctx)
    if (!BridgeConfig.configured) return
    FirebaseMessaging.getInstance().token.addOnSuccessListener { token -> registerToken(token) }
}

fun showNotif(ctx: Context, title: String, body: String) {
    ensureChannel(ctx)
    val n = Notification.Builder(ctx, CHANNEL_ID)
        .setContentTitle(title)
        .setContentText(body)
        .setStyle(Notification.BigTextStyle().bigText(body))
        .setSmallIcon(android.R.drawable.ic_dialog_info)
        .setAutoCancel(true)
        .build()
    (ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
        .notify(abs((title + body).hashCode()) % 100000, n)
}

class AnonMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        appContext = applicationContext
        runCatching { Settings.load() }
        registerToken(token)
    }
    override fun onMessageReceived(msg: RemoteMessage) {
        val title = msg.notification?.title ?: msg.data["title"] ?: "Anonymouse Trade"
        val body = msg.notification?.body ?: msg.data["body"] ?: ""
        showNotif(applicationContext, title, body)
    }
}
