package com.anonymouse.trade.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class SignalDto(
    val pair: String = "", val dir: String = "LONG", val entry: Double = 0.0,
    val roi: Double = 0.0, val status: String = "active", val market: String = "forex",
    val strat: String = "", val type: String = "position", val note: String = "",
    val verdict: String = "", // "green" | "amber" | "red" | "" — hasil gate validasi
)
@Serializable
data class SignalsResp(val signals: List<SignalDto> = emptyList(), val source: String = "")

private val sigJson = Json { ignoreUnknownKeys = true; isLenient = true }

fun buildSignalsPrompt(): String = """
    TUGAS: Kumpulkan SINYAL trading dari sistem quant. Keluarkan HANYA satu blok JSON {"signals":[...],"source":"live"}.

    A. POSISI TERBUKA (type:"position", status:"active"):
       - forex: MT5 API http://192.168.0.111:8000 GET /api/positions → pair=symbol, dir BUY→LONG/SELL→SHORT, entry=price_open, roi=profit% berjalan, market:"forex", strat dari magic (770003=TREND,770004=MEANREV,770007=WRRSI,770002=MAOSC).
       - IDX: /opt/idx-quant/data/ara_paper.json status=="open" → pair=code, dir:"LONG", entry, roi=(cur/entry-1)*100, market:"idx", strat:"ARA".

    B. KANDIDAT ARA HARI INI (type:"ara", status:"candidate", market:"idx", strat:"ARA-hunter"):
       Jalankan: PYTHONPATH=/opt/idx-quant /opt/idx-quant/venv/bin/python -c "..." pakai modul stockbit_history utk ambil movers TOP_GAINER. Filter: ticker 4-huruf, naik>=15% hari ini, nilai transaksi>=Rp10 miliar. pair=code, dir:"LONG", entry=harga sekarang, roi=%naik hari ini, note="near-ARA +X%".
       Lalu utk TIAP kandidat (maks 6) jalankan GATE VALIDASI: PYTHONPATH=/opt/idx-quant /opt/idx-quant/venv/bin/python idx_ara_validate.py <CODE> (cek foreign-flow 5hr, orderbook/ARA-lock, corp-action, penny). Set field "verdict": "green" (🟢 aman/akumulasi), "amber" (🟡 hati-hati), "red" (🔴 risiko/ARA-lock/distribusi/skip). note=alasan singkat (mis. "asing serap" / "ARA-lock" / "distribusi").

    C. VOLUME-IGNITION (type:"ignition", status:"watch", market:"idx") — OPSIONAL, hanya bila ada hasil idx_volign terbaru: pair=code, note="ignition vrX".

    Maks 12 sinyal; urutan: posisi terbuka dulu, lalu kandidat verdict green→amber→red (roi desc). Kalau market IDX libur/krisis & tak ada kandidat, cukup posisi terbuka. Angka HARUS nyata. Jawab HANYA blok ```json ... ```.
""".trimIndent()

fun parseSignals(text: String): List<SignalDto>? {
    val js = extractObj(text) ?: return null
    val d = runCatching { sigJson.decodeFromString<SignalsResp>(js) }.getOrNull() ?: return null
    return d.signals
}

fun mockSignals(): List<SignalDto> = DB.signals.map {
    SignalDto(it.pair, it.dir, it.entry, it.roi, it.status,
        if (it.pair.contains("USDT")) "crypto" else if (it.pair.contains("/")) "forex" else "idx",
        DB.providerById(it.provider).name, "position", "")
}

internal fun extractObj(text: String): String? {
    val fence = Regex("```(?:json)?\\s*([\\s\\S]*?)```").find(text)?.groupValues?.getOrNull(1)?.trim()
    val src = fence ?: text
    val start = src.indexOf('{'); if (start < 0) return null
    var depth = 0
    for (i in start until src.length) when (src[i]) {
        '{' -> depth++
        '}' -> { depth--; if (depth == 0) return src.substring(start, i + 1) }
    }
    return null
}
