package com.anonymouse.trade.data

/** tulis CSV + share via sheet (per-platform). Return pesan status. */
expect fun shareCsv(filename: String, content: String): String

fun tradesToCsv(cfg: BacktestCfg, result: BacktestResult): String = buildString {
    append("# backtest ${cfg.strategy} ${cfg.pair} cap=${cfg.capital} risk=${cfg.riskPct}% period=${cfg.period}d\n")
    append("# return=${result.stats.totalReturn}% PF=${result.stats.profitFactor} winRate=${result.stats.winRate}% maxDD=${result.stats.maxDD}% sharpe=${result.stats.sharpe}\n")
    append("n,dir,day,pnl,result\n")
    result.trades.forEach { t ->
        append("${t.n},${t.dir},${t.day},${t.pnl},${if (t.win) "WIN" else "LOSS"}\n")
    }
}
