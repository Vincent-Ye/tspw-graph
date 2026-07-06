# 《笑傲江湖》知识图谱教学演示 Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个本地可运行的《笑傲江湖》知识图谱教学演示，包含本体导览、Neo4j 图查询、证据定位、图谱可视化和受控问答样例。

**Architecture:** React/TypeScript 单页前端调用 FastAPI；FastAPI 通过 repository 边界访问 Neo4j，并使用 SQLite 管理项目元数据。Phase 1 只导入人工校验的核心种子数据，不实现通用上传和模型抽取；这些能力由后续独立计划接入既有接口。

**Tech Stack:** Python 3.12、FastAPI、Pydantic 2、SQLAlchemy 2、Neo4j Python Driver、pytest、React 19、TypeScript、Vite、TanStack Query、Cytoscape.js、Vitest、Playwright、Docker Compose。

## Global Constraints

- 前端只调用后端 API，不直接访问 Neo4j 或模型服务。
- 不同小说必须使用 `project_id` 隔离；所有图查询必须带项目范围。
- 所有 Cypher 必须参数化并限制查询深度、返回节点数和执行时间。
- 确认事实至少关联一个可定位原文证据。
- 图查询无结果时明确返回“图谱中暂无足够事实”，不得补写无依据答案。
- 模型密钥不得写入日志、SQLite、Neo4j 或前端状态。
- Phase 1 不包含上传、异步抽取、账户、协作审核和生产集群部署。

## File Map

- `compose.yaml`：本地 Neo4j 服务。
- `Makefile`：安装、启动、测试和导入命令。
- `apps/api/pyproject.toml`：后端依赖与 pytest 配置。
- `apps/api/src/app/main.py`：FastAPI 组装与路由注册。
- `apps/api/src/app/settings.py`：环境配置。
- `apps/api/src/app/ontology/`：本体枚举、约束和只读 API。
- `apps/api/src/app/projects/`：SQLite 项目元数据。
- `apps/api/src/app/graph/`：Neo4j repository、查询服务和 API。
- `apps/api/src/app/qa/`：受控问题模板与解释性响应。
- `apps/api/tests/`：单元和集成测试。
- `apps/web/`：React 应用。
- `apps/web/src/features/guide/`：教学导览。
- `apps/web/src/features/ontology/`：TBox/ABox 对照页。
- `apps/web/src/features/graph/`：搜索、画布、实体详情与证据。
- `apps/web/src/features/ask/`：样例问答与技术展开。
- `data/xiaoao/core-graph.json`：人工校验的核心示范图谱。
- `scripts/import_core_graph.py`：幂等种子数据导入入口。
- `tests/e2e/`：跨前后端 Playwright 验收。

---

### Task 1: 可运行的全栈骨架

**Files:**
- Create: `compose.yaml`
- Create: `Makefile`
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/src/app/main.py`
- Create: `apps/api/src/app/settings.py`
- Create: `apps/api/tests/test_health.py`
- Create: `apps/web/package.json`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/App.test.tsx`

**Interfaces:**
- Produces: `GET /api/health -> {"status":"ok"}`；前端根组件 `App()`；Neo4j 地址由 `NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD` 配置。

- [x] **Step 1: 写后端失败测试**

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health() -> None:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [x] **Step 2: 运行测试并确认因 `app.main` 不存在而失败**

Run: `cd apps/api && python -m pytest tests/test_health.py -v`

Expected: `ModuleNotFoundError: No module named 'app'`

- [x] **Step 3: 创建最小 FastAPI 应用和配置**

```python
# apps/api/src/app/main.py
from fastapi import FastAPI

app = FastAPI(title="江湖图谱 API")

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# apps/api/src/app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "development-only"
    sqlite_url: str = "sqlite:///./tspw-graph.db"
```

- [x] **Step 4: 创建 React 冒烟测试与最小应用**

```tsx
// apps/web/src/App.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { App } from './App'

describe('App', () => {
  it('shows the product name', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: '江湖图谱' })).toBeInTheDocument()
  })
})
```

```tsx
// apps/web/src/App.tsx
export function App() {
  return <main><h1>江湖图谱</h1><p>从《笑傲江湖》理解本体与知识图谱</p></main>
}
```

- [x] **Step 5: 配置 Neo4j Compose 和统一命令**

