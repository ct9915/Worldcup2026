# 2026 FIFA 世界盃小組積分榜

即時追蹤 2026 FIFA World Cup 12 個小組的積分、進失球、晉級狀態，每小時自動從官方數據源更新。

## 功能

- 12 個小組的完整積分表（場次、勝平負、進失球、積分）
- 晉級狀態標示：直接晉級（綠）、爭外卡第3名（金）、出局（灰）
- 同分時自動產生平手說明（淨球差 → 進球數 → FIFA排名）
- 小組篩選快速切換
- 每小時透過 GitHub Actions 自動抓取最新數據並更新頁面
- 支援手機瀏覽

## 程式架構

```
Worldcup2026/
├── index.html                        # 前端頁面，動態載入 data.json 渲染積分表
├── data.json                         # 最新積分數據，由 CI 自動更新
├── scripts/
│   └── fetch_standings.py            # 從 api.football-data.org 抓取數據並產生 data.json
└── .github/
    └── workflows/
        └── update-standings.yml      # 每小時執行 fetch script，有變動就 commit
```

### 數據流

```
api.football-data.org
        ↓  (每小時，GitHub Actions cron)
fetch_standings.py
        ↓  (commit data.json)
GitHub repo → GitHub Pages
        ↓  (瀏覽器 fetch data.json)
index.html 渲染積分表
```

### 主要檔案說明

**`fetch_standings.py`**
- 呼叫 `/v4/competitions/WC/standings` 取得積分表
- 呼叫 `/v4/competitions/WC/matches` 取得比賽結果
- 將 API 回傳的英文隊名對應為中文名稱與旗幟 emoji
- 計算已賽場數、生成平手說明文字
- 輸出 `data.json`

**`update-standings.yml`**
- cron: `5 * * * *`（每小時第5分鐘）
- 執行 fetch script 後，若 `data.json` 有變動則自動 commit & push
- 亦可在 GitHub Actions 頁面手動觸發

**`index.html`**
- 頁面載入時 `fetch('data.json')` 取得數據
- 依 API 回傳的排名順序渲染各小組（不在前端重新排序）
- 頁面標題的輪次（第1/2/3輪）與資料時間戳從 `data.json` 動態填入

## 設定方式

1. 至 [api.football-data.org](https://www.api-football-data.org/register) 免費申請 API Token
2. 在 GitHub repo 的 **Settings → Secrets and variables → Actions** 新增：
   ```
   Name:  FOOTBALL_API_KEY
   Value: <your token>
   ```
3. 至 **Actions → Update Standings → Run workflow** 手動執行一次確認
