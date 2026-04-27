# YubiKey OTP sudo Authentication

**Date:** 2026-04-27
**Status:** ✅ PRODUCTION READY

---

## Architecture

```
┌─────────────┐     SSH      ┌──────────────────────────┐
│  Client     │─────────────▶│  Host                     │
│  YubiKey    │              │                          │
│  USB-C      │              │  sudo user runs:         │
│  Slot 1 OTP │              │    sudo <command>        │
└─────────────┘              │         │                │
                             │         ▼                │
                             │  PAM (pam_yubico.so)     │
                             │  mode=client             │
                             │         │                │
                             │         ▼                │
                             │  Validation Server       │
                             │  127.0.0.1:{PORT}        │
                             │  (Python + yubiotp)      │
                             │         │                │
                             │  AES decrypt + CRC check │
                             │  HMAC-SHA1 sign response │
                             │         │                │
                             │    status=OK → sudo OK   │
                             └──────────────────────────┘
```

## Auth Flow

1. User runs `sudo <command>`
2. PAM prompts: `YubiKey for <user>:`
3. User touches YubiKey → OTP typed as keyboard input
4. `pam_yubico.so` sends OTP to validation server
5. Server decrypts OTP (AES-128-ECB), checks CRC16
6. Server checks replay protection (session:counter)
7. Server signs response with HMAC-SHA1
8. PAM verifies HMAC → Success
9. Fallback: if YubiKey fails → password + TOTP

## Environment Variables (required)

| Variable | Description | Example |
|----------|-------------|---------|
| `YUBIVAL_AES_KEY` | AES-128 key (hex) | `a1b2c3...` (32 hex chars) |
| `YUBIVAL_PUBLIC_ID` | YubiKey public ID (modhex) | `vvcccbunttbe` |
| `YUBIVAL_CLIENT_KEY` | HMAC client key (base64) | `base64-encoded-key` |
| `YUBIVAL_PORT` | Server port (default: 10901) | `10901` |
| `YUBIVAL_CLIENT_ID` | Client ID (default: 1) | `1` |

## Components

### Validation Server
- Path: `/opt/yubikey-val-server/server.py`
- Service: `yubikey-val.service` (systemd, enabled)
- Port: `127.0.0.1:{PORT}` (localhost only)
- Library: `python3-yubiotp`

### systemd unit example

```ini
[Unit]
Description=Yubico OTP Validation Server
After=network.target

[Service]
Type=simple
EnvironmentFile=/opt/yubikey-val-server/.env
ExecStart=/usr/bin/python3 /opt/yubikey-val-server/server.py
Restart=always
RestartSec=5
WorkingDirectory=/opt/yubikey-val-server

[Install]
WantedBy=multi-user.target
```

### PAM config example

```
auth [success=done new_authtok_reqd=done default=ignore] pam_yubico.so \
  mode=client \
  urllist=http://127.0.0.1:{PORT}/wsapi/2.0/verify \
  authfile=/etc/yubico/authorized_yubikeys \
  id={CLIENT_ID} \
  key={CLIENT_KEY}
```

## Users

| User     | Groups     | sudo | Auth Method             |
|----------|------------|------|-------------------------|
| admin    | sudo       | YES  | YubiKey OTP / password+TOTP |
| operator | (no sudo)  | NO   | SSH key only            |
| root     | root       | N/A  | Disabled                |

## Files on Host

| File | Purpose |
|------|---------|
| `/opt/yubikey-val-server/server.py` | Validation server |
| `/opt/yubikey-val-server/.env` | Secrets (NOT in repo) |
| `/opt/yubikey-val-server/counter.state` | Replay protection state |
| `/etc/systemd/system/yubikey-val.service` | systemd unit |
| `/etc/pam.d/sudo` | PAM config |
| `/etc/yubico/authorized_yubikeys` | User → YubiKey mapping |

## Service Management

```bash
systemctl status yubikey-val
systemctl restart yubikey-val
journalctl -u yubikey-val -f
curl http://127.0.0.1:{PORT}/wsapi/2.0/verify?otp=test&nonce=abc&id=1
```

## Security

- Root SSH disabled (`PermitRootLogin no`)
- Password auth disabled (`PasswordAuthentication no`)
- SSH key-only + keyboard-interactive (PAM)
- Only Tailscale IPs (Match Address in sshd_config)
- Replay protection on OTP validation
- HMAC-SHA1 signed responses
- Secrets read from environment, never hardcoded
