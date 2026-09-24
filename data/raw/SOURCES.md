# Data Sources & Citation Log

All figures in this project are sourced from public, primary disclosures. No synthetic or fabricated data is used anywhere in the Fielmann or industry-benchmark datasets.

## Fielmann Group AG (real company data)

Primary source: Fielmann Group AG investor relations publications.
Index page: https://www.fielmann-group.com/en/investor-relations/presentations-and-publications/

| Period | Document | URL |
|---|---|---|
| FY2021-FY2025 key figures, Plan vs Actual 2025, Segment reporting 2025 | Annual Report 2025 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Geschaeftsberichte/EN/Fielmann_Annual_Report_2025.pdf |
| Q1 2023 | Quarterly Report Q1-2023 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2023/Fielmann_Quarterly_Report_Q1-2023.pdf |
| H1 2023 | Half-Year Report 2023 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2023/Fielmann_report_half_year_2023.pdf |
| 9M 2023 | Quarterly Report Q3-2023 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2023/Fielmann_Quarterly_Report_Q3-2023.pdf |
| Q1 2024 | Interim Statement Q1-2024 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2024/Fielmann_Interim_Statement_Q1-2024.pdf |
| H1 2024 | Half-Year Report 2024 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2024/Fielmann_report_half_year_2024.pdf |
| 9M 2024 | Interim Statement Q3-2024 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2024/Fielmann_Interim_Statement_Q3-2024.pdf |
| Q1 2025 | Interim Statement Q1-2025 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2025/Fielmann_Interim_Statement_Q1-2025.pdf |
| H1 2025 | Half-Year Report 2025 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2025/Fielmann_report_half_year_2025.pdf |
| 9M 2025 | Interim Statement Q3-2025 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2025/Fielmann_Interim_Statement_Q3-2025.pdf |
| Q1 2026 | Interim Statement Q1-2026 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2026/Fielmann_Interim_Statement_Q1-2026.pdf |
| H1 2026 | Half-Year Report 2026 | https://www.fielmann-group.com/fileadmin/fielmann/Dokumente/Publikationen/Quartalsberichte/EN/2026/Fielmann_Group_AG_report_half_year_2026.pdf |

## German optical retail industry benchmark (ZVA)

Zentralverband der Augenoptiker und Optometristen (ZVA) — the German optical/optometry trade association's annual industry report.

- ZVA-Branchenbericht 2024 ("Augenoptik in Zahlen"): https://www.zva.de/wp-content/uploads/ZVA-Branchenbericht-2024-Download-1.pdf
- ZVA-Branchenbericht 2025/2026: https://www.zva.de/news/zva-branchenbericht-2025-2/
- ZVA branch report index: https://www.zva.de/zva-ubersicht-intern/branchenbericht/

## Verification / reconciliation performed

1. Segment external sales for 2025 sum exactly to Group total consolidated sales (1,482.5 + 241.9 + 106.5 + 211.7 + 276.5 + 116.2 = 2,435.3), confirming the segment table extraction is internally consistent.
2. Derived quarterly figures for 2023 and 2024 sum exactly back to the audited annual totals reported in the Annual Report 2025 (2023: 483.722+496.592+520.997+469.589 = 1,970.9; 2024: 536.667+554.181+601.152+574.900 = 2,266.9), confirming the cumulative-minus-cumulative derivation is arithmetically sound.
3. One known data-quality caveat is logged directly in fielmann_quarterly_2023_2026.csv: the 9M/2024 total consolidated sales figure is stated as EUR 1,692m in the Q3-2024 interim statement itself, but referenced as EUR 1,689m (a ~0.2% difference, likely rounding or minor restatement) in the Q3-2025 interim statement's year-over-year comparison. The contemporaneous report's own figure (1,692) was used as primary.
4. Two extraction tools were cross-checked where possible: figures were pulled directly from each PDF's own key-figures/P&L tables rather than relying solely on third-party summaries (e.g. stockanalysis.com), which were used only as an initial sanity check, not as a data source.

## Note on precision

2023 and 2024 quarterly figures were sourced from precise P&L tables (stated in EUR '000s). 2025 and 2026 quarterly figures were sourced from narrative text in the interim statements, which round to the nearest EUR million. This precision difference is preserved in the `precision_note` column of the quarterly CSV rather than papered over.
