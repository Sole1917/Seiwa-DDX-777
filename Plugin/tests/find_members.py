#!/usr/bin/env python3
"""
Find member variables in DDX777Core.h
"""
import re

with open(r'<PROJECT_ROOT>\Plugin\src\dsp\DDX777Core.h', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_class = False
brace_count = 0
for i, line in enumerate(lines):
    if 'class DDX777Core' in line:
        in_class = True
    if '{' in line:
        brace_count += line.count('{')
    if '}' in line:
        brace_count -= line.count('}')
        if brace_count <= 0 and i > 0:
            break
    if in_class:
        stripped = line.strip()
        if re.match(r'^\s*(double|float|bool|int|Rng)\s+\w+\s*=', stripped) and ';' in line and '(' not in line:
            print(f'Line {i+1}: {line.strip()}')

print("Done")