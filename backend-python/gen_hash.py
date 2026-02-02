#!/usr/bin/env python3
"""生成密码哈希"""
import sys
sys.path.insert(0, 'app')

from core.security import get_password_hash

password = "admin123"
hash_value = get_password_hash(password)
print(hash_value)
