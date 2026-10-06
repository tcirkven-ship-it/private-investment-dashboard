/**
 * Performance calculations.
 *
 * Accounting rules:
 * - Only external cash flows count as invested capital changes:
 *   DEPOSIT (and TRANSFER) add invested capital, WITHDRAWAL reduces it.
 * - BUY/SELL never change invested capital; they only move value between
 *   cash and holdings.
 * - Total P&L = current value - net invested capital.
 * - Quarterly P&L = end value - start value - quarterly external flow.
 */

export interface PerfTransaction {
  event_type: string;
  event_date: string;
  quantity?: number | null;
  price?: number | null;
  gross_amount: number;
  commission?: number | null;
}

export interface ValuationSnapshot {
  valuation_date: string;
  total_value: number;
}

export interface InvestedCapital {
  value: number;
  estimated: boolean;
}

/**
 * Net invested capital = deposits - withdrawals.
 * If no deposit/withdrawal transactions exist at all, fall back to an
 * estimate from buy/sell activity, clearly flagged as estimated.
 */
export function computeInvestedCapital(txs: PerfTransaction[]): InvestedCapital {
  let deposits = 0;
  let withdrawals = 0;
  for (const t of txs) {
    const gross = Number(t.gross_amount) || 0;
    if (t.event_type === "DEPOSIT" || t.event_type === "TRANSFER") deposits += gross;
    else if (t.event_type === "WITHDRAWAL") withdrawals += gross;
  }
  if (deposits !== 0 || withdrawals !== 0) {
    return { value: deposits - withdrawals, estimated: false };
  }
  // Fallback estimate: nothing external recorded, approximate capital put in.
  let estimate = 0;
  for (const t of txs) {
    const gross = Number(t.gross_amount) || 0;
    const comm = Number(t.commission) || 0;
    if (t.event_type === "BUY") estimate += gross + comm;
    else if (t.event_type === "OPENING_POSITION") estimate += (Number(t.quantity) || 0) * (Number(t.price) || 0);
    else if (t.event_type === "SELL") estimate -= gross - comm;
  }
  return { value: Math.max(0, estimate), estimated: true };
}

export function totalPnl(currentValue: number, invested: number): number {
  return currentValue - invested;
}

export function totalReturnPct(pnl: number, invested: number): number | null {
  if (!Number.isFinite(invested) || invested <= 0) return null;
  return (pnl / invested) * 100;
}

export function hasDeposit(txs: PerfTransaction[]): boolean {
  return txs.some((t) => t.event_type === "DEPOSIT");
}

// ---------------------------------------------------------------------------
// Quarters
// ---------------------------------------------------------------------------

export function quarterLabel(dateStr: string): string {
  const year = Number(dateStr.slice(0, 4));
  const month = Number(dateStr.slice(5, 7));
  return `${year}-Q${Math.floor((month - 1) / 3) + 1}`;
}

export function quarterBounds(label: string): { start: string; end: string } {
  const [yearStr, qStr] = label.split("-Q");
  const year = Number(yearStr);
  const q = Number(qStr);
  const startMonth = (q - 1) * 3 + 1;
  const endMonth = startMonth + 2;
  const endDay = new Date(Date.UTC(year, endMonth, 0)).getUTCDate();
  const start = `${year}-${String(startMonth).padStart(2, "0")}-01`;
  const end = `${year}-${String(endMonth).padStart(2, "0")}-${String(endDay).padStart(2, "0")}`;
  return { start, end };
}

function nextQuarterLabel(label: string): string {
  const [yearStr, qStr] = label.split("-Q");
  const year = Number(yearStr);
  const q = Number(qStr);
  return q === 4 ? `${year + 1}-Q1` : `${year}-Q${q + 1}`;
}

export function previousQuarterLabel(label: string): string {
  const [yearStr, qStr] = label.split("-Q");
  const year = Number(yearStr);
  const q = Number(qStr);
  return q === 1 ? `${year - 1}-Q4` : `${year}-Q${q - 1}`;
}

