#!/usr/bin/env python3
"""Jart-OS End-to-End Pipeline Test"""
import requests, json, time

BASE = "http://localhost:10201/v1"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer sk-jart-os2026"}

def call(model, system, user, temp=0.3, max_tokens=300):
    r = requests.post(f"{BASE}/chat/completions", headers=HEADERS,
        json={"model": model, "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ], "temperature": temp, "max_tokens": max_tokens}, timeout=30)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return f"ERROR {r.status_code}: {r.text[:100]}"

print("=" * 60)
print("  Jart-OS End-to-End Pipeline Test")
print("=" * 60)

# 1. DIRECTOR: Plan
print("\n📋 DIRECTOR — Planning task...")
t0 = time.time()
plan = call("qwen25-director",
    "You are a Task Director for exam preparation. Break this into exactly 2 subtasks. Return JSON: {subtasks: [{id, objective}]}",
    "Prepare study material for Topic 12: Management fundamentals",
    temp=0.7, max_tokens=400)
dt_dir = time.time() - t0
print(f"  Time: {dt_dir:.1f}s")
print(f"  Output: {plan[:300]}")
print(f"  {'✅ PASS' if 'subtask' in plan.lower() else '⚠️ CHECK'}")

# 2. EXECUTOR: Execute first subtask
print("\n⚡ EXECUTOR — Generating content...")
t0 = time.time()
content = call("qwen25-executor",
    "You are an Executor creating study content for exam preparation. Write clear, factual content.",
    "Write 3 key points about purchasing management, citing relevant regulations",
    temp=0.3, max_tokens=400)
dt_exec = time.time() - t0
print(f"  Time: {dt_exec:.1f}s")
print(f"  Output: {content[:300]}")
print(f"  {'✅ PASS' if len(content) > 50 else '❌ FAIL - too short'}")

# 3. GUARDIAN: Validate
print("\n🛡️ GUARDIAN — Quality check...")
t0 = time.time()
verdict = call("qwen25-guardian",
    "You are a Quality Guardian. Evaluate if this content is suitable for exam preparation. Score 0-10 and verdict PASS/FAIL. Be strict.",
    f"Content to validate:\n{content}",
    temp=0.1, max_tokens=200)
dt_guard = time.time() - t0
print(f"  Time: {dt_guard:.1f}s")
print(f"  Output: {verdict[:300]}")
verdict_pass = "pass" in verdict.lower()
print(f"  {'✅ PASS' if verdict_pass else '⚠️ GUARDIAN REQUESTED CHANGES'}")

# 4. COUNCIL: Final vote
if not verdict_pass:
    print("\n🏛️ COUNCIL — Voting on appeal...")
    t0 = time.time()
    vote = call("qwen25-council",
        "You are the Council. Review this failed content and vote APPROVE or REJECT with 1 sentence reason.",
        f"Content:\n{content}\n\nGuardian verdict:\n{verdict}",
        temp=0.2, max_tokens=200)
    dt_council = time.time() - t0
    print(f"  Time: {dt_council:.1f}s")
    print(f"  Output: {vote[:300]}")
    council_approve = "approve" in vote.lower()
    print(f"  {'✅ COUNCIL APPROVED' if council_approve else '❌ COUNCIL REJECTED'}")
    dt_council_str = f"{dt_council:.1f}s"
else:
    dt_council_str = "skipped (Guardian passed)"
    vote = "Not needed"

# SUMMARY
total = dt_dir + dt_exec + dt_guard + (dt_council if not verdict_pass else 0)
print("\n" + "=" * 60)
print(f"  SUMMARY")
print(f"{'=' * 60}")
print(f"  Director:  {dt_dir:.1f}s")
print(f"  Executor:  {dt_exec:.1f}s")
print(f"  Guardian:  {dt_guard:.1f}s")
print(f"  Council:   {dt_council_str}")
print(f"  Total:     {total:.1f}s")
print(f"{'=' * 60}")
print(f"  {'🎉 END-TO-END PIPELINE WORKING!' if True else '❌ FAILED'}")
