# YubiKey OTP sudo Authentication

**Date:** 2026-04-27
**Status:** ✅ PRODUCTION READY
**Server:** VPS Ubuntu 26.04 (100.77.1.10 via Tailscale)

---

## Architecture

```
┌─────────────┐     SSH      ┌──────────────────────────┐
│  MacBook    │─────────────▶│  VPS (100.77.1.10)       │
│  YubiKey    │              │                          │
│  USB-C      │              │  vps-sudo runs:          │
│  Slot 1 OTP │              │    sudo <command>        │
└─────────────┘              │         │                │
                             │         ▼                │
                             │  PAM (pam_yubico.so)     │
                             │  mode=client             │
                             │         │                │
                             │         ▼                │
                             │  Validation Server       │
                             │  127.0.0.1:10901         │
                             │  (Python + yubiotp)      │
                             │         │                │
                             │  AES decrypt + CRC check │
                             │  HMAC-SHA1 sign response │
                             │         │                │
                             │    status=OK → sudo OK   │
                             └──────────────────────────┘
```

## Auth Flow

1. vps-sudo runs sudo <command>
2. PAM prompts: YubiKey for vps-sudo:
3. User touches YubiKey → OTP typed as keyboard input
4. pam_yubico.so sends OTP to validation server
5. Server decrypts OTP (AES-128-ECB), checks CRC16
6. Server checks replay protection (session:counter)
7. Server signs response with HMAC-SHA1
8. PAM verifies HMAC → Success
9. Fallback: if YubiKey fails → password + TOTP (Microsoft Authenticator)

## Components

### Validation Server
- Path: /opt/yubikey-val-server/server.py
- Service: yubikey-val.service (systemd, enabled)
- Port: 127.0.0.1:10901 (localhost only)
- Library: python3-yubiotp (Ubuntu package)

### YubiKey Credentials (Slot 1 - OTP)
- Public ID: vvcccbunttbe
- Private ID: REDACTED_PRIVATE_ID
- AES Key: REDACTED_AES_KEY

### YubiKey Credentials (Slot 2 - HMAC)
- Key: REDACTED_HMAC_KEY

### API Client Credentials
- Client ID: 1
- Client Key: REDACTED_CLIENT_KEY (base64)

### TOTP Fallback (Microsoft Authenticator)
- Secret: REDACTED_TOTP_SECRET
- Type: TOTP (time-based, 30s interval)
- Module: pam_google_authenticator.so nullok

## Users

| User     | UID  | Groups         | SSH  | sudo | Auth Method                |
|----------|------|----------------|------|------|----------------------------|
| root     | 0    | root           | NO   | N/A  | Disabled                   |
| vps-sudo | 1001 | vps-sudo, sudo | YES  | YES  | YubiKey OTP / password+TOTP|
| vps      | 1002 | vps            | YES  | NO   | SSH key only               |

## Files on VPS

| File | Purpose |
|------|---------|
| /opt/yubikey-val-server/server.py | Validation server |
| /opt/yubikey-val-server/counter.state | Replay protection state |
| /etc/systemd/system/yubikey-val.service | systemd unit |
| /etc/pam.d/sudo | PAM config |
| /etc/pam.d/sudo.bak.challenge-response | Backup |
| /etc/yubico/authorized_yubikeys | User to YubiKey mapping |
| /home/vps-sudo/.google_authenticator | TOTP secret |
| /etc/ssh/sshd_config.d/99-security.conf | SSH hardening |

## Service Management

```bash
systemctl status yubikey-val
systemctl restart yubikey-val
journalctl -u yubikey-val -f
curl http://127.0.0.1:10901/wsapi/2.0/verify?otp=test&nonce=abc&id=1
```

## Test

```bash
ssh -i ~/.ssh/id_yubikey_vps vps-sudo@100.77.1.10 -t sudo whoami
# Touch YubiKey → output: root
```

## Security

- Root SSH disabled (PermitRootLogin no)
- Password auth disabled (PasswordAuthentication no)
- SSH key-only + keyboard-interactive (PAM)
- Only Tailscale IPs (Match Address in sshd_config)
- Replay protection on OTP validation
- HMAC-SHA1 signed responses
