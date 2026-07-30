package com.relay.pantauidx.data

import kotlin.math.abs
import kotlin.math.roundToLong

/** Multiplatform number formatting (no java.text in commonMain). */
object Fmt {

    fun thousands(v: Double, decimals: Int = 0): String {
        val neg = v < 0
        val rounded = if (decimals == 0) abs(v).roundToLong().toString()
        else {
            val factor = pow10(decimals)
            val scaled = (abs(v) * factor).roundToLong()
            val whole = scaled / factor
            val frac = (scaled % factor).toString().padStart(decimals, '0')
            "$whole.$frac"
        }
        val dot = rounded.indexOf('.')
        val intPart = if (dot >= 0) rounded.substring(0, dot) else rounded
        val fracPart = if (dot >= 0) rounded.substring(dot) else ""
        val sb = StringBuilder()
        for ((i, ch) in intPart.withIndex()) {
            if (i > 0 && (intPart.length - i) % 3 == 0) sb.append(',')
            sb.append(ch)
        }
        return (if (neg) "-" else "") + sb.toString() + fracPart
    }

    /** IDR price like 9.650 (IDX convention uses '.' as thousands, but we keep ',' for LTR clarity). */
    fun price(v: Double): String = thousands(v, 0)

    fun signedPct(v: Double): String {
        val s = thousands(abs(v), 2)
        return (if (v >= 0) "+" else "-") + s + "%"
    }

    fun signed(v: Double, decimals: Int = 0): String {
        val s = thousands(abs(v), decimals)
        return (if (v >= 0) "+" else "-") + s
    }

    /** Compact big rupiah: 11.2 T, 184 M, 18.4 M lot. */
    fun compact(v: Double): String {
        val a = abs(v)
        val (num, suf) = when {
            a >= 1e12 -> v / 1e12 to " T"
            a >= 1e9 -> v / 1e9 to " B"
            a >= 1e6 -> v / 1e6 to " M"
            a >= 1e3 -> v / 1e3 to " K"
            else -> v to ""
        }
        return thousands(num, if (abs(num) >= 100 || suf.isEmpty()) 0 else 1) + suf
    }

    private fun pow10(n: Int): Long {
        var r = 1L; repeat(n) { r *= 10 }; return r
    }
}
