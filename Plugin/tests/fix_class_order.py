#!/usr/bin/env python3
"""
Reorganize DDX777Core.h to move member variables before methods
"""

with open(r'<PROJECT_ROOT>\Plugin\src\dsp\DDX777Core.h', 'r', encoding='utf-8') as f:
    content = f.read()

# Find key positions
class_start = content.find('class DDX777Core')
class_end_idx = content.find('};', content.find('class DDX777Core'))
member_start = content.find('double fs_ = 48000.0;', content.find('class DDX777Core'))

if member_start == -1:
    print("ERROR: Could not find member variable section")
    exit(1)

# Extract parts
before_class = content[:content.find('class DDX777Core')]
class_decl = content[content.find('class DDX777Core'):content.find('{', content.find('class DDX777Core')) + 1]
class_body = content[content.find('{', content.find('class DDX777Core')) + 1:content.rfind('};', content.find('class DDX777Core'))]

# Find member variable section
member_start_idx = content.find('double fs_ = 48000.0;', content.find('class DDX777Core'))

# Split class body
member_start_idx = content.find('double fs_ = 48000.0;', content.find('class DDX777Core'))
methods_part = content[content.find('{', content.find('class DDX777Core')) + 1:member_start_idx]
member_vars = content[member_start_idx:content.rfind('};', content.find('class DDX777Core'))]

# Reconstruct
new_content = content[:content.find('class DDX777Core')] + \
    'class DDX777Core\n{\npublic:\n' + \
    content[member_start_idx:content.rfind('};', content.find('class DDX777Core'))] + '\n' + \
    content[content.find('{', content.find('class DDX777Core')) + 1:member_start_idx] + \
    '\n};' + \
    content[content.rfind('};', content.find('class DDX777Core')) + 2:]

with open(r'<PROJECT_ROOT>\Plugin\src\dsp\DDX777Core.h', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Reorganized class structure')