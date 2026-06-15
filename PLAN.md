# Migration Plan: desktop-ui (Tauri) → web-ui (Pure React Web App)

## Goal
Chuyển desktop UI từ Tauri v2 desktop app sang pure Vite + React web app để dễ bảo trì, deploy và scale.

## Background
- `desktop-ui/` hiện dùng Tauri v2 (Rust backend + WebView frontend)
- Chỉ có 4 files phụ thuộc native API: `logger.ts`, `downloadUtils.ts`, `useAADownloadFolder.ts`, `TTSPage.tsx`
- `MailboxPage.tsx` có workaround cho Tauri webview iframe
- Tất cả API calls đều qua HTTP fetch/WebSocket → web-compatible sẵn
- `package.json` có `@tauri-apps/*` dependencies và scripts `tauri`

## Target Architecture
- `web-ui/` folder mới, copy reusable code từ `desktop-ui/`
- Pure **Vite 5 + React 18 + TypeScript 5 + Tailwind CSS v3 + React Router v6**
- Không có Rust backend, không có `@tauri-apps` plugins
- Serve static build qua nginx/caddy container trong `docker-compose.yml`
- API origin lấy từ window.location (same-origin qua Traefik) hoặc env var

## Detailed Steps

### Phase 1: Scaffold & Cleanup
1. Tạo `web-ui/` copy từ `desktop-ui/`
2. Xóa `src-tauri/` (toàn bộ Rust code)
3. Xóa `node_modules/`, `package-lock.json`
4. Cập nhật `package.json`:
   - Bỏ `@tauri-apps/api`, `@tauri-apps/cli`, `@tauri-apps/plugin-dialog`, `@tauri-apps/plugin-fs`, `@tauri-apps/plugin-opener`
   - Bỏ scripts `"tauri": "tauri"`
   - Giữ lại react, react-dom, react-router-dom, tailwindcss, vite, vitest, playwright, typescript, yaml, @sentry/react
5. `npm install`

### Phase 2: Rewrite Native-Dependent Modules
6. **Rewrite `src/lib/logger.ts`**:
   - Bỏ Tauri fs imports (`@tauri-apps/plugin-fs`, `@tauri-apps/api/path`)
   - Chỉ giữ console logging
   - Giữ `initErrorHandler()` với `window.addEventListener` (web compatible)
7. **Rewrite `src/pages/ArtificialAnalysis/downloadUtils.ts`**:
   - Bỏ `save` dialog và `writeFile`
   - Dùng browser download: tạo Blob URL + `<a download>` trigger click
   - `buildFilename()` giữ nguyên logic
8. **Rewrite `src/pages/ArtificialAnalysis/useAADownloadFolder.ts`**:
   - Bỏ `open` dialog (`@tauri-apps/plugin-dialog`)
   - Vì web không có native folder picker → auto download qua browser default
   - Bỏ `downloadFolder` state hoặc chuyển thành text input metadata (không dùng để write file)
9. **Rewrite `src/pages/TTSPage.tsx`**:
   - Bỏ `open` dialog + `writeFile`
   - Auto download dùng browser Blob URL (`<a download>`)
   - Bỏ UI chọn thư mục lưu, thay bằng nút Download bình thường
10. **Cập nhật `src/pages/MailboxPage.tsx`**:
    - Bỏ comment "srcDoc doesn't work in Tauri webview"
    - Dùng `srcDoc` hoặc blob URL bình thường (web không bị giới hạn này)

### Phase 3: Config Updates
11. **Cập nhật `vite.config.ts`**:
    - Bỏ `envPrefix: ["VITE_", "TAURI_"]` → chỉ `"VITE_"`
    - Giữ `target: "chrome105"` (web compatible)
    - Giữ test config, coverage thresholds
12. **Cập nhật `main.tsx`**:
    - Bỏ Tauri-specific init (nếu có)
    - Giữ `React.StrictMode` + `BrowserRouter`
13. **Cập nhật `src/config.ts`**:
    - `API_BASE_URL` dùng relative path `"/api/v1"` nếu serve cùng domain qua Traefik
    - `TTS_BASE_URL` tương tự `"/tts"` hoặc giữ nguyên `"http://localhost:8700"` cho dev standalone
14. **Tạo `web-ui/Dockerfile`**:
    - Multi-stage: `node:20-alpine` build → `nginx:alpine` serve static `dist/`
    - Copy `nginx.conf` để handle SPA fallback (try_files $uri /index.html)

### Phase 4: Docker Integration
15. **Cập nhật `docker-compose.yml`**:
    - Thêm service `web-ui` image từ `web-ui/Dockerfile`
    - Không expose port trực tiếp (qua Traefik)
    - Labels Traefik để route `Host(`localhost`)` hoặc path prefix
16. **Cập nhật `traefik/traefik.yml`** nếu cần thêm middleware/routing rule
17. **Smoke test**: `docker compose up web-ui`, verify UI load được từ browser

### Phase 5: Build & Verify
18. Build: `npm run build` trong `web-ui/`
19. Verify bundle: grep đảm bảo không còn `@tauri-apps` trong output
20. Run unit tests: `npm run test`
21. Smoke check mở trang, verify:
    - API calls: accounts list, jobs create
    - WebSocket `/jobs/{id}/logs` stream
    - Download image/audio qua browser

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Folder picker không có trên web | Dùng browser download default, bỏ auto-save vào specific folder |
| File write không có trên web | Dùng Blob URL + `<a download>` trigger |
| CORS khi serve web UI khác domain | Serve qua same-origin qua Traefik reverse proxy |
| Tauri-specific performance optimizations lost | Không đáng kể, web app modern đủ nhanh |
| iframe srcDoc Tauri workaround | Web hỗ trợ srcDoc bình thường, bỏ workaround |

## Success Criteria
- [ ] `npm run build` thành công, output trong `dist/`
- [ ] Không có import `@tauri-apps` trong toàn bộ `web-ui/src/`
- [ ] Không có `src-tauri/` folder
- [ ] UI load được trong browser (không qua Tauri)
- [ ] API calls hoạt động (accounts, jobs, config)
- [ ] WebSocket logs stream hoạt động
- [ ] Download image/audio hoạt động qua browser
- [ ] `docker compose up` bao gồm web-ui service chạy ổn định

## Notes
- Giữ nguyên tất cả pages, components, hooks, api client, styles, tests
- Chỉ thay đổi những chỗ Tauri-specific
- `BrowserRouter` vẫn hoạt động vì là SPA serve từ static file server
