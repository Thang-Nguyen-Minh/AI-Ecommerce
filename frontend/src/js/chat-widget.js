/**
 * Floating chatbot widget — nhúng vào bất kỳ trang nào bằng 1 dòng script.
 * Hoạt động cả khi chưa đăng nhập (guest) lẫn đã đăng nhập (dùng token).
 */
(function () {
    const AI_URL = 'http://localhost:8007';
    const PRODUCT_URL = 'http://localhost:8002';

    // ── Inject CSS ──────────────────────────────────────────────────
    const style = document.createElement('style');
    style.textContent = `
#cw-wrap { position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; flex-direction:column; align-items:flex-end; gap:12px; }
#cw-panel {
    width:360px; height:500px; background:#fff; border-radius:16px;
    box-shadow:0 8px 40px rgba(0,0,0,0.18); display:none; flex-direction:column; overflow:hidden;
}
#cw-panel.open { display:flex; }
#cw-header {
    background:linear-gradient(135deg,#667eea,#764ba2); color:#fff;
    padding:14px 16px; display:flex; justify-content:space-between; align-items:center; flex-shrink:0;
}
#cw-header span { font-weight:600; font-size:.95rem; }
#cw-close { background:none; border:none; color:#fff; font-size:1.1rem; cursor:pointer; padding:0 2px; line-height:1; }
#cw-messages { flex:1; overflow-y:auto; padding:12px; background:#f8f9fa; display:flex; flex-direction:column; gap:8px; }
.cw-msg { max-width:82%; padding:9px 13px; border-radius:14px; font-size:.875rem; line-height:1.4; word-break:break-word; }
.cw-user { background:#667eea; color:#fff; align-self:flex-end; border-bottom-right-radius:4px; }
.cw-bot  { background:#fff; border:1px solid #e5e7eb; align-self:flex-start; border-bottom-left-radius:4px; }
.cw-typing { color:#999; font-style:italic; }
#cw-sugg { display:flex; flex-wrap:wrap; gap:6px; padding:0 12px 8px; flex-shrink:0; }
.cw-sugg-chip {
    background:#f3f4ff; border:1px solid #c7d0ff; border-radius:20px;
    padding:4px 10px; font-size:.78rem; cursor:pointer; white-space:nowrap;
    transition:background .15s;
}
.cw-sugg-chip:hover { background:#667eea; color:#fff; border-color:#667eea; }
#cw-footer { padding:10px 12px; border-top:1px solid #e5e7eb; flex-shrink:0; }
#cw-form { display:flex; gap:8px; }
#cw-input { flex:1; border:1px solid #d1d5db; border-radius:20px; padding:7px 14px; font-size:.875rem; outline:none; }
#cw-input:focus { border-color:#667eea; }
#cw-send {
    width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#667eea,#764ba2);
    border:none; color:#fff; cursor:pointer; display:flex; align-items:center; justify-content:center;
    flex-shrink:0; font-size:.85rem;
}
#cw-send:disabled { opacity:.5; cursor:default; }
#cw-btn {
    width:56px; height:56px; border-radius:50%;
    background:linear-gradient(135deg,#667eea,#764ba2);
    border:none; color:#fff; font-size:1.3rem; cursor:pointer;
    box-shadow:0 4px 20px rgba(102,126,234,.55);
    display:flex; align-items:center; justify-content:center;
    transition:transform .2s;
}
#cw-btn:hover { transform:scale(1.08); }
#cw-badge {
    position:absolute; top:-4px; right:-4px; width:12px; height:12px;
    background:#ef4444; border-radius:50%; border:2px solid #fff; display:none;
}
    `;
    document.head.appendChild(style);

    // ── Inject HTML ─────────────────────────────────────────────────
    const wrap = document.createElement('div');
    wrap.id = 'cw-wrap';
    wrap.innerHTML = `
        <div id="cw-panel">
            <div id="cw-header">
                <span><i class="fas fa-robot me-2"></i>Trợ lý mua sắm AI</span>
                <button id="cw-close" title="Đóng"><i class="fas fa-times"></i></button>
            </div>
            <div id="cw-messages"></div>
            <div id="cw-sugg"></div>
            <div id="cw-footer">
                <form id="cw-form">
                    <input id="cw-input" type="text" placeholder="Hỏi về sản phẩm..." autocomplete="off">
                    <button id="cw-send" type="submit"><i class="fas fa-paper-plane"></i></button>
                </form>
            </div>
        </div>
        <div style="position:relative">
            <button id="cw-btn" title="Chat với AI"><i class="fas fa-comments"></i></button>
            <span id="cw-badge"></span>
        </div>
    `;
    document.body.appendChild(wrap);

    // ── State & helpers ─────────────────────────────────────────────
    const panel    = document.getElementById('cw-panel');
    const messages = document.getElementById('cw-messages');
    const suggBox  = document.getElementById('cw-sugg');
    const input    = document.getElementById('cw-input');
    const sendBtn  = document.getElementById('cw-send');
    const badge    = document.getElementById('cw-badge');
    let opened = false;

    function getToken() {
        return localStorage.getItem('access_token') || '';
    }

    function toggle() {
        opened = !opened;
        panel.classList.toggle('open', opened);
        badge.style.display = 'none';
        if (opened && messages.children.length === 0) {
            addMsg('Xin chào! Mình có thể giúp bạn tìm sản phẩm. Bạn đang cần gì?', 'bot');
        }
        if (opened) input.focus();
    }

    function addMsg(text, who) {
        const d = document.createElement('div');
        d.className = `cw-msg cw-${who}`;
        d.textContent = text;
        messages.appendChild(d);
        messages.scrollTop = messages.scrollHeight;
        return d;
    }

    function clearSugg() {
        suggBox.innerHTML = '';
    }

    async function showSugg(ids) {
        clearSugg();
        if (!ids || !ids.length) return;
        const items = await Promise.all(
            ids.slice(0, 4).map(id =>
                fetch(`${PRODUCT_URL}/products/${id}/`).then(r => r.ok ? r.json() : null).catch(() => null)
            )
        );
        items.filter(Boolean).forEach(p => {
            const chip = document.createElement('span');
            chip.className = 'cw-sugg-chip';
            chip.textContent = p.name;
            chip.onclick = () => { window.location.href = `product-detail.html?id=${p.id}`; };
            suggBox.appendChild(chip);
        });
    }

    async function send(text) {
        if (!text.trim()) return;
        clearSugg();
        addMsg(text, 'user');
        input.value = '';
        sendBtn.disabled = true;

        const typing = addMsg('Đang soạn...', 'bot');
        typing.classList.add('cw-typing');

        try {
            const headers = { 'Content-Type': 'application/json' };
            const token = getToken();
            if (token) headers['Authorization'] = `Bearer ${token}`;

            const res = await fetch(`${AI_URL}/chatbot`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ message: text }),
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            typing.textContent = data.reply || 'Mình chưa có câu trả lời phù hợp.';
            typing.classList.remove('cw-typing');
            await showSugg(data.suggested);
        } catch (e) {
            typing.textContent = 'Hệ thống tư vấn tạm bận, bạn thử lại sau nhé.';
            typing.classList.remove('cw-typing');
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    }

    // ── Event listeners ─────────────────────────────────────────────
    document.getElementById('cw-btn').addEventListener('click', toggle);
    document.getElementById('cw-close').addEventListener('click', toggle);
    document.getElementById('cw-form').addEventListener('submit', e => {
        e.preventDefault();
        send(input.value.trim());
    });

    // Hiển thị badge khi widget chưa mở sau 3s
    setTimeout(() => {
        if (!opened) badge.style.display = 'block';
    }, 3000);
})();
