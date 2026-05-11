# P0 Enterprise Drift Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the highest-confidence documentation/code/contract drift that blocks the workspace from being a trustworthy enterprise orchestration repo.

**Architecture:** This P0 pass does not introduce GitOps, SOPS, Flyway, or a full observability stack. It makes the existing root-orchestration model honest and enforceable: internal API client behavior must match the documented contract, stale service-local port docs must point readers to root runtime truth, and exit-review claims must distinguish completed root remediation from future platform-hardening designs.

**Tech Stack:** Python 3.12, pytest, GitHub Actions, Docker Compose, Markdown docs.

---

## File Structure

- Modify `common/src/common/internal_client.py`: make `InternalClient.list_accounts()` unwrap either the documented paginated `data.accounts` shape or a legacy direct list shape.
- Modify `registrar/tests/unit/test_internal_client.py`: add unit tests for paginated and legacy list response shapes.
- Modify service docs with stale runtime ports:
  - `registrar/README.md`
  - `registrar/docs/README.md`
  - `registrar/docs/api-reference.md`
  - `registrar/docs/architecture.md`
  - `mail-service/README.md`
  - `aa-proxy/README.md`
  - `tts-proxy/README.md`
- Modify `docs/superpowers/audits/enterprise-exit-review-2026-05-02.md`: rescope the score to what is actually enforceable in this checkout.
- Run `python .github/scripts/validate_runtime_truth.py` after docs changes.
- Run `pytest registrar/tests/unit/test_internal_client.py -q` after client/test changes.

## Task 1: Fix internal client list contract

**Files:**
- Modify: `common/src/common/internal_client.py`
- Modify: `registrar/tests/unit/test_internal_client.py`

- [ ] **Step 1: Add failing tests for list response shapes**

Add these tests to `registrar/tests/unit/test_internal_client.py` inside `class TestInternalClient`:

```python
    @pytest.mark.asyncio
    async def test_list_accounts_unwraps_paginated_contract(self):
        from common.internal_client import InternalClient
        async with InternalClient() as client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "data": {
                    "accounts": [{"email": "a@test.com"}],
                    "total": 1,
                    "page": 1,
                    "limit": 100,
                    "pages": 1,
                }
            }
            client._client.get = AsyncMock(return_value=mock_resp)

            result = await client.list_accounts("TEST")
            assert result == [{"email": "a@test.com"}]

    @pytest.mark.asyncio
    async def test_list_accounts_accepts_legacy_direct_list(self):
        from common.internal_client import InternalClient
        async with InternalClient() as client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"data": [{"email": "legacy@test.com"}]}
            client._client.get = AsyncMock(return_value=mock_resp)

            result = await client.list_accounts()
            assert result == [{"email": "legacy@test.com"}]
```

- [ ] **Step 2: Run the focused tests and confirm the first test fails**

Run:

```powershell
pytest registrar/tests/unit/test_internal_client.py -q
```

Expected before implementation: `test_list_accounts_unwraps_paginated_contract` fails because `list_accounts()` returns the full `data` dict.

- [ ] **Step 3: Implement the minimal client fix**

Replace the body after `resp.raise_for_status()` in `InternalClient.list_accounts()` with:

```python
            data = resp.json()["data"] or []
            if isinstance(data, dict):
                return data.get("accounts", [])
            return data
```

- [ ] **Step 4: Re-run focused tests**

Run:

```powershell
pytest registrar/tests/unit/test_internal_client.py -q
```

Expected: all tests in that file pass.

- [ ] **Step 5: Commit**

```powershell
git add common/src/common/internal_client.py registrar/tests/unit/test_internal_client.py
git commit -m "fix: align internal account list client contract"
```

## Task 2: Mark stale service-local runtime docs and point to root truth

**Files:**
- Modify: `registrar/README.md`
- Modify: `registrar/docs/README.md`
- Modify: `registrar/docs/api-reference.md`
- Modify: `registrar/docs/architecture.md`
- Modify: `mail-service/README.md`
- Modify: `aa-proxy/README.md`
- Modify: `tts-proxy/README.md`

- [ ] **Step 1: Add root-truth note to service docs that mention stale ports**

Use short notes, for example:

```markdown
> Runtime note: root orchestration publishes this service on port `8709`. Older service-local examples that mention `8799` are legacy local-dev references and must not be used as platform runtime truth.
```

Use service-specific ports:

- registrar: root port `8709`, stale `8799`
- mail-service: root port `8701`, stale `8801`
- aa-proxy: root port `8702`, stale `8802`
- tts-proxy: root port `8700`, stale `8800`

- [ ] **Step 2: Keep local-dev examples intact only if clearly labeled legacy/local**

Do not rewrite endpoint tables wholesale. Add or adjust the nearby text so a reader understands root docs are canonical for platform orchestration.

- [ ] **Step 3: Validate root runtime docs still pass**

Run:

```powershell
python .github/scripts/validate_runtime_truth.py
```

Expected: `Runtime truth validation passed.`

- [ ] **Step 4: Commit**

```powershell
git add registrar/README.md registrar/docs/README.md registrar/docs/api-reference.md registrar/docs/architecture.md mail-service/README.md aa-proxy/README.md tts-proxy/README.md
git commit -m "docs: mark stale service-local runtime ports"
```

## Task 3: Correct enterprise exit-review scope

**Files:**
- Modify: `docs/superpowers/audits/enterprise-exit-review-2026-05-02.md`

- [ ] **Step 1: Rewrite the score/residual-risk language**

Keep the historical evidence, but make the conclusion accurate for this checkout:

- root orchestration boundary remains `10/10`
- full platform is `post-remediation baseline`, not fully GitOps/prod-ready
- SOPS/AGE, Flyway, full observability stack, full service CI matrix, and shared `common.config` are future platform-hardening work unless implemented in artifact form
- note the remaining `common.context` type-only service references as boundary cleanup debt

- [ ] **Step 2: Validate docs consistency**

Run:

```powershell
python .github/scripts/validate_runtime_truth.py
```

Expected: `Runtime truth validation passed.`

- [ ] **Step 3: Commit**

```powershell
git add docs/superpowers/audits/enterprise-exit-review-2026-05-02.md
git commit -m "docs: clarify enterprise remediation exit scope"
```

## Task 4: Final P0 verification

**Files:**
- No new source edits expected.

- [ ] **Step 1: Run focused unit tests**

```powershell
pytest registrar/tests/unit/test_internal_client.py -q
```

Expected: pass.

- [ ] **Step 2: Run root runtime validator**

```powershell
python .github/scripts/validate_runtime_truth.py
```

Expected: `Runtime truth validation passed.`

- [ ] **Step 3: Inspect git status**

```powershell
git status --short
```

Expected: clean after commits.

## Self-Review

- Spec coverage: covers P0 drift fix, stale docs cleanup, and exit-review honesty. It explicitly excludes GitOps/SOPS/Flyway/observability implementation for this pass.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: `list_accounts()` remains `list[dict[str, Any]]`; both response shapes return lists.
