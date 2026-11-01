# Copyright (c) 2025 DFlexy · https://github.com/DFlexy

import sys
sys.dont_write_bytecode = True

import re
import hashlib
import base64
import logging
from urllib.parse import urlparse, parse_qs, unquote
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MagnetParser:
    @staticmethod
    def parse(uri: str) -> Dict:
        parsed = urlparse(uri)
        if parsed.scheme != 'magnet':
            raise ValueError(f"Esquema inválido: {parsed.scheme}")
        
        match = re.search(r'xt=urn:btih:([^&]+)', parsed.query, re.IGNORECASE)
        if match:
            info_hash_raw = match.group(1)
            if '%' in info_hash_raw:
                def replace_percent(match):
                    hex_chars = match.group(1)
                    if all(c in '0123456789abcdefABCDEF' for c in hex_chars):
                        return hex_chars
                    return ''
                
                info_hash_cleaned = re.sub(r'%([0-9A-Fa-f]{2})', replace_percent, info_hash_raw)
                if len(info_hash_cleaned) in [32, 40]:
                    info_hash_encoded = info_hash_cleaned
                else:
                    info_hash_decoded = unquote(info_hash_raw)
                    if len(info_hash_decoded) in [32, 40]:
                        info_hash_encoded = info_hash_decoded
                    elif len(info_hash_raw) in [32, 40]:
                        info_hash_encoded = info_hash_raw
                    else:
                        info_hash_encoded = info_hash_cleaned
            else:
                info_hash_encoded = info_hash_raw
        else:
            query = parse_qs(parsed.query)
            xt = query.get('xt', [])
            if not xt:
                raise ValueError("Parâmetro xt não encontrado")
            xt_value = xt[0]
            if not xt_value.startswith('urn:btih:'):
                raise ValueError("Formato de xt inválido")
            info_hash_encoded = unquote(xt_value[9:])
        
        info_hash_bytes = MagnetParser._decode_infohash(info_hash_encoded)
        
        query = parse_qs(parsed.query)
        info_hash_hex = info_hash_bytes.hex()
        
        display_name = ''
        if 'dn' in query:
            display_name = unquote(query['dn'][0])
        
        trackers = []
        if 'tr' in query:
            trackers = [unquote(tr) for tr in query['tr']]
        
        params = {}
        for key, values in query.items():
            if key not in ['xt', 'dn', 'tr']:
                params[key] = unquote(values[0]) if values else ''
        
        result = {
            'info_hash': info_hash_hex,
            'display_name': display_name,
            'trackers': trackers,
            'params': params
        }
        return result
    
    @staticmethod
    def _decode_infohash(encoded: str) -> bytes:
        encoded_clean = ''.join(c for c in encoded if c.isalnum() or c in '+-=')
        
        hex_chars = ''.join(c for c in encoded_clean if c in '0123456789abcdefABCDEF')
        
        if len(hex_chars) == 40:
            try:
                return bytes.fromhex(hex_chars)
            except ValueError:
                pass
        
        if len(hex_chars) > 40:
            try:
                return bytes.fromhex(hex_chars[:40])
            except ValueError:
                pass
        
        if len(encoded_clean) == 40:
            try:
                if all(c in '0123456789abcdefABCDEF' for c in encoded_clean):
                    return bytes.fromhex(encoded_clean)
            except ValueError:
                pass
        
        if len(encoded_clean) == 32:
            try:
                return base64.b32decode(encoded_clean.upper())
            except Exception:
                pass
        
        if len(encoded) == 40:
            try:
                hex_only = ''.join(c for c in encoded if c in '0123456789abcdefABCDEF')
                if len(hex_only) >= 40:
                    return bytes.fromhex(hex_only[:40])
            except ValueError:
                pass
        
        if len(encoded) == 32:
            try:
                return base64.b32decode(encoded.upper())
            except Exception:
                pass
        
        raise ValueError(f"Tamanho de info_hash inválido: {len(encoded_clean)} (original: {len(encoded)})")


def parse_bencode_size(data: bytes, expected_hash: Optional[str] = None) -> Optional[int]:
    """Read the complete v1 info dictionary, verifying its exact SHA-1 when supplied."""
    try:
        def parse(pos, depth=0):
            if depth > 64 or pos >= len(data):
                raise ValueError("invalid bencode")
            token = data[pos:pos + 1]
            if token == b'i':
                end = data.index(b'e', pos + 1)
                raw = data[pos + 1:end]
                if not raw or (raw.startswith(b'0') and len(raw) > 1) or raw.startswith(b'-0'):
                    raise ValueError("invalid integer")
                return int(raw), end + 1
            if token in (b'l', b'd'):
                is_dict = token == b'd'
                result = {} if is_dict else []
                pos += 1
                while pos < len(data) and data[pos:pos + 1] != b'e':
                    value, pos = parse(pos, depth + 1)
                    if is_dict:
                        if not isinstance(value, bytes) or value in result:
                            raise ValueError("invalid key")
                        item, pos = parse(pos, depth + 1)
                        result[value] = item
                    else:
                        result.append(value)
                if pos >= len(data):
                    raise ValueError("truncated container")
                return result, pos + 1
            if token.isdigit():
                colon = data.index(b':', pos)
                raw = data[pos:colon]
                if not raw.isdigit() or (len(raw) > 1 and raw.startswith(b'0')):
                    raise ValueError("invalid string")
                end = colon + 1 + int(raw)
                if end > len(data):
                    raise ValueError("truncated string")
                return data[colon + 1:end], end
            raise ValueError("invalid token")

        if data[:1] != b'd':
            return None
        pos, info, info_bytes = 1, None, None
        seen = set()
        while pos < len(data) and data[pos:pos + 1] != b'e':
            key, pos = parse(pos)
            if not isinstance(key, bytes) or key in seen:
                return None
            seen.add(key)
            start = pos
            value, pos = parse(pos)
            if key == b'info':
                info, info_bytes = value, data[start:pos]
        if pos != len(data) - 1 or data[pos:pos + 1] != b'e' or not isinstance(info, dict):
            return None
        if expected_hash and hashlib.sha1(info_bytes).hexdigest() != expected_hash.lower():
            return None
        files = info.get(b'files')
        if files is not None:
            if not isinstance(files, list) or not files:
                return None
            lengths = [f.get(b'length') if isinstance(f, dict) else None for f in files]
            if any(type(n) is not int or n < 0 for n in lengths):
                return None
            size = sum(lengths)
        else:
            size = info.get(b'length')
        return size if type(size) is int and size > 0 else None
    except (ValueError, IndexError, OverflowError, RecursionError):
        return None
