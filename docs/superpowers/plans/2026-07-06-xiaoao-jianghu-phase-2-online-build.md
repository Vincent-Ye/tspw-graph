# 《笑傲江湖》知识图谱阶段二在线构建 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付可上传 TXT、通过独立 Worker 调用 OpenAI 兼容 API 或 Ollama、可恢复地构建隔离知识图谱并展示进度与质量报告的阶段二闭环。

**Architecture:** React 构建工作台调用 FastAPI；FastAPI 将项目、文件和任务写入 SQLite，并通过 SSE 发布持久化状态。独立 Worker 使用租约领取任务，完成切分、结构化抽取、确定性消歧、本体校验和 Neo4j 幂等入图；模型密钥只由 Worker 从环境变量读取。

**Tech Stack:** Python 3.12+、FastAPI、Pydantic 2、SQLAlchemy 2、httpx、Neo4j Python Driver、pytest、React 19、TypeScript、Vite、Vitest、Playwright、Docker Compose。

## Global Constraints

- 单机 Docker Compose 部署，不引入 Redis、PostgreSQL、对象存储或多机 Worker。
- 单个 TXT 最大 20 MB；接受 UTF-8、UTF-8-BOM 和 GB18030，服务端规范化为 UTF-8。
- 上传路径、文件名和项目 ID 均由服务端控制；内置 `xiaoao` 项目只读。
- 模型密钥只读自 Worker 环境变量，不进入前端、SQLite、Neo4j、SSE 或日志。
- 默认测试使用固定响应模型；OpenAI 兼容 API 和 Ollama 使用本地假服务做契约测试。
- 所有 SQLite、文件和 Neo4j 数据都以 `project_id` 隔离；导入和删除必须幂等。
- 模型输出视为不可信输入，必须通过 Pydantic Schema、本体、数量限制和证据偏移校验。
- 每片最多尝试 3 次；暂停不领取新片段；恢复和 Worker 重启不得重复成功片段。

---

## File Map

### Backend domain

- `apps/api/src/app/projects/models.py`：项目、上传文件、任务、章节、片段、尝试和质量统计 SQLAlchemy 模型。
- `apps/api/src/app/projects/repository.py`：项目 CRUD 与 SQLite 初始化。
- `apps/api/src/app/projects/files.py`：上传流限制、编码识别、规范化和受控路径。
- `apps/api/src/app/projects/service.py`：项目上传和删除用例。
- `apps/api/src/app/projects/router.py`：项目与上传 HTTP API。
- `apps/api/src/app/jobs/models.py`：任务状态、API DTO 和状态转换表。
- `apps/api/src/app/jobs/repository.py`：任务领取租约、进度和事件快照。
- `apps/api/src/app/jobs/service.py`：暂停、恢复、取消、重试和质量报告。
- `apps/api/src/app/jobs/router.py`：任务控制与 SSE API。
- `apps/api/src/app/worker/main.py`：Worker 轮询入口。
- `apps/api/src/app/worker/runner.py`：单任务阶段编排。
- `apps/api/src/app/extraction/splitter.py`：章节识别、回退分段和重叠切片。
- `apps/api/src/app/extraction/models.py`：结构化模型输出与候选对象。
- `apps/api/src/app/extraction/providers.py`：统一模型接口和档案。
- `apps/api/src/app/extraction/openai_compatible.py`：OpenAI 兼容适配器。
- `apps/api/src/app/extraction/ollama.py`：Ollama 适配器。
- `apps/api/src/app/extraction/fixed.py`：固定响应适配器。
- `apps/api/src/app/extraction/router.py`：只读模型档案 API。
- `apps/api/src/app/extraction/normalize.py`：本体归一化、确定性消歧和证据校验。
- `apps/api/src/app/extraction/pipeline.py`：片段抽取、合并、质量统计和 GraphDocument 生成。
- `apps/api/src/app/graph/neo4j.py`：新增按项目删除和在线批次写入。
- `apps/api/src/app/settings.py`：数据目录、Worker、模型与资源限制配置。
- `apps/api/src/app/main.py`：注册项目和任务路由。

### Frontend

- `apps/web/src/api/client.ts`：项目、任务、质量和上传 API 类型。
- `apps/web/src/app/ProjectContext.tsx`：当前项目加载、切换和 URL 恢复。
- `apps/web/src/app/router.tsx`：使用真实构建页替换 Phase 2 占位页。
- `apps/web/src/features/build/BuildPage.tsx`：上传、监控和结果容器。
- `apps/web/src/features/build/UploadStep.tsx`：文件、标题和模型档案表单。
- `apps/web/src/features/build/JobProgress.tsx`：SSE 进度与控制按钮。
- `apps/web/src/features/build/QualityReport.tsx`：质量指标、拒绝原因和跳转。
- `apps/web/src/features/projects/ProjectSwitcher.tsx`：全局项目切换器。
- `apps/web/src/features/graph/GraphPage.tsx`、`story/StoryPage.tsx`、`ask/AskPage.tsx`：改为消费当前项目。

### Runtime and verification