`compose.yaml` 只暴露 `7474` 与 `7687`，使用命名卷；`Makefile` 提供 `install`、`dev`、`test`、`neo4j-up`、`neo4j-down`。依赖安装分别执行 `python -m pip install -e 'apps/api[dev]'` 与 `npm --prefix apps/web install`。

- [x] **Step 6: 运行全栈冒烟测试**

Run: `make test`

Expected: 后端 `1 passed`，前端 `1 passed`。

- [x] **Step 7: 提交**

```bash
git add compose.yaml Makefile apps/api apps/web
git commit -m "build: scaffold knowledge graph demo"
```

### Task 2: 本体契约与教学 API

**Files:**
- Create: `apps/api/src/app/ontology/models.py`
- Create: `apps/api/src/app/ontology/catalog.py`
- Create: `apps/api/src/app/ontology/router.py`
- Create: `apps/api/tests/ontology/test_catalog.py`
- Modify: `apps/api/src/app/main.py`

**Interfaces:**
- Produces: `EntityType`、`RelationType`、`OntologyCatalog`；`GET /api/ontology -> OntologyCatalog`。

- [x] **Step 1: 写失败测试，锁定类、关系和教学示例**

```python
def test_catalog_contains_tbox_and_abox_example(client) -> None:
    body = client.get("/api/ontology").json()
    assert {item["id"] for item in body["entity_types"]} >= {"Person", "Organization", "MartialArt", "Event", "Place", "Artifact"}
    knows = next(item for item in body["relation_types"] if item["id"] == "KNOWS")
    assert knows["source_types"] == ["Person"]
    assert knows["target_types"] == ["MartialArt"]
    assert body["example"] == {"subject": "令狐冲", "predicate": "KNOWS", "object": "独孤九剑"}
```

- [x] **Step 2: 运行并确认 `/api/ontology` 返回 404**

Run: `cd apps/api && python -m pytest tests/ontology/test_catalog.py -v`

Expected: FAIL，状态码为 `404`。

- [x] **Step 3: 实现不可变本体模型和目录**

使用 Pydantic frozen models。实体类型包含中英文标签、说明、颜色和父类型；关系类型包含中英文标签、起点类型、终点类型、是否对称、是否时态化。`TeachingEvent` 作为 `Event` 子类，使用 `TEACHER`、`STUDENT`、`SUBJECT` 表达传授三元事实。

- [x] **Step 4: 注册只读路由并验证**

Run: `cd apps/api && python -m pytest tests/ontology/test_catalog.py -v`

Expected: `1 passed`。

- [x] **Step 5: 提交**

```bash
git add apps/api/src/app/ontology apps/api/src/app/main.py apps/api/tests/ontology
git commit -m "feat: define xiaoao ontology catalog"
```

### Task 3: 项目元数据与核心图谱幂等导入

**Files:**
- Create: `apps/api/src/app/projects/models.py`
- Create: `apps/api/src/app/projects/repository.py`
- Create: `apps/api/src/app/graph/importer.py`
- Create: `apps/api/src/app/graph/neo4j.py`
- Create: `apps/api/tests/graph/test_importer.py`
- Create: `data/xiaoao/core-graph.json`
- Create: `scripts/import_core_graph.py`

**Interfaces:**
- Produces: `ProjectRepository.ensure_builtin_project() -> Project`；`GraphImporter.import_document(document: GraphDocument) -> ImportSummary`。
- Consumes: Task 2 的 `EntityType` 与 `RelationType` 字符串值。

- [x] **Step 1: 写幂等导入失败测试**

```python
def test_importing_same_document_twice_is_idempotent(fake_graph) -> None:
    importer = GraphImporter(fake_graph)
    first = importer.import_document(sample_document())
    second = importer.import_document(sample_document())
    assert first.created_entities == 3
    assert second.created_entities == 0
    assert fake_graph.count("Entity") == 3
    assert fake_graph.count("Fact") == 2
    assert fake_graph.count("Evidence") == 2
```

- [x] **Step 2: 运行并确认 `GraphImporter` 不存在**

Run: `cd apps/api && python -m pytest tests/graph/test_importer.py -v`

Expected: import error。

- [x] **Step 3: 定义种子数据契约**

`core-graph.json` 顶层固定为 `project`、`chapters`、`entities`、`facts`、`evidence`。所有实体 ID 使用 `xiaoao:<type>:<slug>`；所有事实 ID 使用主体、关系、客体或事件的稳定哈希；证据必须含 `chapter_id`、`start_offset`、`end_offset`、`quote` 和 `text_hash`。

