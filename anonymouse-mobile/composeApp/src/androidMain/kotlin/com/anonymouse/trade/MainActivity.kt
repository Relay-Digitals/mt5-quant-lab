package com.anonymouse.trade

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.anonymouse.trade.data.Settings
import com.anonymouse.trade.data.appContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        appContext = applicationContext
        Settings.load()
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        // izin notifikasi (Android 13+)
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
        }
        // FCM: buat channel + daftarkan token ke bridge
        initFcm(applicationContext)

        setContent { App() }
    }
}