- `apps/api/Dockerfile`、`apps/web/Dockerfile`：Compose 服务镜像。
- `apps/web/nginx.conf`：静态站点与同源 `/api`、SSE 反向代理。
- `compose.yaml`：web、api、worker、neo4j 和共享数据卷。
- `tests/e2e/online-build.spec.ts`：在线构建端到端路径。
- `README.md`、`.env.example`、`Makefile`：配置、运行和验证命令。

---

### Task 1: 持久化项目与受控上传文件

**Files:**
- Modify: `apps/api/src/app/projects/models.py`
- Modify: `apps/api/src/app/projects/repository.py`
- Create: `apps/api/src/app/projects/files.py`
- Modify: `apps/api/src/app/settings.py`
- Test: `apps/api/tests/projects/test_files.py`
- Test: `apps/api/tests/projects/test_repository.py`

**Interfaces:**
- Consumes: `Settings.sqlite_url` 和现有 `ProjectRepository.ensure_builtin_project()`。
- Produces: `StoredUpload`、`UploadStore.save(project_id, filename, stream)`、`ProjectRepository.create_user_project()`、`ProjectRepository.list_projects()` 和项目关联表。

- [ ] **Step 1: 写上传限制与编码识别失败测试**

```python
from io import BytesIO

import pytest

from app.projects.files import InvalidUpload, UploadStore


def test_save_normalizes_gb18030_and_uses_server_filename(tmp_path):
    store = UploadStore(tmp_path, max_bytes=1024)
    result = store.save("project-1", "../原稿.txt", BytesIO("第一章 开端".encode("gb18030")))
    assert result.encoding == "gb18030"
    assert result.path.parent == tmp_path / "project-1"
    assert result.path.name == "source.txt"
    assert result.path.read_text(encoding="utf-8") == "第一章 开端"


def test_save_rejects_non_txt_and_oversized_content(tmp_path):
    store = UploadStore(tmp_path, max_bytes=4)
    with pytest.raises(InvalidUpload, match="TXT_ONLY"):
        store.save("p", "book.pdf", BytesIO(b"text"))
    with pytest.raises(InvalidUpload, match="FILE_TOO_LARGE"):
        store.save("p", "book.txt", BytesIO(b"12345"))
```

- [ ] **Step 2: 运行测试并确认因模块缺失而失败**

Run: `.venv/bin/python -m pytest apps/api/tests/projects/test_files.py -v`
Expected: FAIL with `ModuleNotFoundError: app.projects.files`.

- [ ] **Step 3: 实现流式上传、编码识别和受控路径**

```python
@dataclass(frozen=True)
class StoredUpload:
    path: Path
    encoding: str
    size_bytes: int
    sha256: str


class UploadStore:
    def __init__(self, root: Path, max_bytes: int = 20 * 1024 * 1024):
        self.root = root.resolve()
        self.max_bytes = max_bytes

    def save(self, project_id: str, filename: str, stream: BinaryIO) -> StoredUpload:
        if Path(filename).suffix.lower() != ".txt":
            raise InvalidUpload("TXT_ONLY")
        raw = stream.read(self.max_bytes + 1)
        if len(raw) > self.max_bytes:
            raise InvalidUpload("FILE_TOO_LARGE")
        if not raw:
            raise InvalidUpload("EMPTY_FILE")
        text, encoding = decode_text(raw)
        project_dir = (self.root / project_id).resolve()
        if self.root not in project_dir.parents:
            raise InvalidUpload("INVALID_PROJECT_PATH")
        project_dir.mkdir(parents=True, exist_ok=False)
        path = project_dir / "source.txt"
        path.write_text(text, encoding="utf-8")
        return StoredUpload(path, encoding, len(raw), hashlib.sha256(raw).hexdigest())
```

`decode_text()` 必须按 `utf-8-sig`、`utf-8`、`gb18030` 顺序尝试，并在全部失败时抛出 `InvalidUpload("UNSUPPORTED_ENCODING")`。

- [ ] **Step 4: 扩展 SQLite 模型并测试项目创建**

```python
def test_create_user_project_persists_upload_metadata(tmp_path):
    repo = ProjectRepository(create_engine(f"sqlite:///{tmp_path / 'db.sqlite'}"))
    project = repo.create_user_project(
        project_id="p-1", title="测试小说", source_path="p-1/source.txt",
        source_sha256="abc", source_encoding="utf-8", source_size=12,
    )
    assert project.is_builtin is False
    assert repo.list_projects()[0].id == "p-1"
```

新增 `Project.is_builtin`、`source_path`、`source_sha256`、`source_encoding`、`source_size` 和 `updated_at`。`ensure_builtin_project()` 必须设置 `is_builtin=True`，且不覆盖已有用户字段。

- [ ] **Step 5: 运行项目测试**

Run: `.venv/bin/python -m pytest apps/api/tests/projects -v`
Expected: PASS.

- [ ] **Step 6: 提交**

```bash
git add apps/api/src/app/projects apps/api/src/app/settings.py apps/api/tests/projects
git commit -m "feat: persist uploaded novel projects"
```

---

### Task 2: 项目上传服务、列表与幂等删除 API

**Files:**
- Modify: `apps/api/pyproject.toml`
- Create: `apps/api/src/app/projects/service.py`
- Create: `apps/api/src/app/projects/router.py`
- Modify: `apps/api/src/app/graph/neo4j.py`
- Modify: `apps/api/src/app/main.py`
- Test: `apps/api/tests/projects/test_router.py`
- Test: `apps/api/tests/projects/test_service.py`