- [x] **Step 4: 实现 SQLite 项目仓储和 Neo4j 幂等导入**

使用唯一约束 `(project_id, entity_id)`、`(project_id, fact_id)`、`(project_id, evidence_id)`；写入顺序为项目与章节、实体、事实、证据、证据关联。每批事务最多 500 条记录。

- [x] **Step 5: 写入首批人工校验数据**

至少覆盖令狐冲、任盈盈、岳不群、风清扬、东方不败、华山派、日月神教、独孤九剑、吸星大法、葵花宝典及其关键关系；每条事实必须从 `笑傲江湖/笑傲江湖.txt` 取得可定位短证据。导入脚本在校验失败时返回非零退出码并打印事实 ID。

- [x] **Step 6: 启动 Neo4j，连续导入两次并验证计数不增加**

Run: `make neo4j-up && python scripts/import_core_graph.py && python scripts/import_core_graph.py`

Expected: 第二次输出 `created_entities=0 created_facts=0 created_evidence=0`。

- [x] **Step 7: 提交**

```bash
git add apps/api/src/app/projects apps/api/src/app/graph data/xiaoao scripts/import_core_graph.py apps/api/tests/graph
git commit -m "feat: import curated xiaoao graph"
```

### Task 4: 受限图查询与证据 API

**Files:**
- Create: `apps/api/src/app/graph/models.py`
- Create: `apps/api/src/app/graph/repository.py`
- Create: `apps/api/src/app/graph/service.py`
- Create: `apps/api/src/app/graph/router.py`
- Create: `apps/api/tests/graph/test_service.py`
- Create: `apps/api/tests/graph/test_router.py`
- Modify: `apps/api/src/app/main.py`

**Interfaces:**
- Produces: `search(project_id, query, types, limit)`；`neighborhood(project_id, entity_id, depth, limit, from_chapter, to_chapter)`；`shortest_path(project_id, source_id, target_id, max_depth)`；`entity_detail(project_id, entity_id)`；`timeline(project_id, person_id, from_chapter, to_chapter, limit)`。

- [x] **Step 1: 写项目隔离和边界失败测试**

```python
def test_neighborhood_rejects_unbounded_depth(client) -> None:
    response = client.get("/api/graph/neighborhood", params={"project_id": "xiaoao", "entity_id": "x", "depth": 4})
    assert response.status_code == 422

def test_search_never_returns_other_project(graph_service) -> None:
    rows = graph_service.search("xiaoao", "令狐", [], 20)
    assert rows and all(row.project_id == "xiaoao" for row in rows)
```

- [x] **Step 2: 运行并确认路由和服务不存在**

Run: `cd apps/api && python -m pytest tests/graph/test_service.py tests/graph/test_router.py -v`

Expected: collection error 或 404。

- [x] **Step 3: 实现参数化 repository**

搜索上限 50；邻居深度只允许 1 或 2、节点上限 100；最短路径最大深度 6；时间线最多返回 100 个事件。邻居与时间线接受可选章节区间，并按关系的 `from_chapter`、`to_chapter` 判断有效性。所有 Cypher 首个匹配条件包含 `project_id: $project_id`，关系两端再次校验项目一致。实体详情返回属性、按类型分组的关系和按章节排序的证据。

- [x] **Step 4: 实现 API 错误语义**

不存在实体返回 `404 ENTITY_NOT_FOUND`；超出边界由 Pydantic 返回 422；Neo4j 暂时不可用返回 `503 GRAPH_UNAVAILABLE`；响应不得包含驱动异常和连接凭据。

- [x] **Step 5: 运行测试**

Run: `cd apps/api && python -m pytest tests/graph -v`

Expected: 全部 PASS。

- [x] **Step 6: 提交**

```bash
git add apps/api/src/app/graph apps/api/src/app/main.py apps/api/tests/graph
git commit -m "feat: add bounded graph query APIs"
```

### Task 5: 受控模板问答

**Files:**
- Create: `apps/api/src/app/qa/models.py`
- Create: `apps/api/src/app/qa/templates.py`
- Create: `apps/api/src/app/qa/service.py`
- Create: `apps/api/src/app/qa/router.py`
- Create: `apps/api/tests/qa/test_service.py`
- Modify: `apps/api/src/app/main.py`

