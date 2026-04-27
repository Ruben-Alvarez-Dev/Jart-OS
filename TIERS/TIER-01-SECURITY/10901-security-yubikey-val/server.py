#!/usr/bin/env python3
"""
Yubico OTP Validation Server - WSAPI 2.0 compliant
Uses python3-yubiotp for OTP decryption and validation.
"""

import base64
import hashlib
import hmac
import os
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from binascii import unhexlify

from yubiotp.otp import decode_otp, CRCError

# --- Configuration (from environment variables) ---
PORT = int(os.environ.get('YUBIVAL_PORT', '10901'))
AES_KEY = unhexlify(os.environ['YUBIVAL_AES_KEY'])
PUBLIC_ID = os.environ['YUBIVAL_PUBLIC_ID']
CLIENT_ID = int(os.environ.get('YUBIVAL_CLIENT_ID', '1'))
CLIENT_KEY = base64.b64decode(os.environ['YUBIVAL_CLIENT_KEY'])

# --- State (replay protection) ---
STATE_FILE = '/opt/yubikey-val-server/counter.state'
last_session = 0
last_counter = 0


def load_state():
    global last_session, last_counter
    try:
        with open(STATE_FILE, 'r') as f:
            parts = f.read().strip().split(':')
            last_session = int(parts[0])
            last_counter = int(parts[1])
    except (FileNotFoundError, ValueError):
        last_session = 0
        last_counter = 0


def save_state(session, counter):
    global last_session, last_counter
    last_session = session
    last_counter = counter
    with open(STATE_FILE, 'w') as f:
        f.write(f'{session}:{counter}')


def verify_otp(otp_string):
    """Verify an OTP token. Returns (status, session, counter)."""
    if not otp_string:
        return 'NO_OTP_PROVIDED', 0, 0

    if not otp_string.startswith(PUBLIC_ID):
        return 'BAD_OTP', 0, 0

    try:
        token = otp_string.encode('ascii')
        pub_id, otp = decode_otp(token, AES_KEY)
    except CRCError:
        return 'BAD_OTP', 0, 0
    except Exception:
        return 'BAD_OTP', 0, 0

    # Replay protection
    if otp.session < last_session:
        return 'REPLAYED_OTP', otp.session, otp.counter
    if otp.session == last_session and otp.counter <= last_counter:
        return 'REPLAYED_OTP', otp.session, otp.counter

    save_state(otp.session, otp.counter)
    return 'OK', otp.session, otp.counter


def sign_response(params):
    """Compute HMAC-SHA1 signature over response parameters."""
    # Sort params alphabetically by key, join with &
    sorted_items = sorted(params.items())
    data = '&'.join(f'{k}={v}' for k, v in sorted_items)
    sig = hmac.new(CLIENT_KEY, data.encode('utf-8'), hashlib.sha1).digest()
    return base64.b64encode(sig).decode('ascii')


class ValidationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path not in ('/wsapi/2.0/verify', '/wsapi/decrypt'):
            self.send_response(404)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)
        otp_string = params.get('otp', [''])[0]
        nonce = params.get('nonce', ['na'])[0]

        status, session, counter = verify_otp(otp_string)
        timestamp = int(time.time())

        # Build response parameters (all EXCEPT 'h')
        resp_params = {
            'nonce': nonce,
            'otp': otp_string,
            'sessioncounter': str(session),
            'sessionuse': str(counter),
            'sl': '100',
            'status': status,
            't': str(timestamp),
        }

        # Sign and add HMAC
        signature = sign_response(resp_params)
        resp_params['h'] = signature

        # Format response
        response_body = '\r\n'.join(f'{k}={v}' for k, v in resp_params.items()) + '\r\n'

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(response_body.encode('utf-8'))

    def log_message(self, format, *args):
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {args[0]}')


def main():
    load_state()
    server = HTTPServer(('127.0.0.1', PORT), ValidationHandler)
    print(f'Yubico OTP Validation Server on 127.0.0.1:{PORT}')
    print(f'  Public ID: {PUBLIC_ID}')
    print(f'  Client ID: {CLIENT_ID}')
    print(f'  HMAC key: [REDACTED]')
    print(f'  Last state: session={last_session}, counter={last_counter}')
    server.serve_forever()


if __name__ == '__main__':
    main()