**Interfaces:**
- Consumes: Task 1 的 `UploadStore`、`ProjectRepository`。
- Produces: `ProjectUploadService.create()`、`GET /api/projects`、`GET /api/projects/{id}`、`DELETE /api/projects/{id}` 和 `Neo4jGraphWriter.delete_project(project_id)`。上传 HTTP 端点在 Task 3 创建任务仓储后接入。

- [ ] **Step 1: 写上传服务失败测试**

```python
def test_upload_service_creates_project(service):
    project = service.create(
        title="测试小说", filename="book.txt",
        stream=BytesIO("第一章\n令狐冲出现。".encode()),
    )
    assert project.title == "测试小说"
    assert project.source_path.endswith("source.txt")
```

- [ ] **Step 2: 运行并确认路由不存在**

Run: `.venv/bin/python -m pytest apps/api/tests/projects/test_service.py::test_upload_service_creates_project -v`
Expected: FAIL with `ImportError: ProjectUploadService`.

- [ ] **Step 3: 实现上传服务和 API DTO**

```python
class ProjectUploadService:
    def create(self, title: str, filename: str, stream: BinaryIO) -> Project:
        project_id = f"project-{uuid4()}"
        stored = self.uploads.save(project_id, filename, stream)
        try:
            project = self.projects.create_user_project(
                project_id=project_id, title=title.strip(),
                source_path=str(stored.path.relative_to(self.uploads.root)),
                source_sha256=stored.sha256, source_encoding=stored.encoding,
                source_size=stored.size_bytes,
            )
            return project
        except Exception:
            self.uploads.delete_project(project_id)
            raise
```

列表和删除路由在本任务注册。上传错误类型先由服务层保留，Task 3 的 multipart 路由负责映射为 HTTP 状态。在 `apps/api/pyproject.toml` 运行时依赖中加入 `python-multipart>=0.0.20,<1`，供 Task 3 解析上传。

- [ ] **Step 4: 写并实现项目删除测试**

```python
def test_delete_user_project_cleans_all_stores(service, graph_writer):
    service.delete("p-1")
    assert service.projects.get("p-1") is None
    assert not service.uploads.project_dir("p-1").exists()
    graph_writer.delete_project.assert_called_once_with("p-1")


def test_delete_builtin_project_is_forbidden(service):
    with pytest.raises(BuiltinProjectError):
        service.delete("xiaoao")
```

删除顺序固定为标记 `DELETING`、删除 Neo4j 项目数据、删除项目文件、删除 SQLite 行。重复调用已删除项目返回成功。Neo4j 查询必须参数化：`MATCH (n {project_id: $project_id}) DETACH DELETE n`。

- [ ] **Step 5: 运行项目 API 测试**

Run: `.venv/bin/python -m pytest apps/api/tests/projects -v`
Expected: PASS.

- [ ] **Step 6: 提交**

```bash
git add apps/api/pyproject.toml apps/api/src/app/projects apps/api/src/app/graph/neo4j.py apps/api/src/app/main.py apps/api/tests/projects
git commit -m "feat: add project upload and deletion APIs"
```

---

### Task 3: 持久化任务、租约 Worker 与 SSE

**Files:**
- Create: `apps/api/src/app/jobs/__init__.py`
- Create: `apps/api/src/app/jobs/models.py`
- Create: `apps/api/src/app/jobs/repository.py`
- Create: `apps/api/src/app/jobs/service.py`
- Create: `apps/api/src/app/jobs/router.py`
- Create: `apps/api/src/app/worker/__init__.py`
- Create: `apps/api/src/app/worker/main.py`
- Create: `apps/api/src/app/worker/runner.py`
- Modify: `apps/api/src/app/projects/models.py`
- Modify: `apps/api/src/app/projects/router.py`
- Modify: `apps/api/src/app/main.py`
- Test: `apps/api/tests/projects/test_router.py`
- Test: `apps/api/tests/jobs/test_repository.py`
- Test: `apps/api/tests/jobs/test_router.py`
- Test: `apps/api/tests/worker/test_runner.py`

**Interfaces:**
- Consumes: 项目 ID、模型档案 ID 和 SQLite engine。
- Produces: `JobStatus`、`JobRepository.claim_next(worker_id, lease_seconds)`、`JobService` 控制方法、`WorkerRunner.run_once()`、`POST /api/projects/upload` 和任务 HTTP/SSE API。

- [ ] **Step 1: 写状态转换和租约失败测试**

```python
def test_illegal_transition_is_rejected():
    with pytest.raises(InvalidJobTransition):
        transition(JobStatus.COMPLETED, JobStatus.EXTRACTING)


def test_expired_lease_can_be_reclaimed(repository, clock):
    job = repository.create("p-1", "fixed:test")
    assert repository.claim_next("w-1", 30).id == job.id
    clock.advance(seconds=31)
    assert repository.claim_next("w-2", 30).id == job.id
```

- [ ] **Step 2: 运行并确认 jobs 模块缺失**

Run: `.venv/bin/python -m pytest apps/api/tests/jobs/test_repository.py -v`
Expected: FAIL with `ModuleNotFoundError: app.jobs`.