**Interfaces:**
- Produces: `POST /api/ask`，请求 `{project_id, question}`，响应 `{answer, path, query_explanation, cypher_template, parameters, evidence}`。
- Consumes: Task 4 的图查询 repository；不接受客户端 Cypher。

- [x] **Step 1: 写有结果与无结果测试**

```python
def test_answer_includes_path_and_evidence(qa_service) -> None:
    answer = qa_service.ask("xiaoao", "令狐冲的师父是谁？")
    assert "岳不群" in answer.answer
    assert answer.path
    assert answer.evidence[0].chapter_id
    assert "$project_id" in answer.cypher_template

def test_no_result_does_not_invent(qa_service) -> None:
    answer = qa_service.ask("xiaoao", "令狐冲的生日是哪天？")
    assert answer.answer == "图谱中暂无足够事实"
    assert answer.evidence == []
```

- [x] **Step 2: 运行并确认 `qa_service` 不存在**

Run: `cd apps/api && python -m pytest tests/qa/test_service.py -v`

Expected: fixture 或 import error。

- [x] **Step 3: 实现四类允许模板**

仅支持“实体简介”“人物关系”“所属组织/掌握武学”“两实体路径”。模板选择器使用确定性关键词和实体搜索，不调用模型。无法分类、实体不明确或无查询结果时返回固定无依据提示。

- [x] **Step 4: 实现响应解释**

响应显示参数化 Cypher 模板与脱敏参数；证据只返回短片段、章节和偏移；自然语言答案只能由命中节点、关系和证据拼装。

- [x] **Step 5: 运行测试并提交**

Run: `cd apps/api && python -m pytest tests/qa -v`

Expected: 全部 PASS。

```bash
git add apps/api/src/app/qa apps/api/src/app/main.py apps/api/tests/qa
git commit -m "feat: add explainable template questions"
```

### Task 6: 教学、本体与图谱前端

**Files:**
- Create: `apps/web/src/api/client.ts`
- Create: `apps/web/src/app/router.tsx`
- Create: `apps/web/src/features/guide/GuidePage.tsx`
- Create: `apps/web/src/features/ontology/OntologyPage.tsx`
- Create: `apps/web/src/features/graph/GraphPage.tsx`
- Create: `apps/web/src/features/graph/GraphCanvas.tsx`
- Create: `apps/web/src/features/graph/EntityPanel.tsx`
- Create: `apps/web/src/features/story/StoryPage.tsx`
- Create: `apps/web/src/features/ask/AskPage.tsx`
- Create: `apps/web/src/styles/theme.css`
- Create: `apps/web/src/features/guide/GuidePage.test.tsx`
- Create: `apps/web/src/features/graph/GraphPage.test.tsx`
- Create: `apps/web/src/features/story/StoryPage.test.tsx`
- Modify: `apps/web/src/App.tsx`

**Interfaces:**
- Consumes: Tasks 2、4、5 的 API。
- Produces: `/guide`、`/ontology`、`/graph`、`/story`、`/ask` 页面和业务/技术双层视图。

- [x] **Step 1: 写教学路径失败测试**

```tsx
it('moves from a triple to the ontology explanation', async () => {
  render(<GuidePage />)
  expect(screen.getByText('令狐冲')).toBeVisible()
  await userEvent.click(screen.getByRole('button', { name: '下一步：什么是本体' }))
  expect(screen.getByRole('heading', { name: '本体定义世界的规则' })).toBeVisible()
})
```

- [x] **Step 2: 写图谱交互失败测试**

```tsx
it('searches and expands an entity with evidence', async () => {
  server.use(searchHandler('令狐冲'), detailHandler('令狐冲', '第十章'))
  render(<GraphPage />)
  await userEvent.type(screen.getByRole('searchbox'), '令狐冲')
  await userEvent.click(await screen.findByText('令狐冲'))
  expect(await screen.findByText('第十章')).toBeVisible()
})
```

- [x] **Step 3: 运行并确认页面模块不存在**

Run: `npm --prefix apps/web test -- --run`

Expected: module resolution FAIL。

- [x] **Step 4: 实现统一页面壳与教学导览**

顶部导航固定为“导览、本体、图谱、故事线、问答、构建”；Phase 1 的“构建”显示“Phase 2 开放”说明，不出现无效上传按钮。导览以三元组、TBox/ABox、路径查询和证据链四步完成。

