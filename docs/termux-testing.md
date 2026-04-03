# Mobile / Termux Testing Guide

This guide covers testing Agent Reach on Android devices using Termux.

## Install

```bash
pkg update && pkg install python git
pip install https://github.com/YOUR_FORK/agent-reach/archive/main.zip
agent-reach install --env=auto
```

## Test Each Tier Manually

### Tier 1 - Jina (should work instantly)

```bash
agent-reach fetch https://example.com
```

### Tier 2 - Scrapling basic (no browser)

```bash
agent-reach fetch https://example.com --mode=scrapling
```

### Check doctor output

```bash
agent-reach doctor
```

## Known Termux Limitations

- **StealthyFetcher (Camoufox) won't work on Termux** — no browser binary support on ARM Android
- **Lightpanda also not available on Termux** (Linux x86_64 only)
- **Tier 1 and Tier 2 work fine on Termux**
- For full stealth testing use your Hetzner VPS instead

## How to Test Stealth on VPS from Mobile

SSH into your Hetzner VPS from Termux:

```bash
ssh user@your-vps-ip
agent-reach fetch https://www.mohre.gov.ae --mode=stealth
agent-reach doctor
```

## Expected Doctor Output on Termux

```
👁️  Agent Reach Status
========================================

✅ Ready to use:
  ✅ Web pages — Jina Reader + Scrapling fallback (Tier 1-2 only on Termux)
  ⚠️  Scrapling Stealth — Camoufox not available on ARM/Android
  ⚠️  Lightpanda — x86_64 only, use VPS for full browser features
```

## Troubleshooting

### pip install fails with "No module named '_ctypes'"

```bash
pkg install libffi
```

### git clone fails

```bash
pkg install openssl
```

### Python packages fail to build

Some packages may need additional dependencies:

```bash
pkg install clang pkg-config
```

## Summary

| Feature | Termux Support | Notes |
|---------|---------------|-------|
| Tier 1: Jina Reader | ✅ Yes | Works perfectly |
| Tier 2: Scrapling Fetcher | ✅ Yes | Lightweight, no browser needed |
| Tier 3: StealthyFetcher | ❌ No | Camoufox requires x86_64 Linux/macOS/Windows |
| Tier 4: Lightpanda | ❌ No | Docker/x86_64 only |
| UAE Gov Portals | ⚠️ Limited | Use VPS for full access |