- [ ] **Step 3: 实现状态机和原子领取**

```python
class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    SPLITTING = "SPLITTING"
    EXTRACTING = "EXTRACTING"
    RESOLVING = "RESOLVING"
    VALIDATING = "VALIDATING"
    IMPORTING = "IMPORTING"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


ALLOWED = {
    JobStatus.QUEUED: {JobStatus.SPLITTING, JobStatus.CANCELLED},
    JobStatus.SPLITTING: {JobStatus.EXTRACTING, JobStatus.PAUSED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.EXTRACTING: {JobStatus.RESOLVING, JobStatus.PAUSED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.RESOLVING: {JobStatus.VALIDATING, JobStatus.PAUSED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.VALIDATING: {JobStatus.IMPORTING, JobStatus.PAUSED, JobStatus.FAILED, JobStatus.CANCELLED},
    JobStatus.IMPORTING: {JobStatus.COMPLETED, JobStatus.FAILED},
    JobStatus.PAUSED: {JobStatus.QUEUED, JobStatus.CANCELLED},
    JobStatus.FAILED: {JobStatus.QUEUED, JobStatus.CANCELLED},
}
```

`claim_next()` 使用 SQLite `BEGIN IMMEDIATE`，只领取 `QUEUED` 或租约过期且非终止状态的任务，并原子更新 `worker_id`、`lease_expires_at` 和 `updated_at`。

- [ ] **Step 4: 写任务控制和 SSE 测试**

```python
def test_pause_resume_and_retry(client, queued_job):
    assert client.post(f"/api/jobs/{queued_job.id}/pause").json()["status"] == "PAUSED"
    assert client.post(f"/api/jobs/{queued_job.id}/resume").json()["status"] == "QUEUED"


def test_events_resume_after_last_event_id(client, job_with_events):
    response = client.get(
        f"/api/jobs/{job_with_events.id}/events",
        headers={"Last-Event-ID": "1"},
    )
    assert "id: 2" in response.text
    assert "event: job" in response.text
```

SSE 每次发送完整安全快照，事件 ID 单调递增；测试环境在任务终止后关闭流。生产流每 15 秒发送注释心跳，并在客户端断开时停止轮询。

上传端点在同一步接入 Task 2 的服务和本任务的任务仓储：

```python
def test_upload_creates_project_and_queued_job(client):
    response = client.post(
        "/api/projects/upload",
        data={"title": "测试小说", "model_profile_id": "fixed:test"},
        files={"file": ("book.txt", "第一章\n令狐冲出现。".encode(), "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["job"]["status"] == "QUEUED"
```

路由先校验标题 1–300 字和模型档案允许列表，再调用 `ProjectUploadService.create()` 与 `JobRepository.create()`；若任务创建失败，调用项目删除服务回滚项目。上传错误映射为 `413 FILE_TOO_LARGE`、`415 TXT_ONLY/UNSUPPORTED_ENCODING` 或 `422 EMPTY_FILE`。

- [ ] **Step 5: 实现 Worker 单轮编排与重启测试**

```python
def test_runner_does_not_repeat_completed_stage(repository, runner):
    job = repository.create("p-1", "fixed:test")
    repository.set_status(job.id, JobStatus.EXTRACTING)
    runner.run_once()
    assert runner.splitter.calls == 0
    assert runner.extractor.calls == 1
```

`WorkerRunner.run_once()` 领取一个任务，从当前持久化阶段调用对应处理器；每完成一个阶段立即写入下一状态并续租。捕获异常时使用错误分类器决定重试片段或将任务标记为 `FAILED`，事件只保存稳定错误码。

- [ ] **Step 6: 运行任务和 Worker 测试**

Run: `.venv/bin/python -m pytest apps/api/tests/jobs apps/api/tests/worker -v`
Expected: PASS.

- [ ] **Step 7: 提交**

```bash
git add apps/api/src/app/jobs apps/api/src/app/worker apps/api/src/app/projects apps/api/src/app/main.py apps/api/tests/jobs apps/api/tests/projects/test_router.py apps/api/tests/worker
git commit -m "feat: add resumable extraction jobs"
```

---

### Task 4: 章节识别、回退分段与重叠切片

**Files:**
- Create: `apps/api/src/app/extraction/__init__.py`
- Create: `apps/api/src/app/extraction/splitter.py`
- Test: `apps/api/tests/extraction/test_splitter.py`

**Interfaces:**
- Consumes: 规范化 UTF-8 文本。
- Produces: `Chapter(number, title, start_offset, end_offset, text)`、`TextChunk(id, chapter_number, start_offset, end_offset, text)` 和 `split_document(text, max_chars, overlap_chars)`。

- [ ] **Step 1: 写章节与绝对偏移测试**

```python
def test_split_document_preserves_absolute_offsets():
    text = "序言\n第一章 开端\n甲乙丙丁\n第二章 转折\n戊己庚辛"
    result = split_document(text, max_chars=8, overlap_chars=2)
    assert [chapter.title for chapter in result.chapters] == ["序言", "开端", "转折"]
    for chunk in result.chunks:
        assert text[chunk.start_offset:chunk.end_offset] == chunk.text


def test_document_without_headings_falls_back_to_body_chunks():
    result = split_document("第一段。\n\n第二段。", max_chars=8, overlap_chars=2)
    assert result.chapters[0].title == "正文"
    assert result.chunks
```

