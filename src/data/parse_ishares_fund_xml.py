#!/usr/bin/env python3
"""Extract a flat, auditable holdings table from iShares SpreadsheetML.

The upstream file is retained unchanged. Some current iShares SpreadsheetML
documents contain unescaped URL ampersands, so lxml recovery mode is used and
the extracted header/row contract is validated explicitly.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from lxml import etree


SS = "urn:schemas-microsoft-com:office:spreadsheet"
EXPECTED_HEADER = [
    "Ticker",
    "Name",
    "Sector",
    "Asset Class",
    "Market Value",
    "Weight (%)",
    "Notional Value",
    "Quantity",
    "Price",
    "Location",
    "Exchange",
    "Currency",
    "FX Rate",
    "Accrual Date",
]
TICKER_MAP = {"BRKB": "BRK-B", "BFB": "BF-B"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cell_values(row: etree._Element) -> list[str]:
    return ["".join(cell.itertext()).strip() for cell in row.findall(f"{{{SS}}}Cell")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    xml_parser = etree.XMLParser(recover=True, no_network=True)
    tree = etree.parse(str(args.input), xml_parser)
    worksheets = tree.findall(f".//{{{SS}}}Worksheet")
    holdings = next(
        sheet
        for sheet in worksheets
        if sheet.attrib.get(f"{{{SS}}}Name") == "Holdings"
    )
    rows = holdings.findall(f".//{{{SS}}}Row")
    values = [cell_values(row) for row in rows]
    header_index = next(i for i, row in enumerate(values) if row[: len(EXPECTED_HEADER)] == EXPECTED_HEADER)
    as_of = next(row[1] for row in values if row and row[0] == "Fund Holdings as of")

    extracted: list[dict[str, str]] = []
    for row in values[header_index + 1 :]:
        if len(row) < len(EXPECTED_HEADER):
            continue
        record = dict(zip(EXPECTED_HEADER, row[: len(EXPECTED_HEADER)]))
        if record["Asset Class"] != "Equity":
            continue
        if record["Location"] != "United States" or record["Currency"] != "USD":
            continue
        record["YFinance Ticker"] = TICKER_MAP.get(record["Ticker"], record["Ticker"])
        record["Issuer Key"] = (
            "ALPHABET"
            if record["Ticker"] in {"GOOG", "GOOGL"}
            else record["Name"].replace(" CLASS A", "").replace(" CLASS B", "").replace(" CLASS C", "")
        )
        extracted.append(record)

    if len(extracted) < 90:
        raise ValueError(f"Unexpectedly small equity universe: {len(extracted)}")

    fieldnames = EXPECTED_HEADER + ["YFinance Ticker", "Issuer Key"]
    csv_path = args.output_dir / "oef_equities.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(extracted)

    preferred_by_issuer: dict[str, dict[str, str]] = {}
    for record in extracted:
        key = record["Issuer Key"]
        if key not in preferred_by_issuer or float(record["Weight (%)"]) > float(preferred_by_issuer[key]["Weight (%)"]):
            preferred_by_issuer[key] = record
    deduplicated = sorted(preferred_by_issuer.values(), key=lambda row: (-float(row["Weight (%)"]), row["YFinance Ticker"]))

    ticker_path = args.output_dir / "yfinance_tickers.txt"
    ticker_path.write_text("\n".join(row["YFinance Ticker"] for row in deduplicated) + "\n", encoding="utf-8")

    manifest = {
        "source": "iShares S&P 100 ETF (OEF) official fund-data workbook",
        "source_url": "https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US&portfolioId=239723&component=fundDownload&userType=individual",
        "raw_path": str(args.input),
        "raw_sha256": sha256(args.input),
        "holdings_as_of": as_of,
        "equity_rows": len(extracted),
        "deduplicated_issuers": len(deduplicated),
        "duplicate_issuer_tickers_removed": sorted(set(row["YFinance Ticker"] for row in extracted) - set(row["YFinance Ticker"] for row in deduplicated)),
        "output_csv": str(csv_path),
        "output_csv_sha256": sha256(csv_path),
        "ticker_file": str(ticker_path),
        "ticker_file_sha256": sha256(ticker_path),
        "limitations": [
            "Current holdings snapshot, not historical index membership.",
            "Projecting this universe backward creates survivorship and membership bias.",
            "One share class per issuer is retained using current OEF weight.",
        ],
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "equities": len(extracted), "issuers": len(deduplicated), "manifest": str(manifest_path)}))


if __name__ == "__main__":
    main()
