"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase";
import { Info, TrendingUp, Shield, BarChart3 } from "lucide-react";

interface Holding {
  rank: number;
  ticker: string;
  company_name: string;
  target_weight: number;
  b2_score: number;
  quality_percentile: number;
  quality_components_ok: number;
  sector: string;
  industry: string;
  inclusion_reason: string;
}

const MOCK_HOLDINGS: Holding[] = [
  { rank: 1, ticker: "MU", company_name: "Micron Technology, Inc.", target_weight: 3.333, b2_score: 0.988, quality_percentile: 0.699, quality_components_ok: 4, sector: "Technology", industry: "Semiconductors", inclusion_reason: "Strong momentum combined with above-median Quality score" },
  { rank: 2, ticker: "DOCN", company_name: "DigitalOcean Holdings, Inc.", target_weight: 3.333, b2_score: 0.988, quality_percentile: 0.338, quality_components_ok: 4, sector: "Technology", industry: "Software - Infrastructure", inclusion_reason: "Top-decile momentum; excluded if Quality were much weaker" },
  { rank: 3, ticker: "BE", company_name: "Bloom Energy Corporation", target_weight: 3.333, b2_score: 0.988, quality_percentile: 0.255, quality_components_ok: 4, sector: "Industrials", industry: "Electrical Equipment & Parts", inclusion_reason: "Strong Price signal" },
  { rank: 4, ticker: "VICR", company_name: "Vicor Corporation", target_weight: 3.333, b2_score: 0.988, quality_percentile: 0.753, quality_components_ok: 4, sector: "Technology", industry: "Electronic Components", inclusion_reason: "Top momentum and strong Quality profile" },
  { rank: 5, ticker: "TTMI", company_name: "TTM Technologies, Inc.", target_weight: 3.333, b2_score: 0.988, quality_percentile: 0.280, quality_components_ok: 4, sector: "Technology", industry: "Electronic Components", inclusion_reason: "Very strong momentum" },
  { rank: 6, ticker: "MXL", company_name: "MaxLinear, Inc.", target_weight: 3.333, b2_score: 0.988, quality_percentile: 0.328, quality_components_ok: 4, sector: "Technology", industry: "Semiconductors", inclusion_reason: "Excellent Price ranking" },
  { rank: 7, ticker: "WDC", company_name: "Western Digital Corporation", target_weight: 3.333, b2_score: 0.988, quality_percentile: 0.751, quality_components_ok: 4, sector: "Technology", industry: "Computer Hardware", inclusion_reason: "Top momentum with very strong Quality" },
  { rank: 8, ticker: "SYRE", company_name: "Spyre Therapeutics, Inc.", target_weight: 3.333, b2_score: 0.981, quality_percentile: 0.579, quality_components_ok: 2, sector: "Healthcare", industry: "Biotechnology", inclusion_reason: "Strong Price signal" },
  { rank: 9, ticker: "POWL", company_name: "Powell Industries, Inc.", target_weight: 3.333, b2_score: 0.979, quality_percentile: 0.892, quality_components_ok: 4, sector: "Industrials", industry: "Electrical Equipment & Parts", inclusion_reason: "Strong Price and excellent Quality" },
  { rank: 10, ticker: "STRL", company_name: "Sterling Infrastructure, Inc.", target_weight: 3.333, b2_score: 0.979, quality_percentile: 0.789, quality_components_ok: 4, sector: "Industrials", industry: "Engineering & Construction", inclusion_reason: "Strong momentum with solid Quality" },
  { rank: 11, ticker: "AMD", company_name: "Advanced Micro Devices, Inc.", target_weight: 3.333, b2_score: 0.974, quality_percentile: 0.731, quality_components_ok: 4, sector: "Technology", industry: "Semiconductors", inclusion_reason: "Strong Price and Quality" },
  { rank: 12, ticker: "AGX", company_name: "Argan, Inc.", target_weight: 3.333, b2_score: 0.959, quality_percentile: 0.800, quality_components_ok: 4, sector: "Industrials", industry: "Engineering & Construction", inclusion_reason: "Good momentum, excellent Quality" },
  { rank: 13, ticker: "GTX", company_name: "Garrett Motion Inc.", target_weight: 3.333, b2_score: 0.952, quality_percentile: 0.578, quality_components_ok: 4, sector: "Consumer Cyclical", industry: "Auto Parts", inclusion_reason: "Good momentum, adequate Quality" },
  { rank: 14, ticker: "MYRG", company_name: "MYR Group Inc.", target_weight: 3.333, b2_score: 0.952, quality_percentile: 0.690, quality_components_ok: 4, sector: "Industrials", industry: "Engineering & Construction", inclusion_reason: "Good Price signal with solid Quality" },
  { rank: 15, ticker: "FIX", company_name: "Comfort Systems USA, Inc.", target_weight: 3.333, b2_score: 0.949, quality_percentile: 0.880, quality_components_ok: 4, sector: "Industrials", industry: "Engineering & Construction", inclusion_reason: "Strong Quality and good momentum" },
  { rank: 16, ticker: "MTRN", company_name: "Materion Corporation", target_weight: 3.333, b2_score: 0.927, quality_percentile: 0.421, quality_components_ok: 4, sector: "Basic Materials", industry: "Other Industrial Metals & Mining", inclusion_reason: "Adequate momentum" },
  { rank: 17, ticker: "ELVN", company_name: "Enliven Therapeutics, Inc.", target_weight: 3.333, b2_score: 0.927, quality_percentile: 0.381, quality_components_ok: 2, sector: "Healthcare", industry: "Biotechnology", inclusion_reason: "Adequate Price signal" },
  { rank: 18, ticker: "VRT", company_name: "Vertiv Holdings Co.", target_weight: 3.333, b2_score: 0.940, quality_percentile: 0.807, quality_components_ok: 4, sector: "Industrials", industry: "Electrical Equipment & Parts", inclusion_reason: "Good Price and Quality" },
  { rank: 19, ticker: "BTSG", company_name: "BrightSpring Health Services", target_weight: 3.333, b2_score: 0.925, quality_percentile: 0.396, quality_components_ok: 4, sector: "Healthcare", industry: "Health Information Services", inclusion_reason: "Adequate momentum" },
  { rank: 20, ticker: "KGS", company_name: "Kodiak Gas Services, Inc.", target_weight: 3.333, b2_score: 0.930, quality_percentile: 0.420, quality_components_ok: 4, sector: "Energy", industry: "Oil & Gas Equipment & Services", inclusion_reason: "Adequate Price and Quality" },
  { rank: 21, ticker: "MOD", company_name: "Modine Manufacturing Company", target_weight: 3.333, b2_score: 0.931, quality_percentile: 0.500, quality_components_ok: 4, sector: "Consumer Cyclical", industry: "Auto Parts", inclusion_reason: "Average Quality, good Price" },
  { rank: 22, ticker: "INSW", company_name: "International Seaways, Inc.", target_weight: 3.333, b2_score: 0.913, quality_percentile: 0.777, quality_components_ok: 4, sector: "Energy", industry: "Oil & Gas Midstream", inclusion_reason: "Good Quality, moderate Price" },
  { rank: 23, ticker: "SPHR", company_name: "Sphere Entertainment Co.", target_weight: 3.333, b2_score: 0.927, quality_percentile: 0.558, quality_components_ok: 4, sector: "Communication Services", industry: "Entertainment", inclusion_reason: "Moderate Quality and Price" },
  { rank: 24, ticker: "IRDM", company_name: "Iridium Communications Inc.", target_weight: 3.333, b2_score: 0.903, quality_percentile: 0.530, quality_components_ok: 4, sector: "Communication Services", industry: "Telecom Services", inclusion_reason: "Moderate Quality" },
  { rank: 25, ticker: "TXG", company_name: "10x Genomics, Inc.", target_weight: 3.333, b2_score: 0.898, quality_percentile: 0.653, quality_components_ok: 4, sector: "Healthcare", industry: "Health Information Services", inclusion_reason: "Good Quality" },
  { rank: 26, ticker: "TWST", company_name: "Twist Bioscience Corporation", target_weight: 3.333, b2_score: 0.898, quality_percentile: 0.495, quality_components_ok: 4, sector: "Healthcare", industry: "Diagnostics & Research", inclusion_reason: "Moderate Quality" },
  { rank: 27, ticker: "WTTR", company_name: "Select Water Solutions, Inc.", target_weight: 3.333, b2_score: 0.902, quality_percentile: 0.461, quality_components_ok: 4, sector: "Energy", industry: "Oil & Gas Equipment & Services", inclusion_reason: "Moderate Quality" },
  { rank: 28, ticker: "EWTX", company_name: "Edgewise Therapeutics, Inc.", target_weight: 3.333, b2_score: 0.898, quality_percentile: 0.324, quality_components_ok: 2, sector: "Healthcare", industry: "Biotechnology", inclusion_reason: "Marginal Quality, adequate Price" },
  { rank: 29, ticker: "COCO", company_name: "The Vita Coco Company, Inc.", target_weight: 3.333, b2_score: 0.891, quality_percentile: 0.816, quality_components_ok: 4, sector: "Consumer Defensive", industry: "Beverages - Non-Alcoholic", inclusion_reason: "Excellent Quality" },
  { rank: 30, ticker: "KALU", company_name: "Kaiser Aluminum Corporation", target_weight: 3.333, b2_score: 0.887, quality_percentile: 0.413, quality_components_ok: 4, sector: "Basic Materials", industry: "Aluminum", inclusion_reason: "Adequate Quality, moderate Price" },
];

