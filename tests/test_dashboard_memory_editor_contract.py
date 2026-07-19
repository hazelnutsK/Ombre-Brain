import json
from pathlib import Path
import shutil
import subprocess

import pytest

import web.buckets as buckets_web


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "frontend" / "dashboard.html"


class FakeMCP:
    def __init__(self):
        self.routes = {}

    def custom_route(self, path, methods):
        def decorator(handler):
            for method in methods:
                self.routes[(method, path)] = handler
            return handler

        return decorator


class JsonRequest:
    def __init__(self, *, path_params=None):
        self.path_params = path_params or {}
        self.headers = {}
        self.query_params = {}


class FakeDecayEngine:
    def calculate_score(self, _metadata):
        return 1.0


class FakeBucketManager:
    def __init__(self, bucket):
        self.bucket = bucket

    async def list_all(self, *, include_archive=False):
        assert include_archive is True
        return [self.bucket]

    async def get(self, bucket_id):
        return self.bucket if bucket_id == self.bucket["id"] else None

    async def get_triggered_feels(self, _bucket_id):
        return []


def _payload(response):
    return json.loads(response.body.decode("utf-8"))


def _dashboard_function(name, next_name):
    html = DASHBOARD.read_text(encoding="utf-8")
    start = html.index(f"function {name}(")
    end = html.index(f"function {next_name}(", start)
    return html[start:end]


@pytest.mark.asyncio
async def test_bucket_detail_preserves_raw_content_and_separates_display_text(
    monkeypatch,
):
    raw_content = "before [[Target|Alias]] and [[Target#Section]] after"
    bucket = {
        "id": "memory-1",
        "metadata": {"name": "Linked memory", "type": "dynamic"},
        "content": raw_content,
    }
    manager = FakeBucketManager(bucket)
    monkeypatch.setattr(buckets_web.sh, "_require_auth", lambda _request: None)
    monkeypatch.setattr(buckets_web.sh, "bucket_mgr", manager, raising=False)
    monkeypatch.setattr(
        buckets_web.sh, "decay_engine", FakeDecayEngine(), raising=False
    )
    mcp = FakeMCP()
    buckets_web.register(mcp)

    list_response = await mcp.routes[("GET", "/api/buckets")](JsonRequest())
    detail_response = await mcp.routes[("GET", "/api/bucket/{bucket_id}")](
        JsonRequest(path_params={"bucket_id": "memory-1"})
    )
    listed = _payload(list_response)[0]
    detail = _payload(detail_response)

    assert listed["content_preview"] == (
        "before Target|Alias and Target#Section after"
    )
    assert detail["content"] == raw_content
    assert detail["display_content"] == listed["content_preview"]


def test_dashboard_uses_display_text_for_preview_and_raw_content_for_editor():
    source = _dashboard_function("showDetail", "bucketPin")

    assert "typeof b.display_content === 'string'" in source
    assert "esc(displayContent)" in source
    assert "_content_for_edit: b.content" in source
    assert "'<div class=\"detail-content\">' + esc(b.content)" not in source


def test_dashboard_detail_does_not_render_an_editor_for_failed_bucket_fetch():
    source = _dashboard_function("showDetail", "bucketPin")

    assert "var b = await readJsonSafe(res);" in source
    assert "if (!res.ok)" in source
    assert "Array.isArray(b)" in source
    assert "const generation = ++detailLoadGeneration;" in source
    assert "if (generation !== detailLoadGeneration) return false;" in source
    assert source.index("if (!res.ok)") < source.index("renderEditForm(")


def test_editor_preserves_special_and_future_bucket_types():
    render_source = _dashboard_function("renderEditForm", "bucketSaveEdit")
    save_source = _dashboard_function("bucketSaveEdit", "maybeShowOnboarding")

    assert (
        "const editableTypes = ['dynamic','permanent','feel','plan','letter']"
        in render_source
    )
    assert "const currentType = String(meta.type || 'dynamic')" in render_source
    assert "[currentType].concat(editableTypes)" in render_source
    assert "meta.pinned && typeIsEditable" in render_source
    assert "? ['permanent', 'dynamic']" in render_source
    assert "currentType === t ? 'selected' : ''" in render_source
    assert "typeIsEditable ? '' : 'disabled" in render_source
    assert "if (typeEl && !typeEl.disabled) body.type = typeEl.value" in save_source
    assert "type: document.getElementById('edit-type').value" not in save_source


