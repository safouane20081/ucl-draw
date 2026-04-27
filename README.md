# ucl-draw
# 🏆 UCL 2024/25 League Phase Draw Simulator

A Python simulator that replicates the **official UEFA Champions League draw rules** for the 2024/25 league phase format.

---

## 📋 Overview

This tool simulates the UCL league phase draw for 36 teams across 4 pots, following all official UEFA constraints. It uses a backtracking + retry algorithm to guarantee a valid draw every time.

---

## ⚙️ Official Rules Enforced

| Rule | Detail |
|------|--------|
| 36 teams | 4 pots of 9 teams each |
| 8 opponents per team | Exactly 2 from **each** pot (including own pot) |
| Home/Away balance | Exactly 4 home and 4 away games |
| No same-country clashes | Teams from the same country never meet |
| Country cap | Max 2 opponents from any single country |

---

## 🚀 Getting Started

### Requirements

```bash
pip install pandas
```

### Run with default sample data

```bash
python ucl_draw.py
```
> Automatically generates `ucl_teams.csv` if no file is found.

### Run with your own CSV

```bash
python ucl_draw.py your_file.csv
```

---

## 📁 CSV Format

Your CSV file must have these 3 columns:

```csv
team,country,pot
Real Madrid,Spain,1
Manchester City,England,1
Bayern Munich,Germany,1
...
```

---

## 📊 Sample Output
