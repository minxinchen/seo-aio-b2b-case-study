> 2026-09-16 狀態更新：單產品實驗已於 8/21 發布，成效待驗證；最新 [實驗紀錄](../experiments/single-product-aio.md) 與 [結果](results.md) 優先於下方歷史方法敘述。

# 方法補充：AI Agent 如何參與專案

AI Agent 在這個專案裡是一種工作方法，不是研究目標本身。

我的目標是把 SEO 與 AIO 做起來，而 Agent 主要負責大量掃描、比較、產生程式與驗證；人負責定義問題、判斷資料真實性、決定是否採用建議，以及是否允許正式上線。

## 工作分工

### 人負責

- 決定網站目前最值得解的問題
- 決定產品資料哪一份具有最高權威
- 判斷 Agent 的結論是否合理
- 決定要直接修改、先做實驗，還是暫時不做
- 決定是否允許正式上線
- 發現新的證據後，決定是否推翻舊結論

### AI Agent 負責

- 掃描大量頁面與檔案
- 比對繁中、簡中、英文內容
- 產生候選 HTML、JSON-LD、文案與 script
- 建立驗證程式
- 整理修改前 / 修改後證據
- 整理修改紀錄、問題檢討與目前專案狀態
- 從大量歷史紀錄中找出與當前問題最相關的 log

### Deterministic tools 負責

- HTTP status
- canonical
- hreflang
- H1 / metadata
- schema parse
- sitemap
- 站內連結
- 圖片狀態
- viewport / overflow
- known-value consistency
- Lighthouse / performance comparison

這些機械式檢查不需要每次都讓 LLM 重新推理，因此盡量交給 script 固定執行。

---

## 實際工作流程

```text
發現問題
  ↓
確認基準狀態與資料來源
  ↓
Agent 協助掃描 / 比較 / 提出修改方案
  ↓
人判斷是否採用
  ↓
先保存修改前證據
  ↓
修改或建立隔離實驗
  ↓
清除 cache
  ↓
匿名公開驗證
  ↓
執行 deterministic checks
  ↓
保存修改後證據
  ↓
PASS → 正式上線 / 更新 project state
FAIL → 修正 / rollback / 問題檢討
```

這套流程不是一開始就設計完成，而是在實際犯錯後慢慢長出來。

---

## 為什麼不能讓 Agent 自己判斷「完成」

專案裡真的發生過幾種錯誤：

1. 繁中完成後，Agent 把局部成功外推成三語完成。
2. 產品正文更新後，較舊的 FAQ / JSON-LD 還留著舊規格。
3. WordPress 登入狀態已看到新版，但匿名訪客仍拿到 Breeze cache 舊版。
4. 某次上線驗收已經標成 PASS，後續更完整的檢查卻找到漏同步問題。

因此「完成」不能只靠 Agent 的自然語言總結，而要看公開結果與驗證條件。

---

## Log 怎麼變成可用的專案記憶

原專案累積了大量 Lighthouse runs、HTML、screenshots、JSON、stderr 與修改前後快照。這些原始資料都重要，但不代表 Agent 每次都要全部載入。

我後來把它們分成三層：

```text
原始證據
Lighthouse / HTML / screenshot / JSON / stderr
        ↓
代表性 Log
哪一份紀錄真正改變了問題判斷？
        ↓
決策規則
因此改了什麼實作、驗收或上線決策？
```

例如首頁效能：

```text
觀察
Mobile LCP 約 13 秒

可能原因
主機 / image / slider / JavaScript / CSS / cache

關鍵實驗
只替換第一屏 Smart Slider 3
13.10s → 3.16s

判斷
主機不是主要瓶頸
第一屏載入結構才是高影響變因

決策
移除重型 slider，重做 lightweight hero

正式上線
2.72s
```

真正值得之後的 Agent 優先讀取的，不是幾十份 Lighthouse 原始輸出，而是這份**改變了因果判斷與實作方向的隔離測試紀錄**。

---

## Agent 載入歷史資料的順序

```text
目前問題
  ↓
Project State
  ↓
問題類別
  ↓
Evidence Map
  ↓
代表性 Log
  ↓
必要時才往下讀原始證據
```

這樣做是為了避免兩件事：

- 一次把所有歷史檔案塞進 context，造成 token 浪費與資訊混淆。
- 幾週後只靠對話記憶，把「曾經測試」誤記成「已經正式上線」。

→ [Log 的整理方式](../logs/README.md)

---

## 人與 Agent 不一定同意

AIO / Structured Data 階段就出現過真正的意見差異。

Agent 當時優先守住正式環境 Rich Results 的正確性，不願意為了增加欄位去補不存在的 Offer、price、review、rating，這個判斷對正式環境安全是合理的。

但我另外提出一個可小範圍執行的問題：

> 能不能只選一個產品作為實驗組，在不虛構商業資料的前提下，強化頁面可見 FAQ 與 HTML 語意結構，其他產品保持不變，再觀察後續 GSC 與 AI / search visibility？

這個實驗已於 2026-08-21 發布，技術 gate 通過；**搜尋與 AI 引用效果仍未驗證**。詳見 [實驗現況](../experiments/single-product-aio.md)。

它保留下來的原因是：正式環境的目標是降低已知錯誤，實驗的目標則是取得新的資訊。兩者不一定會得到相同決策。