def test_editor_submits_metadata_using_storage_field_names():
    source = _dashboard_function("bucketSaveEdit", "maybeShowOnboarding")

    assert "dont_surface: document.getElementById('edit-dont-surface').checked" in source
    assert "why_remembered: document.getElementById('edit-why').value" in source
    assert "if (weightEl) body.weight = parseFloat(weightEl.value) / 100" in source


def test_editor_keeps_pin_type_and_importance_constraints_in_sync():
    render_source = _dashboard_function("renderEditForm", "syncEditPinConstraints")
    sync_source = _dashboard_function("syncEditPinConstraints", "bucketSaveEdit")
    save_source = _dashboard_function("bucketSaveEdit", "maybeShowOnboarding")

    assert "onchange=\"syncEditPinConstraints('type')\"" in render_source
    assert "syncEditPinConstraints('importance')" in render_source
    assert "onchange=\"syncEditPinConstraints('pinned')\"" in render_source
    assert "typeEl.value = 'permanent';" in sync_source
    assert "importanceEl.value = '10';" in sync_source
    assert "pinnedEl.checked = false;" in sync_source
    assert "syncEditPinConstraints('save');" in save_source
    assert save_source.index("syncEditPinConstraints('save');") < save_source.index(
        "const body = {"
    )


def test_imported_memory_cards_open_the_full_editor_and_refresh_after_save():
    list_source = _dashboard_function(
        "loadImportResults", "openImportedBucketEditor"
    )
    open_source = _dashboard_function(
        "openImportedBucketEditor", "detectPatterns"
    )
    render_source = _dashboard_function("renderEditForm", "syncEditPinConstraints")
    save_source = _dashboard_function("bucketSaveEdit", "maybeShowOnboarding")

    # The import result contains only a 300-character preview. The edit button
    # must pass only the ID and let showDetail fetch the lossless bucket body.
    assert "openImportedBucketEditor(this.dataset.bucketId)" in list_source
    assert 'data-bucket-id="${escAttr(b.id)}"' in list_source
    assert "renderEditForm(b.id, b)" not in list_source
    assert "if (!await showDetail(bid)) return;" in open_source

    # One global detail editor avoids duplicate edit-* element IDs, and opening
    # from the import review area should land directly in the expanded form.
    assert 'id="bucket-edit-form"' in render_source
    assert "document.getElementById('bucket-edit-form')" in open_source
    assert "editor.open = true;" in open_source
    assert 'for="edit-content"' in render_source
    assert "contentInput.focus();" in open_source
    assert "preventScroll" not in open_source

    # Saving while the import tab is visible refreshes the preview card without
    # kicking the reviewer back to the top of the list.
    assert "const importView = document.getElementById('import-view');" in save_source
    assert "const refreshImportResults =" in save_source
    assert "const detailGenerationAtSave = detailLoadGeneration;" in save_source
    assert "if (detailLoadGeneration === detailGenerationAtSave)" in save_source
    assert (
        "await loadImportResults({preserveScroll:true, "
        "scrollTop:importScrollTop});" in save_source
    )
    assert save_source.index("if (!r.ok)") < save_source.index(
        "await loadImportResults({preserveScroll:true, scrollTop:importScrollTop});"
    ) < save_source.index("} catch (e) {")


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is unavailable")
def test_imported_memory_editor_opens_and_focuses_at_runtime():
    html = DASHBOARD.read_text(encoding="utf-8")
    start = html.index("async function openImportedBucketEditor(")
    end = html.index("async function detectPatterns(", start)
    source = html[start:end]
    script = """
let passedId = null;
let scrolled = false;
let focused = false;
let loadSucceeds = true;
const editor = {
  open: false,
  scrollIntoView(options) { scrolled = options.block === 'start'; },
};
const contentInput = {
  focus() { focused = true; },
};
const document = {
  getElementById(id) {
    if (id === 'bucket-edit-form') return editor;
    if (id === 'edit-content') return contentInput;
    return null;
  },
};
async function showDetail(id) { passedId = id; return loadSucceeds; }
""" + source + """
(async function() {
  await openImportedBucketEditor('id / & "quoted"');
  const success = [passedId, editor.open, focused];
  editor.open = false;
  focused = false;
  loadSucceeds = false;
  await openImportedBucketEditor('missing');
  process.stdout.write(JSON.stringify([
    success, editor.open, focused,
  ]));
})().catch(function(error) {
  console.error(error);
  process.exit(1);
});
"""
    completed = subprocess.run(
        [shutil.which("node"), "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == [
        ['id / & "quoted"', True, True], False, False,
    ]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is unavailable")
def test_import_results_latest_request_wins_and_preserves_scroll():
    html = DASHBOARD.read_text(encoding="utf-8")
    start = html.index("let importResultsLoadGeneration = 0;")
    end = html.index("async function openImportedBucketEditor(", start)
    source = html[start:end]
    script = """
const pending = [];
const container = {
  innerHTML: '<div>existing</div>',
  scrollTop: 73,
  setAttribute() {},
  removeAttribute() {},
};
const document = {
  getElementById(id) { return id === 'import-results-list' ? container : null; },
};
const BASE = '';
function fetch() { return new Promise(resolve => pending.push(resolve)); }
async function readJsonSafe(response) { return response.payload; }
function esc(value) { return String(value == null ? '' : value); }
function escAttr(value) { return esc(value); }
""" + source + """
(async function() {
  const oldRequest = loadImportResults({preserveScroll:true, scrollTop:73});
  const newRequest = loadImportResults({preserveScroll:true, scrollTop:73});
  pending[1]({ok:true, status:200, payload:{buckets:[{
    id:'new', name:'fresh response', content:'new body', type:'dynamic',
    domain:[], tags:[], importance:5,
  }]}});
  await newRequest;
  pending[0]({ok:true, status:200, payload:{buckets:[{
    id:'old', name:'stale response', content:'old body', type:'dynamic',
    domain:[], tags:[], importance:5,
  }]}});
  await oldRequest;
  process.stdout.write(JSON.stringify([
    container.innerHTML.includes('fresh response'),
    container.innerHTML.includes('stale response'),
    container.scrollTop,
  ]));
})().catch(function(error) {
  console.error(error);
  process.exit(1);
});
"""
    completed = subprocess.run(
        [shutil.which("node"), "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == [True, False, 73]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is unavailable")
def test_bucket_detail_latest_request_wins_at_runtime():
    html = DASHBOARD.read_text(encoding="utf-8")
    start = html.index("let detailLoadGeneration = 0;")
    end = html.index("async function bucketPin(", start)
    source = html[start:end]
    script = """
const pending = [];
const panel = {classList:{add() {}, toggle() {}}};
const content = {innerHTML:''};
const document = {
  getElementById(id) {
    if (id === 'detail-panel') return panel;
    if (id === 'detail-content') return content;
    return null;
  },
};
const BASE = '';
function fetch(url) {
  return new Promise(resolve => pending.push({url, resolve}));
}
async function readJsonSafe(response) { return response.payload; }
function esc(value) { return String(value == null ? '' : value); }
""" + source + """
(async function() {
  const oldRequest = showDetail('old/id');
  const newRequest = showDetail('new/id');
  pending[1].resolve({ok:false, status:404, payload:{error:'new failure'}});
  const newResult = await newRequest;
  const afterNew = content.innerHTML;
  pending[0].resolve({ok:false, status:404, payload:{error:'stale failure'}});
  const oldResult = await oldRequest;
  process.stdout.write(JSON.stringify([
    pending.map(item => item.url), newResult, oldResult,
    afterNew.includes('new failure'),
    content.innerHTML.includes('new failure'),
    content.innerHTML.includes('stale failure'),
  ]));
})().catch(function(error) {
  console.error(error);
  process.exit(1);
});
"""
    completed = subprocess.run(
        [shutil.which("node"), "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == [
        ["/api/bucket/old%2Fid", "/api/bucket/new%2Fid"],
        False,
        False,
        True,
        True,
        False,
    ]
