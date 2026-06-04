"""
LSTM next-item predictor (GĐ2 thật).
Inference: load snapshot đóng băng (eval → xác định, BR-5); thiếu snapshot/torch lỗi → [] (fallback).
Train: xem train_lstm.py.
"""
import logging
import os

from .config import LSTM_DIR

logger = logging.getLogger("ai.lstm")

MODEL_PATH = os.path.join(LSTM_DIR, "model.pt")

_model = None
_meta = None


def build_model(vocab, emb=64, hidden=128):
    import torch.nn as nn

    class NextItemLSTM(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(vocab, emb)
            self.lstm = nn.LSTM(emb, hidden, batch_first=True)
            self.fc = nn.Linear(hidden, vocab)

        def forward(self, x):              # x: (batch, seq)
            e = self.emb(x)
            out, _ = self.lstm(e)
            return self.fc(out[:, -1, :])  # logits cho item kế tiếp

    return NextItemLSTM()


def _load():
    global _model, _meta
    if _model is not None:
        return True
    if not os.path.exists(MODEL_PATH):
        return False
    try:
        import torch
        ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
        m = build_model(ckpt["vocab"], ckpt["emb"], ckpt["hidden"])
        m.load_state_dict(ckpt["state"])
        m.eval()                          # BR-5: xác định, không dropout/online
        _model, _meta = m, ckpt
        logger.info(f"LSTM snapshot loaded (vocab={ckpt['vocab']})")
        return True
    except Exception as e:
        logger.warning(f"LSTM load error: {e}")
        return False


def available():
    return _load()


def predict_next(recent_ids, k=10, exclude=()):
    """recent_ids: chuỗi product_id chronological (cũ→mới). Trả [(product_id, prob)]."""
    if not _load() or not recent_ids:
        return []
    try:
        import torch
        id2idx, idx2id = _meta["id2idx"], _meta["idx2id"]
        seq = [id2idx[p] for p in recent_ids if p in id2idx]
        if not seq:
            return []
        x = torch.tensor([seq[-20:]], dtype=torch.long)
        with torch.no_grad():
            probs = torch.softmax(_model(x)[0], dim=-1)
        order = torch.argsort(probs, descending=True).tolist()
        ex = set(exclude)
        out = []
        for idx in order:
            pid = idx2id[idx]
            if pid in ex:
                continue
            out.append((pid, float(probs[idx])))
            if len(out) >= k:
                break
        return out
    except Exception as e:
        logger.warning(f"LSTM predict error: {e}")
        return []