- [ ] **Step 2: 运行并确认 splitter 缺失**

Run: `.venv/bin/python -m pytest apps/api/tests/extraction/test_splitter.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: 实现确定性切分**

章节标题支持 `第[零一二三四五六七八九十百千0-9]+[章节回]`。前置文本归为“序言”；没有标题时全部归为“正文”。切片优先在空行和句号处分界，无法找到边界时按字符上限切分；每个新片段最多向前重叠 `overlap_chars`，但不得越过章节起点。

```python
@dataclass(frozen=True)
class TextChunk:
    id: str
    chapter_number: int
    start_offset: int
    end_offset: int
    text: str

    def validate_against(self, source: str) -> None:
        if source[self.start_offset:self.end_offset] != self.text:
            raise ValueError("CHUNK_OFFSET_MISMATCH")
```

- [ ] **Step 4: 添加边界测试并运行**

覆盖 CRLF、UTF-8-BOM 已移除文本、超长单段、重复章节名、重叠不跨章节和空白正文。

Run: `.venv/bin/python -m pytest apps/api/tests/extraction/test_splitter.py -v`
Expected: PASS.

- [ ] **Step 5: 提交**

```bash
git add apps/api/src/app/extraction apps/api/tests/extraction/test_splitter.py
git commit -m "feat: split uploaded novels into traceable chunks"
```

---

### Task 5: 统一模型接口与供应商契约

**Files:**
- Create: `apps/api/src/app/extraction/models.py`
- Create: `apps/api/src/app/extraction/providers.py`
- Create: `apps/api/src/app/extraction/openai_compatible.py`
- Create: `apps/api/src/app/extraction/ollama.py`
- Create: `apps/api/src/app/extraction/fixed.py`
- Create: `apps/api/src/app/extraction/router.py`
- Modify: `apps/api/src/app/settings.py`
- Modify: `apps/api/src/app/main.py`
- Test: `apps/api/tests/extraction/test_models.py`
- Test: `apps/api/tests/extraction/test_providers.py`
- Test: `apps/api/tests/extraction/test_provider_contracts.py`

**Interfaces:**
- Consumes: `TextChunk` 和本体目录。
- Produces: `ExtractionProvider.extract(request) -> ExtractionResult`、`ProviderRegistry` 和 `GET /api/model-profiles`。

- [ ] **Step 1: 写恶意与越界模型输出测试**

```python
def test_extraction_result_rejects_excessive_entities():
    payload = {"entities": [{"name": str(i), "type": "Person"} for i in range(101)], "facts": []}
    with pytest.raises(ValidationError):
        ExtractionResult.model_validate(payload)


def test_evidence_offsets_must_be_inside_chunk():
    with pytest.raises(ValidationError):
        CandidateEvidence(start=0, end=999, quote="越界", chunk_length=10)
```

- [ ] **Step 2: 运行并确认模型类型缺失**

Run: `.venv/bin/python -m pytest apps/api/tests/extraction/test_models.py -v`
Expected: FAIL with import error.

- [ ] **Step 3: 实现严格候选 Schema**

```python
class CandidateEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    local_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    aliases: list[str] = Field(default_factory=list, max_length=20)


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entities: list[CandidateEntity] = Field(max_length=100)
    facts: list[CandidateFact] = Field(max_length=200)
```

证据使用片段局部 `start`、`end` 和 `quote`；验证器检查 `0 <= start < end <= chunk_length`、引文长度不超过 500。

- [ ] **Step 4: 写 OpenAI 与 Ollama 契约测试**

```python
def test_openai_provider_uses_json_schema(httpx_mock, request):
    httpx_mock.add_response(json={"choices": [{"message": {"content": FIXED_JSON}}]})
    result = OpenAICompatibleProvider(base_url="http://fake/v1", model="demo", api_key="secret").extract(request)
    sent = httpx_mock.get_request()
    assert sent.url.path == "/v1/chat/completions"
    assert sent.headers["authorization"] == "Bearer secret"
    assert result.entities[0].name == "令狐冲"


def test_ollama_provider_uses_structured_format(httpx_mock, request):
    httpx_mock.add_response(json={"message": {"content": FIXED_JSON}})
    result = OllamaProvider(base_url="http://fake", model="qwen3").extract(request)
    assert httpx_mock.get_request().url.path == "/api/chat"
    assert result.facts
