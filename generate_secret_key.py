#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for JWT authentication.
Run this to create a new secret key for your .env file.
"""

import secrets
import string

def generate_secret_key(length: int = 64) -> str:
    """Generate a cryptographically secure random secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    key = generate_secret_key()
    print("\n" + "="*70)
    print("Generated SECRET_KEY for JWT Authentication")
    print("="*70)
    print(f"\nSECRET_KEY={key}\n")
    print("="*70)
    print("\nPaste this into your .env file:")
    print("  1. Open .env in a text editor")
    print("  2. Find the line: SECRET_KEY=...")
    print("  3. Replace with the generated key above")
    print("  4. Save and restart the application")
    print("="*70 + "\n")
