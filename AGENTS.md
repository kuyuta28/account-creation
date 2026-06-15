# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.


- Code luôn dùng functional programming style, tránh sử dụng OOP nếu không cần thiết.
- Sử dụng các thư viện hỗ trợ functional programming để viết code ngắn gọn, dễ đọc và dễ bảo trì.
- Luôn áp dụng các design patterns phù hợp với functional programming, cộng với các best practices để đảm bảo code của bạn luôn sạch sẽ và dễ hiểu.
- Luôn tách file thành các module nhỏ, mỗi module chỉ có một trách nhiệm duy nhất để tăng tính tái sử dụng và dễ bảo trì.
- Sử dụng các công cụ kiểm tra code như ESLint, Prettier để đảm bảo code của bạn luôn tuân thủ các quy tắc và chuẩn mực đã đề ra.
- Luôn viết unit tests cho code của bạn để đảm bảo tính đúng đắn và dễ dàng phát hiện lỗi khi có thay đổi.
- Luôn sử dụng các thư viện có sẵn để giải quyết các vấn đề phổ biến thay vì tự viết lại từ đầu, giúp tiết kiệm thời gian và tăng tính ổn định của code.

## Quy trình BẮT BUỘC khi viết service mới (registrar)

Khi thêm service mới vào `src/services/`, **PHẢI** làm theo thứ tự sau TRƯỚC KHI viết code:

1. **Dùng Playwright lấy HTML rendered** — KHÔNG dùng `requests.get()` vì nhiều web render client-side (Next.js, React...).
2. **Dump & phân tích DOM** — liệt kê tất cả `<button>`, `<input>`, tab, dialog. Xác định chính xác element nào cần tương tác.
3. **Xác định thứ tự tương tác** — nhiều trang có button trùng tên hoặc OAuth button nằm trước trong DOM (ví dụ: "Continue with Google" trước "Continue →").
4. **Code dựa trên DOM thực tế** — không đoán, không giả định cấu trúc trang.
5. **Dump HTML sau mỗi action** (`logger.dump_html()`) để verify.

### Lưu ý quan trọng:
- Cấm HARDCODE toàn bộ 

- CẤM CODE FALLBACK KHI MÀ TAO KHÔNG CHỈ RA, NGHE CHO RÕ CHƯA, CẤM CODE BẤT KỲ HƯỚNG FALLBACK NÀO, FLOW ĐÉO ĐÚNG HƯỚNG THÌ NÉM LỖI, CẤM FALLBACK

- CẤM NUỐT LỖI
- CẤM CODE BLOCKING, ĐỒNG BỘ, PHẢI CODE NON-BLOCKING, ASYNC, VÀ NHỮNG TÍNH NĂNG NÀO CÓ THỂ CHẠY CONCURRENT ĐƯỢC THÌ PHẢI CHẠY CONCURRENT, KHÔNG ĐƯỢC CHẠY SEQUENTIAL, KHÔNG ĐƯỢC CHẠY BLOCKING

- NGHIÊM CẤM GIẢI QUYẾT VẤN ĐỀ THEO HƯỚNG VÁ LỖI NGẮN HẠN, NẾU CODE HIỆN TẠI LOGIC HỆ THỐNG, CÁCH XỬ LÝ SAI TỪ ĐẦU, HOÀN TOÀN CÓ THỂ ĐẬP ĐI XÂY LẠI, HÃY NGHĨ THEO HƯỚNG ENTERPRISE SCALE, NGHĨ THEO HƯỚNG SẢN PHẨM CÓ THỂ MỞ RỘNG VÀ BỀN VỮNG TRONG NHIỀU NĂM, ĐỪNG NGHĨ THEO HƯỚNG GIẢI QUYẾT VẤN ĐỀ NHANH CHÓNG, TẠM THỜI, HAY TẠM ỔN, HÃY NGHĨ THEO HƯỚNG GIẢI QUYẾT VẤN ĐỀ MỘT CÁCH BỀN VỮNG, DÙ CÓ THỂ PHỨC TẠP HƠN, KHÓ VIẾT HƠN, NHƯNG LẠI GIẢI QUYẾT VẤN ĐỀ MỘT CÁCH TOÀN DIỆN, HOÀN CHỈNH, VÀ BỀN VỮNG TRONG NHIỀU NĂM.