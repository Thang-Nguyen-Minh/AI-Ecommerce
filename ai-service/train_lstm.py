"""
Train LSTM next-item từ behavior store, lưu snapshot ai_data/lstm/model.pt.
Chạy: docker exec ecom-ai-service python train_lstm.py
"""
import os

import torch
import torch.nn as nn

from app import db
from app.config import LSTM_DIR
from app.lstm_model import MODEL_PATH, build_model

torch.manual_seed(42)
EMB, HIDDEN, EPOCHS, MAXLEN = 64, 128, 40, 20


def main():
    seqs = [s for s in db.ordered_sequences().values() if len(s) >= 2]
    if not seqs:
        print("Không đủ dữ liệu — hãy seed behavior trước.")
        return

    vocab_ids = sorted({pid for s in seqs for pid in s})
    id2idx = {pid: i for i, pid in enumerate(vocab_ids)}
    idx2id = vocab_ids
    V = len(vocab_ids)

    # Mẫu (prefix → next item)
    samples = []
    for s in seqs:
        idx = [id2idx[p] for p in s]
        for i in range(1, len(idx)):
            samples.append((idx[max(0, i - MAXLEN):i], idx[i]))
    print(f"vocab={V}, sequences={len(seqs)}, samples={len(samples)}")

    model = build_model(V, EMB, HIDDEN)
    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.CrossEntropyLoss()

    model.train()
    for ep in range(EPOCHS):
        total = 0.0
        for prefix, target in samples:
            x = torch.tensor([prefix], dtype=torch.long)
            y = torch.tensor([target], dtype=torch.long)
            opt.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            total += loss.item()
        if ep % 5 == 0 or ep == EPOCHS - 1:
            print(f"  epoch {ep:02d}  loss={total / len(samples):.4f}")

    os.makedirs(LSTM_DIR, exist_ok=True)
    torch.save({
        "state": model.state_dict(), "vocab": V, "emb": EMB, "hidden": HIDDEN,
        "id2idx": id2idx, "idx2id": idx2id,
    }, MODEL_PATH)
    print(f"✅ Đã lưu snapshot: {MODEL_PATH}")

    # Sanity: dự đoán cho 1 chuỗi gaming
    model.eval()
    sample_seq = seqs[0][-MAXLEN:]
    x = torch.tensor([[id2idx[p] for p in sample_seq]], dtype=torch.long)
    with torch.no_grad():
        top = torch.topk(torch.softmax(model(x)[0], -1), 5).indices.tolist()
    print("Sanity — chuỗi mẫu:", sample_seq[-5:], "→ next top5 product_id:", [idx2id[i] for i in top])


if __name__ == "__main__":
    main()