- [x] **Step 5: 实现本体和图谱页面**

本体页从 `/api/ontology` 加载，不在前端复制本体。Cytoscape 节点颜色来自实体类型；首次加载不绘制全图，只在搜索选中后展开一层。画布最多显示 100 节点；详情侧栏显示属性、关系、章节和短证据。

- [x] **Step 6: 实现问答页与技术展开面板**

提供四个可点击样例问题和文本输入。默认显示答案、路径和证据；“查看技术细节”展开 Cypher 模板、参数和查询说明。无结果时显示固定提示和返回图谱探索的链接。

- [x] **Step 7: 实现故事线页面**

故事线按章节顺序展示核心事件，并允许选择人物后只保留其参与事件。选择章节区间时，页面调用时间线和邻居查询的章节范围参数，展示该阶段有效的隶属、盟友、敌对与持有关系。组件测试固定验证“令狐冲”筛选后出现“思过崖传剑”，且不出现无关事件。

- [x] **Step 8: 运行组件测试和类型检查**

Run: `npm --prefix apps/web test -- --run && npm --prefix apps/web run typecheck`

Expected: 全部 PASS，TypeScript 无错误。

- [x] **Step 9: 提交**

```bash
git add apps/web/src
git commit -m "feat: add ontology teaching experience"
```

### Task 7: 端到端验收与本地运行文档

**Files:**
- Create: `tests/e2e/package.json`
- Create: `tests/e2e/playwright.config.ts`
- Create: `tests/e2e/demo.spec.ts`
- Create: `README.md`
- Modify: `Makefile`

**Interfaces:**
- Consumes: Tasks 1–6 的运行命令和 API。
- Produces: `make verify`；从空环境启动演示的操作文档。

- [x] **Step 1: 写端到端验收测试**

```ts
test('visitor learns, explores and verifies an answer', async ({ page }) => {
  await page.goto('/guide')
  await expect(page.getByRole('heading', { name: /看懂.*知识图谱/ })).toBeVisible()
  await page.getByRole('link', { name: '图谱' }).click()
  await page.getByRole('searchbox').fill('令狐冲')
  await page.getByText('令狐冲', { exact: true }).click()
  await expect(page.getByText('原文证据')).toBeVisible()
  await page.getByRole('link', { name: '问答' }).click()
  await page.getByRole('button', { name: '令狐冲的师父是谁？' }).click()
  await expect(page.getByText('岳不群')).toBeVisible()
  await page.getByRole('button', { name: '查看技术细节' }).click()
  await expect(page.getByText(/MATCH/)).toBeVisible()
  await page.getByRole('link', { name: '故事线' }).click()
  await page.getByRole('combobox', { name: '人物' }).selectOption({ label: '令狐冲' })
  await expect(page.getByText('思过崖传剑')).toBeVisible()
})
```

- [x] **Step 2: 运行并确认测试因服务未编排而失败**

Run: `npm --prefix tests/e2e test`

Expected: 连接失败或缺少 webServer 配置。

- [x] **Step 3: 配置 Playwright webServer 与 `make verify`**

Playwright 启动 FastAPI 和 Vite，Neo4j 由 Compose 提供；`make verify` 顺序执行后端测试、前端测试、类型检查、核心数据校验和 E2E。失败时保留 trace，成功时不生成仓库内截图。

- [x] **Step 4: 写 README**

README 明确 Python、Node、Docker 前置条件；给出环境变量表；提供 `make install`、`make neo4j-up`、`python scripts/import_core_graph.py`、`make dev`、`make verify`；说明 Phase 1 使用人工校验核心图，在线上传将在 Phase 2 实现。

- [x] **Step 5: 从清洁进程运行完整验证**

Run: `make verify`

Expected: pytest、Vitest、TypeScript、数据校验和 Playwright 全部退出码 0。

- [x] **Step 6: 提交**

```bash
git add tests/e2e README.md Makefile
git commit -m "test: verify knowledge graph demo end to end"
```

## Completion Gate

- `make verify` 全部通过。
- `git status --short` 只允许显示用户提供且未跟踪的 `笑傲江湖/` 目录。
- 《笑傲江湖》核心种子数据中每条确认事实都有章节、偏移、短引文和文本指纹。
- 图谱、问答和证据查询均受 `project_id`、深度、数量和超时约束。
- Phase 1 页面不存在伪装成可用功能的上传或模型配置入口。