```

将 `pytest-httpx` 加入 dev 依赖。适配器统一设置连接/读取超时、禁止无限响应体，并将 429/5xx/网络超时分类为可重试错误；401/403、模型不存在和 Schema 错误分类为永久或配置错误。

- [ ] **Step 5: 实现环境档案和只读 API**

`Settings` 支持 `MODEL_PROFILES_JSON`，每个档案包含 `id`、`provider`、`base_url`、`model`、`api_key_env`、`timeout_seconds`。`ProviderRegistry` 只在 Worker 解析 `api_key_env` 指向的环境变量；API 返回时移除 `api_key_env` 并只给出 `available: bool`。

- [ ] **Step 6: 运行适配层测试**

Run: `.venv/bin/python -m pytest apps/api/tests/extraction/test_models.py apps/api/tests/extraction/test_providers.py apps/api/tests/extraction/test_provider_contracts.py -v`
Expected: PASS and captured logs do not contain `secret`.

- [ ] **Step 7: 提交**

```bash
git add apps/api/pyproject.toml apps/api/src/app/extraction apps/api/src/app/settings.py apps/api/src/app/main.py apps/api/tests/extraction
git commit -m "feat: add structured extraction providers"
```

---

### Task 6: 抽取归一化、幂等入图与质量报告

**Files:**
- Create: `apps/api/src/app/extraction/normalize.py`
- Create: `apps/api/src/app/extraction/pipeline.py`
- Modify: `apps/api/src/app/worker/runner.py`
- Modify: `apps/api/src/app/graph/importer.py`
- Modify: `apps/api/src/app/graph/neo4j.py`
- Modify: `apps/api/src/app/jobs/service.py`
- Modify: `apps/api/src/app/jobs/router.py`
- Test: `apps/api/tests/extraction/test_normalize.py`
- Test: `apps/api/tests/extraction/test_pipeline.py`
- Test: `apps/api/tests/jobs/test_quality.py`
- Test: `apps/api/tests/extraction/test_live_pipeline.py`

**Interfaces:**
- Consumes: Task 4 的 `TextChunk`、Task 5 的 `ExtractionResult`、现有 `GraphImporter`。
- Produces: `normalize_chunk_result()`、`ExtractionPipeline.process_job()`、在线 `GraphDocument` 和 `GET /api/jobs/{id}/quality`。

- [ ] **Step 1: 写本体与证据拒绝测试**

```python
def test_normalizer_rejects_unknown_type_and_quote_mismatch(chunk, catalog):
    result = ExtractionResult.model_validate({
        "entities": [{"local_id": "x", "name": "某人", "type": "Unknown", "aliases": []}],
        "facts": [],
    })
    normalized = normalize_chunk_result("p-1", chunk, result, catalog)
    assert normalized.entities == []
    assert normalized.rejections[0].code == "UNKNOWN_ENTITY_TYPE"


def test_same_name_with_deterministic_alias_merges(candidate_batch):
    resolved = resolve_entities(candidate_batch, aliases={"令狐沖": "令狐冲"})
    assert len(resolved.entities) == 1
```

- [ ] **Step 2: 运行并确认归一化函数缺失**

Run: `.venv/bin/python -m pytest apps/api/tests/extraction/test_normalize.py -v`
Expected: FAIL with import error.

- [ ] **Step 3: 实现稳定标识和保守消歧**

稳定实体 ID 为 `project_id:type:slug(normalized_name)`；事实 ID 为 `sha256(project_id|relation|source_id|target_id|from_chapter|to_chapter)`。只合并规范名相同或明确别名映射的实体；同名但类型或上下文冲突时生成带短哈希后缀的候选 ID，并计入 `ambiguous_entities`。

证据局部偏移换算为 `chunk.start_offset + local_offset`，随后验证源文本切片等于 quote；不一致时拒绝该证据及依赖它的事实。

- [ ] **Step 4: 写完整流水线幂等测试**

```python
def test_fixed_provider_pipeline_is_idempotent(pipeline, graph_repository, uploaded_project):
    first = pipeline.process_job(uploaded_project.job_id)
    second = pipeline.process_job(uploaded_project.job_id, force_replay=True)
    assert first.quality.accepted_facts > 0
    assert graph_repository.count_entities(uploaded_project.id) == first.quality.accepted_entities
    assert second.import_summary.created_entities == 0
    assert second.import_summary.created_facts == 0
```

流水线必须逐片保存成功结果，失败片段记录尝试和错误码。跨片段合并完成后构造现有 `GraphDocument`，复用 `GraphImporter` 写入，不另建图写入逻辑。

- [ ] **Step 5: 实现质量报告 API**

```python
class QualityReport(BaseModel):
    total_chunks: int
    successful_chunks: int
    failed_chunks: int
    accepted_entities: int
    accepted_facts: int
    accepted_evidence: int
    ambiguous_entities: int
    rejected_by_code: dict[str, int]
    model_calls: int
    retry_count: int
