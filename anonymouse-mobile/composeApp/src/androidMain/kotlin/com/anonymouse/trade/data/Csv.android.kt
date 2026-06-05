package com.anonymouse.trade.data

import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

actual fun shareCsv(filename: String, content: String): String {
    return try {
        val ctx = appContext
        val dir = File(ctx.cacheDir, "exports").apply { mkdirs() }
        val f = File(dir, filename)
        f.writeText(content)
        val uri = FileProvider.getUriForFile(ctx, "${ctx.packageName}.fileprovider", f)
        val share = Intent(Intent.ACTION_SEND).apply {
            type = "text/csv"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_SUBJECT, filename)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        ctx.startActivity(Intent.createChooser(share, "Export CSV").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        "CSV diekspor: $filename"
    } catch (e: Exception) {
        "Gagal export: ${e.message?.take(60)}"
    }
}
