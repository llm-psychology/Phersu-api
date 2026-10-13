# Phersu-api

Phersu-api 是 PersonaDough 與 PsychAnchor 的 HTTP/SSE 整合入口。

## 職責

- FastAPI 請求/回應、人格與記憶管理 API。
- 背景任務與模擬事件 SSE。
- 網頁展示與可選的 Unity WebGL 靜態資產。
- `simulation/` 暫存原本的生活、位置與火災環境 adapter；人格生成呼叫 PersonaDough，訪談、對話及人格決策呼叫 PsychAnchor。

目前是第一次 repository 拆分，保留既有路由。`app.py` 仍有待拆成 routers/services；全域狀態、JSON 檔案儲存、授權與多 worker 管理都尚未完成企業平台重構。

## 執行

需要 Python 3.10+，三個 repo 放在相鄰目錄。此版對應 PersonaDough 的 `refactor/repository-split` 與 PsychAnchor 的 `refactor/extract-anchoring` 分支；取得方法見 [Phersu 主導覽](https://github.com/llm-psychology/Phersu)。

GitHub repo 名稱為 `Phersu-api`；本地資料夾沿用 `persona-api`，Python 發行套件名稱仍為 `persona-api`，import 名稱為 `persona_api`。repo 更名不影響以下執行方式。

```powershell
python -m pip install -e ../PersonaDough -e ../PsychAnchor -e .
Copy-Item .env.example .env
python -m uvicorn persona_api.app:app --host 127.0.0.1 --port 20000
```

- API 文件：`http://127.0.0.1:20000/docs`
- 啟動健康檢查：`http://127.0.0.1:20000/health`（只驗證 HTTP 程序存活，沒有驗證外部模型服務）。
- 主頁：`http://127.0.0.1:20000/`
- 火災展示：`http://127.0.0.1:20000/fire_simulation_sse`

設定 `PERSONA_DATA_DIR` 與 PsychAnchor 相同的絕對路徑。參照 `.env.example` 設定聊天後端及記憶資料路徑。Uvicorn 可用 `--env-file .env` 指定設定檔。

`POST /generate?count=1` 只生成並儲存人格，不自動建立訪談索引；訪談由獨立的 `POST /generate-rag/{persona_id}` 啟動。

Unity 資產不在原公開 repo。可透過 `UNITY_BUILD_DIR` 指向本機建置資料夾；缺少它時 API 仍可啟動，Unity 頁面無法使用。

## 驗證與限制

```powershell
python -m pip install -e '../PersonaDough[dev]' -e '../PsychAnchor[dev]' -e '.[dev]'
python -m pytest tests
```

本專案採用 GPL-3.0 授權，詳見 [LICENSE](LICENSE)。