```

`GET /api/jobs/{id}/quality` 仅对 `COMPLETED`、`FAILED` 或 `CANCELLED` 任务返回报告；构建中返回 `409 QUALITY_NOT_READY`。

- [ ] **Step 6: 运行固定模型到 Neo4j 集成测试**

Run: `RUN_NEO4J_INTEGRATION=1 .venv/bin/python -m pytest apps/api/tests/extraction/test_live_pipeline.py -v`
Expected: PASS with project-scoped entities, facts and evidence queryable.

- [ ] **Step 7: 提交**

```bash
git add apps/api/src/app/extraction apps/api/src/app/worker apps/api/src/app/graph apps/api/src/app/jobs apps/api/tests/extraction apps/api/tests/jobs
git commit -m "feat: build validated project graphs online"
```

---

### Task 7: 构建工作台与全局项目切换

**Files:**
- Modify: `apps/web/src/api/client.ts`
- Create: `apps/web/src/app/ProjectContext.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/app/router.tsx`
- Create: `apps/web/src/features/projects/ProjectSwitcher.tsx`
- Create: `apps/web/src/features/build/BuildPage.tsx`
- Create: `apps/web/src/features/build/UploadStep.tsx`
- Create: `apps/web/src/features/build/JobProgress.tsx`
- Create: `apps/web/src/features/build/QualityReport.tsx`
- Modify: `apps/web/src/features/graph/GraphPage.tsx`
- Modify: `apps/web/src/features/story/StoryPage.tsx`
- Modify: `apps/web/src/features/ask/AskPage.tsx`
- Modify: `apps/web/src/styles/theme.css`
- Test: `apps/web/src/features/build/BuildPage.test.tsx`
- Test: `apps/web/src/app/ProjectContext.test.tsx`

**Interfaces:**
- Consumes: Tasks 2、3、5、6 的项目、任务、档案、SSE 和质量 API。
- Produces: 上传—监控—结果 UI，以及图谱、故事线和问答共享的 `useProject()`。

- [ ] **Step 1: 写项目 URL 恢复测试**

```tsx
it('restores the selected project from the URL', async () => {
  window.history.replaceState({}, '', '/graph?project=project-1')
  render(<ProjectProvider><Probe /></ProjectProvider>)
  expect(await screen.findByText('project-1')).toBeVisible()
})
```

- [ ] **Step 2: 运行并确认 ProjectContext 缺失**

Run: `npm --prefix apps/web test -- --run src/app/ProjectContext.test.tsx`
Expected: FAIL with unresolved import.

- [ ] **Step 3: 实现项目上下文和切换器**

```tsx
type ProjectContextValue = {
  projects: ProjectSummary[]
  projectId: string
  setProjectId: (id: string) => void
  refreshProjects: () => Promise<void>
}

export function useProject(): ProjectContextValue {
  const value = useContext(ProjectContext)
  if (!value) throw new Error('useProject must be used inside ProjectProvider')
  return value
}
```

默认项目为 URL `project` 参数，否则使用 `xiaoao`。切换时使用 `history.replaceState` 保留当前路由并更新参数。Graph、Story、Ask 移除固定 `PROJECT_ID`，统一读取上下文。

- [ ] **Step 4: 写上传和任务恢复测试**

```tsx
it('uploads a novel and restores progress after remount', async () => {
  const user = userEvent.setup()
  const { unmount } = render(<BuildPage />)
  await user.upload(screen.getByLabelText('TXT 小说'), new File(['第一章'], 'book.txt', { type: 'text/plain' }))
  await user.type(screen.getByLabelText('项目标题'), '测试小说')
  await user.selectOptions(screen.getByLabelText('模型配置'), 'fixed:test')
  await user.click(screen.getByRole('button', { name: '开始构建' }))
  expect(await screen.findByText('抽取实体与关系')).toBeVisible()
  unmount()
  render(<BuildPage />)
  expect(await screen.findByText('抽取实体与关系')).toBeVisible()
})
```

- [ ] **Step 5: 实现三段构建工作台**

`UploadStep` 使用 `FormData`，客户端提前检查 `.txt` 与 20 MB，但服务端仍是权威。`JobProgress` 使用 `EventSource`，每个事件覆盖本地任务快照；`error` 时关闭连接并退回每 2 秒请求 `GET /api/jobs/{id}`，任务终止后停止轮询。控制按钮只在状态允许时显示。

`QualityReport` 显示指标、拒绝原因和“进入项目图谱”；点击后设置当前项目并导航到 `/graph?project=<id>`。

- [ ] **Step 6: 添加错误与无障碍测试**

覆盖上传失败、模型档案不可用、暂停/恢复、失败重试、SSE 重连、按钮禁用、进度条 `aria-valuenow` 和错误 `role=alert`。

Run: `npm --prefix apps/web test -- --run`
Expected: PASS.

- [ ] **Step 7: 运行类型检查与生产构建**

Run: `npm --prefix apps/web run typecheck && npm --prefix apps/web run build`
Expected: both exit 0; no new chunk exceeds the existing graph-engine chunk by more than 100 kB.

- [ ] **Step 8: 提交**

```bash
git add apps/web/src
git commit -m "feat: add online graph build workspace"
```

---

### Task 8: Docker Compose、端到端验收与运行文档

**Files:**
- Create: `apps/api/Dockerfile`
- Create: `apps/web/Dockerfile`
- Create: `apps/web/nginx.conf`
- Modify: `compose.yaml`
- Modify: `Makefile`
- Create: `.env.example`
- Modify: `README.md`
- Create: `tests/e2e/fixtures/sample-novel.txt`
- Create: `tests/e2e/online-build.spec.ts`
- Modify: `tests/e2e/playwright.config.ts`

**Interfaces:**
- Consumes: Tasks 1–7 全部运行接口。
- Produces: `docker compose up --build` 的 web/api/worker/neo4j 栈、可选真实模型冒烟命令和最终 `make verify`。

- [ ] **Step 1: 写在线构建 E2E 测试**

```ts
test('uploads, builds and explores an isolated graph', async ({ page }) => {
  await page.goto('/build')
  await page.getByLabel('TXT 小说').setInputFiles('fixtures/sample-novel.txt')
  await page.getByLabel('项目标题').fill('E2E 小说')
  await page.getByLabel('模型配置').selectOption('fixed:test')
  await page.getByRole('button', { name: '开始构建' }).click()
  await expect(page.getByText('构建完成')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText('接受事实')).not.toContainText('0')
  await page.getByRole('link', { name: '进入项目图谱' }).click()
  await expect(page).toHaveURL(/\/graph\?project=project-/)
  await page.getByRole('searchbox').fill('测试人物')
  await expect(page.getByRole('button', { name: /测试人物/ })).toBeVisible()
})
```

- [ ] **Step 2: 运行并确认 Compose/Worker 尚未编排而失败**

Run: `npm --prefix tests/e2e test -- online-build.spec.ts`
Expected: FAIL because `/build` still lacks a running Worker-backed completion path.

- [ ] **Step 3: 编排四服务与共享卷**

`compose.yaml` 新增：

```yaml
  api:
    build: ./apps/api
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    environment: &app-env
      SQLITE_URL: sqlite:////data/tspw-graph.db
      DATA_ROOT: /data/uploads
      NEO4J_URI: bolt://neo4j:7687
      MODEL_PROFILES_JSON: '${MODEL_PROFILES_JSON:-[{"id":"fixed:test","provider":"fixed","base_url":"","model":"test","api_key_env":"","timeout_seconds":10}]}'
    volumes: [app-data:/data]
    depends_on:
      neo4j: {condition: service_healthy}
  worker:
    build: ./apps/api
    command: python -m app.worker.main
    environment: *app-env
    volumes: [app-data:/data]
    depends_on:
      neo4j: {condition: service_healthy}
  web:
    build: ./apps/web
    ports: ["5173:80"]
    depends_on: [api]