export function enumerateQuarterLabels(firstDate: string, lastLabel: string): string[] {
  const out: string[] = [];
  let label = quarterLabel(firstDate);
  while (label <= lastLabel && out.length < 200) {
    out.push(label);
    label = nextQuarterLabel(label);
  }
  return out;
}

export interface QuarterRow {
  label: string;
  isInception?: boolean;
  startValue: number | null;
  startValueNote?: string | null;
  endValue: number | null;
  endValueEstimated?: boolean;
  externalFlow: number;
  pnl: number | null;
  returnPct: number | null;
  isCurrent: boolean;
  spyReturnPct: number | null;
  qqqReturnPct: number | null;
}

export function buildQuarterRows(args: {
  transactions: PerfTransaction[];
  valuations: ValuationSnapshot[];
  currentValue: number;
  today: string;
  benchmarkReturns?: { SPY?: Map<string, number | null>; QQQ?: Map<string, number | null> };
}): QuarterRow[] {
  const { transactions, valuations, currentValue, today } = args;
  const currentLabel = quarterLabel(today);
  const lastCompletedLabel = previousQuarterLabel(currentLabel);
  const dates = [
    ...transactions.map((t) => t.event_date),
    ...valuations.map((v) => v.valuation_date),
  ].filter(Boolean).sort();
  const firstDate = dates.length > 0 ? dates[0] : today;
  const labels = enumerateQuarterLabels(firstDate, currentLabel);
  const sorted = [...valuations].sort((a, b) => a.valuation_date.localeCompare(b.valuation_date));

  const findLatestOnOrBefore = (date: string): ValuationSnapshot | null => {
    for (let i = sorted.length - 1; i >= 0; i--) {
      if (sorted[i].valuation_date <= date) return sorted[i];
    }
    return null;
  };

  return labels.map((label) => {
    const { start, end } = quarterBounds(label);
    const isCurrent = label === currentLabel;

    // Start value: snapshot on/before quarter start; exact zero when the
    // portfolio had no activity yet; otherwise an in-quarter snapshot (noted).
    let startValue: number | null = null;
    let startValueNote: string | null = null;
    const startSnap = findLatestOnOrBefore(start);
    if (startSnap) {
      startValue = Number(startSnap.total_value);
    } else if (!transactions.some((t) => t.event_date < start)) {
      startValue = 0;
    } else {
      const inQuarter = sorted.find((v) => v.valuation_date >= start && v.valuation_date <= end);
      if (inQuarter) {
        startValue = Number(inQuarter.total_value);
        startValueNote = `as of ${inQuarter.valuation_date}`;
      }
    }

    // End value: live value for the current quarter; snapshot on/before quarter
    // end for past quarters; flagged "latest available" fallback otherwise.
    let endValue: number | null = null;
    let endValueEstimated = false;
    if (isCurrent) {
      endValue = currentValue;
    } else {
      const endSnap = findLatestOnOrBefore(end);
      if (endSnap) {
        endValue = Number(endSnap.total_value);
      } else {
        const after = sorted.find((v) => v.valuation_date > end);
        if (after) {
          endValue = Number(after.total_value);
          endValueEstimated = true;
        } else if (sorted.length === 0 && label === lastCompletedLabel) {
          endValue = currentValue;
          endValueEstimated = true;
        }
      }
    }

    let externalFlow = 0;
    for (const t of transactions) {
      if (t.event_date < start || t.event_date > end) continue;
      const gross = Number(t.gross_amount) || 0;
      if (t.event_type === "DEPOSIT" || t.event_type === "TRANSFER") externalFlow += gross;
      else if (t.event_type === "WITHDRAWAL") externalFlow -= gross;
    }

    const pnl = startValue !== null && endValue !== null ? endValue - startValue - externalFlow : null;
    // Return denominator: start value, or capital deployed when the quarter
    // began with an empty portfolio (start = 0).
    const denominator = startValue !== null && startValue > 0 ? startValue : externalFlow > 0 ? externalFlow : null;
    const returnPct = pnl !== null && denominator !== null ? (pnl / denominator) * 100 : null;

    return {
      label,
      startValue,
      startValueNote,
      endValue,
      endValueEstimated,
      externalFlow,
      pnl,
      returnPct,
      isCurrent,
      spyReturnPct: args.benchmarkReturns?.SPY?.get(label) ?? null,
      qqqReturnPct: args.benchmarkReturns?.QQQ?.get(label) ?? null,
    };
  });
}

