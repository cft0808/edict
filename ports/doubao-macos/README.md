# 三省六部 · Mac OS 豆包工作版本（doubao-macos 移植）

> **版本名稱：Mac OS 豆包工作三省六部版本**
> 上游：[cft0808/edict](https://github.com/cft0808/edict)（OpenClaw 三省六部制）
> 執行環境：macOS 桌面版豆包工作（Doubao Work）主代理 + 子代理

## 一、定位

本目錄是 edict 在 **Mac OS 豆包工作環境**的輕量移植：不常駐 Agent 進程、不需自行管理模型 API Key，由主代理（太子）依固定流程派發子代理，跑完即收；全程把旨意與軌跡寫入本機 `state.json`，由單檔 HTML 看板（軍機處）顯示。

## 二、與 OpenClaw 原版差異

| 項目 | 真 edict（OpenClaw 原版） | 本移植版（Mac OS 豆包工作） |
|---|---|---|
| 運行 | 12 個常駐 Agent 進程＋Gateway | 主代理按流程派子代理，跑完即收 |
| 模型 | 每官可各配模型與 API Key | 共用豆包模型，免 API Key |
| 看板 | React 軍機處看板 | 單檔 HTML 看板，`state.json` 驅動、10 秒輪詢 |
| 狀態 CLI | `edict.sh` + Gateway | 純 Python 標準庫 CLI `edict.py`（new / set / list） |
| 分級 | 常駐流程統一調度 | L0 純查詢、L1 簡案、L2 完整鏈路；L1 三駁自動升 L2 |
| 適合 | 長期常駐、多模型分流 | 單次任務也要制度與審計 |

## 三、檔案清單

- `SKILL.md`：制度說明（十二官職責、呼叫權限矩陣、三級通道、等待視窗硬約束）
- `edict.py`：旨意立案／更新／列表 CLI（僅 Python 標準庫，無外部依賴）
- `index.html`：軍機處看板（讀取同目錄 `state.json`）
- `start.sh`：本機啟動 `http.server`（預設 `127.0.0.1:7891`）
- `state.example.json`：狀態檔範本；首次使用複製為 `state.json`

## 四、快速開始

```bash
cp state.example.json state.json
bash start.sh
# 瀏覽器開啟 http://127.0.0.1:7891
```

CLI 操作：

```bash
python3 edict.py new "旨意標題"          # 立案，取得 E-00x
python3 edict.py set E-001 --stage 門下省 --dept 門下省 --status 審核中 --note "..."
python3 edict.py list
```

## 五、環境專屬部署細節

`SKILL.md` 第五節記錄的 LaunchAgent 開機常駐、Safari 書籤、`/etc/hosts` 別名、`state.json` symlink 等，是 macOS 豆包工作三機部署的本機設定；其他環境可略過，制度流程與檔案結構不受影響。

## 六、相對上游的改動摘要

1. **流程移植**：太子分揀 → 中書起草 → 門下審核（可否決退回）→ 尚書派發 → 六部並行執行 → 門下複審 → 歸檔。
2. **三級通道**：
   - L0 純查詢：太子立案後直答，不派衙門；
   - L1 帶建議：太子 → 中書（簡案）→ 門下輕審（目標對齊、事實無誤、無越權承諾）→ 太子交付，不派六部；
   - L2 涉金額／對外承諾／不可逆操作：強制完整鏈路；L1 經門下第 3 次退回後自動升 L2。
3. **權限矩陣**：不得跳級、不得逆向亂派；六部僅回報尚書省；太子為唯一對外出口。
4. **審計軌跡**：每道旨意含 `id / title / stage / status / created / updated / depts / log`，全程寫入 `state.json`。
5. **看板**：七衙門欄 + 資料中出現的動態額外階段欄；卡片狀態標籤（完成／失敗）；點擊卡片看歷程，Escape 關閉細節；每 10 秒自動刷新。
6. **CLI 強化**：`new`／`set` 皆寫 `updated` 時間戳，供跨機同步判斷狀態主體新舊。