export default function ModelPage() {
  const [holdings] = useState<Holding[]>(MOCK_HOLDINGS);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Official Model</h1>
        <p className="text-sm text-neutral-500 mt-1">M1 B2 Quality Veto N30 — {holdings.length} holdings at equal weight</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="metric-label">Model</p>
          <p className="text-sm font-semibold mt-1">M1 B2 Quality Veto</p>
        </div>
        <div className="card">
          <p className="metric-label">Effective Date</p>
          <p className="text-sm font-semibold mt-1">2026-06-23</p>
        </div>
        <div className="card">
          <p className="metric-label">Holdings</p>
          <p className="text-sm font-semibold mt-1">{holdings.length} equal weight</p>
        </div>
        <div className="card">
          <p className="metric-label">Status</p>
          <p className="text-sm font-semibold mt-1 text-green-400">Published</p>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="table-header">#</th>
                <th className="table-header">Ticker</th>
                <th className="table-header text-right">Weight</th>
                <th className="table-header text-right">B2 Score</th>
                <th className="table-header text-right">Q %ile</th>
                <th className="table-header">Sector</th>
                <th className="table-header">Industry</th>
                <th className="table-header">Reason</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h) => (
                <tr key={h.ticker} className="border-b border-neutral-800/50 hover:bg-neutral-900/50 transition-colors">
                  <td className="table-cell text-neutral-500">{h.rank}</td>
                  <td className="table-cell-text font-semibold">{h.ticker}</td>
                  <td className="table-cell text-right">{h.target_weight.toFixed(1)}%</td>
                  <td className="table-cell text-right">{h.b2_score.toFixed(3)}</td>
                  <td className="table-cell text-right">{h.quality_percentile.toFixed(3)}</td>
                  <td className="table-cell-text text-sm">{h.sector}</td>
                  <td className="table-cell-text text-sm text-neutral-400">{h.industry}</td>
                  <td className="table-cell-text text-sm text-neutral-400 max-w-xs truncate">{h.inclusion_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