/**
 * Lifetime row: start at zero (portfolio inception), current value as end,
 * external flow = net invested capital, P&L = current - net invested.
 */
export function buildInceptionRow(args: {
  transactions: PerfTransaction[];
  currentValue: number;
  netInvested: number;
  today: string;
  benchmarkObservations?: {
    SPY?: { observation_date: string; total_return_index: number | null }[];
    QQQ?: { observation_date: string; total_return_index: number | null }[];
  };
}): QuarterRow {
  const { transactions, currentValue, netInvested, today } = args;
  const pnl = currentValue - netInvested;
  const returnPct = netInvested > 0 ? (pnl / netInvested) * 100 : null;

  const firstDate = transactions.map((t) => t.event_date).filter(Boolean).sort()[0];
  const spyReturnPct =
    firstDate && args.benchmarkObservations?.SPY
      ? benchmarkRangeReturn(args.benchmarkObservations.SPY, firstDate, today)
      : null;
  const qqqReturnPct =
    firstDate && args.benchmarkObservations?.QQQ
      ? benchmarkRangeReturn(args.benchmarkObservations.QQQ, firstDate, today)
      : null;

  return {
    label: "Since inception",
    isInception: true,
    startValue: 0,
    endValue: currentValue,
    externalFlow: netInvested,
    pnl,
    returnPct,
    isCurrent: false,
    spyReturnPct,
    qqqReturnPct,
  };
}

/**
 * Return over an arbitrary date range from total-return index observations.
 * Base = last observation on or before `from`; close = last on or before `to`.
 */
export function benchmarkRangeReturn(
  obs: { observation_date: string; total_return_index: number | null }[],
  from: string,
  to: string,
): number | null {
  const sorted = [...obs]
    .filter((o) => o.total_return_index !== null && Number(o.total_return_index) > 0)
    .sort((a, b) => a.observation_date.localeCompare(b.observation_date));
  const findLatestOnOrBefore = (date: string) => {
    for (let i = sorted.length - 1; i >= 0; i--) {
      if (sorted[i].observation_date <= date) return sorted[i];
    }
    return null;
  };
  const base = findLatestOnOrBefore(from);
  const close = findLatestOnOrBefore(to);
  if (base && close && close.observation_date > base.observation_date) {
    return (Number(close.total_return_index) / Number(base.total_return_index) - 1) * 100;
  }
  return null;
}

/**
 * Quarterly returns from benchmark total-return index observations.
 * Base = last observation on or before the quarter start; close = last
 * observation on or before the quarter end. Null when either is missing.
 */
export function benchmarkQuarterReturns(
  obs: { observation_date: string; total_return_index: number | null }[],
): Map<string, number | null> {
  const out = new Map<string, number | null>();
  const sorted = [...obs]
    .filter((o) => o.total_return_index !== null && Number(o.total_return_index) > 0)
    .sort((a, b) => a.observation_date.localeCompare(b.observation_date));
  if (sorted.length === 0) return out;

  const labels = enumerateQuarterLabels(
    sorted[0].observation_date,
    quarterLabel(sorted[sorted.length - 1].observation_date),
  );
  for (const label of labels) {
    const { start, end } = quarterBounds(label);
    const findLatestOnOrBefore = (date: string) => {
      for (let i = sorted.length - 1; i >= 0; i--) {
        if (sorted[i].observation_date <= date) return sorted[i];
      }
      return null;
    };
    const base = findLatestOnOrBefore(start);
    const closing = findLatestOnOrBefore(end);
    if (base && closing && closing.observation_date !== base.observation_date) {
      out.set(label, (Number(closing.total_return_index) / Number(base.total_return_index) - 1) * 100);
    } else {
      out.set(label, null);
    }
  }
  return out;
}
