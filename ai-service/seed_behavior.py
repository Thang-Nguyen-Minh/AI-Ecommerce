"""
Seed knowledge base qua PIPELINE THẬT (plan_seed_knowledge_base.md):
- Tạo ~50 tài khoản qua /auth/register/ (form mới: full_name, phone unique, occupation).
- Mỗi tài khoản gửi 12-18 event qua POST /events theo persona (cụm sản phẩm thật).
Chạy trong container ai-service:  docker exec ecom-ai-service python seed_behavior.py
"""
import random
import sys

import requests

BASE_USER = "http://user-service:8000"
BASE_AI = "http://localhost:8000"
BASE_PRODUCT = "http://product-service:8000"
PASSWORD = "Pass123!"

random.seed(42)


def product_ids_by_type():
    by = {"book": [], "electronics": [], "fashion": []}
    for t in by:
        page = 1
        while True:
            r = requests.get(f"{BASE_PRODUCT}/products/?product_type={t}&page={page}", timeout=10)
            if r.status_code != 200:
                break
            d = r.json()
            by[t] += [p["id"] for p in d.get("results", [])]
            if not d.get("next"):
                break
            page += 1
    return by


PERSONAS = (
    [("gaming", "electronics", "Game thủ")] * 18
    + [("study", "book", "Sinh viên")] * 18
    + [("fashion", "fashion", "Nhân viên thời trang")] * 14
)  # = 50


def register_and_login(email, full_name, phone, occupation):
    requests.post(f"{BASE_USER}/auth/register/", json={
        "email": email, "password": PASSWORD, "full_name": full_name,
        "phone": phone, "occupation": occupation,
        "address": "Khu seed, Ha Noi",
    }, timeout=10)  # 400 nếu đã tồn tại — bỏ qua, vẫn login
    r = requests.post(f"{BASE_USER}/auth/login/", json={"email": email, "password": PASSWORD}, timeout=10)
    if r.status_code != 200:
        return None
    return r.json().get("access")


def main():
    by = product_ids_by_type()
    popular = (by["electronics"][:1] + by["book"][:1])  # vài món phổ biến chéo cụm
    all_ids = by["book"] + by["electronics"] + by["fashion"]
    if not all_ids:
        print("Không có sản phẩm — hãy seed catalog trước.")
        sys.exit(1)

    total_events = 0
    accounts = []
    for i, (persona, cluster, occ) in enumerate(PERSONAS):
        email = f"user{i:02d}@seed.local"
        phone = f"09{50000000 + i}"  # unique
        token = register_and_login(email, f"Seed {persona.title()} {i:02d}", phone, occ)
        if not token:
            print(f"  ! login fail {email}")
            continue
        accounts.append((email, persona, occ))
        headers = {"Authorization": f"Bearer {token}"}
        items = by[cluster] or all_ids
        n_events = random.randint(12, 18)
        for _ in range(n_events):
            r = random.random()
            if r < 0.80:
                pid = random.choice(items)
            elif r < 0.95 and popular:
                pid = random.choice(popular)
            else:
                pid = random.choice(all_ids)
            action = random.choices(["view", "click", "add_to_cart"], weights=[6, 3, 1])[0]
            resp = requests.post(f"{BASE_AI}/events", headers=headers,
                                 json={"product_id": pid, "action": action}, timeout=10)
            if resp.status_code == 201:
                total_events += 1

    print(f"\n✅ Seed xong: {len(accounts)} tài khoản, {total_events} events.")
    print("Mật khẩu chung:", PASSWORD)
    by_persona = {}
    for email, persona, occ in accounts:
        by_persona.setdefault(persona, []).append(email)
    for persona, emails in by_persona.items():
        print(f"\n[{persona}] ({len(emails)} tài khoản):")
        for e in emails:
            print("  ", e)


if __name__ == "__main__":
    main()