```

Web 容器通过同源 `/api` 反向代理 API。API 与 Worker 共享 `app-data`，但只有 Worker 读取模型密钥环境变量；若 Compose YAML 锚点会把密钥传给 API，必须拆分公开配置和 Worker 私密环境，确保 API 容器环境中没有密钥。

`apps/web/nginx.conf` 对 SSE 禁用代理缓冲：

```nginx
server {
  listen 80;
  root /usr/share/nginx/html;
  location / { try_files $uri /index.html; }
  location /api/ {
    proxy_pass http://api:8000;
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_read_timeout 1h;
  }
}
```

Playwright 改为复用 `make verify` 已启动的 Compose 服务，不再自行启动仅含 API/Vite 的旧开发栈：

```ts
export default defineConfig({
  testDir: '.',
  timeout: 30_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
  },
})
```

- [ ] **Step 4: 扩展验证命令与真实模型冒烟入口**

`make verify` 顺序为：Compose 健康启动、固定数据导入、后端全测试、前端测试、类型检查、生产构建、证据校验和全部 Playwright。新增：

```make
worker:
	.venv/bin/python -m app.worker.main

smoke-openai:
	RUN_MODEL_SMOKE=openai .venv/bin/python -m pytest apps/api/tests/extraction/test_model_smoke.py -v

smoke-ollama:
	RUN_MODEL_SMOKE=ollama .venv/bin/python -m pytest apps/api/tests/extraction/test_model_smoke.py -v
```

冒烟测试缺少相应档案或密钥时明确 skip，不进入默认 `verify`。

- [ ] **Step 5: 写 `.env.example` 与 README**

文档必须列出 `DATA_ROOT`、`MODEL_PROFILES_JSON`、OpenAI 密钥变量和 Ollama 地址示例；说明密钥只设置在 Worker 环境；给出本地进程运行、Compose 运行、项目删除、失败重试、两种冒烟测试和数据卷备份命令。样例中使用占位值，不能包含真实密钥。

- [ ] **Step 6: 从冷启动运行完整验收**

Run: `docker compose down && make verify`
Expected: backend tests、frontend tests、typecheck、build、evidence validation、Phase 1 E2E and online-build E2E all exit 0.

- [ ] **Step 7: 执行密钥与原文泄漏检查**

Run: `git grep -n -E 'sk-[A-Za-z0-9_-]{20,}|Bearer [A-Za-z0-9_-]{20,}' -- ':!docs/superpowers/plans/*'`
Expected: no output.

Run: `git ls-files '笑傲江湖/**'`
Expected: no output.

- [ ] **Step 8: 提交**

```bash
git add apps/api/Dockerfile apps/web/Dockerfile apps/web/nginx.conf compose.yaml Makefile .env.example README.md tests/e2e
git commit -m "test: verify online graph builds end to end"
```

## Completion Gate

- `docker compose down && make verify` 从冷启动全部通过。
- 固定模型完成上传、异步处理、Neo4j 入图、质量报告、项目切换和图谱查询闭环。
- OpenAI 兼容 API 与 Ollama 契约测试通过；真实模型冒烟测试可按环境开关执行。
- 暂停、恢复、取消、失败片段重试和 Worker 重启续跑均有自动测试。
- 20 MB、UTF-8/UTF-8-BOM/GB18030、路径穿越、恶意模型输出和项目隔离测试通过。
- SQLite、Neo4j、日志、SSE 和前端中均不存在模型密钥。
- `git status --short` 为空，且小说原文未被 Git 跟踪。
