#!/usr/bin/env python3
"""
Reorganize DDX777Core.h to move member variables before methods
"""

with open(r'<PROJECT_ROOT>\Plugin\src\dsp\DDX777Core.h', 'r', encoding='utf-8') as f:
    content = f.read()

# Find class boundaries
class_start_idx = content.find('class DDX777Core')
class_end_idx = content.find('};', content.find('class DDX777Core'))
class_text = content[content.find('class DDX777Core'):content.find('};', content.find('class DDX777Core')) + 2]

# Find member variable section (starts with "double fs_ = 48000.0;")
member_start_idx = content.find('double fs_ = 48000.0;', content.find('class DDX777Core'))

# Split class into: before members, member variables, after members
before_members = content[:member_start_idx]
member_vars = content[member_start_idx:content.rfind('};', content.find('class DDX777Core'))]

# The part before member variables is the methods
methods_part = content[content.find('class DDX777Core'):member_start_idx]

# Now reconstruct: class declaration + public: + member variables + methods + closing
# We need to insert member variables right after "public:"

# Find the "public:" line
public_idx = content.find('public:', content.find('class DDX777Core'))
if public_idx == -1:
    print("public: not found")
    exit(1)

# Find the end of the class
class_end_idx = content.find('};', content.find('class DDX777Core'))
class_text = content[content.find('class DDX777Core'):class_end_idx + 2]

# Split at member variables
member_start = content.find('double fs_ = 48000.0;', content.find('class DDX777Core'))
before_members = content[:member_start_idx]
member_vars_text = content[member_start_idx:content.rfind('};', content.find('class DDX777Core'))]

# Now we need to insert member variables after "public:"
# Find the public: line
public_pos = content.find('public:', content.find('class DDX777Core'))
if public_pos == -1:
    print("public: not found")
    exit(1)

# Find the opening brace after public:
brace_pos = content.find('{', public_pos)
insert_pos = brace_pos + 1

# New content: everything before the brace, then member variables, then the rest
new_content = content[:member_start_idx] + \
    '\n    // Member variables (must be declared before methods that use them)\n' + \
    content[member_start_idx:content.rfind('};', content.find('class DDX777Core'))] + \
    '\n' + \
    content[content.rfind('};', content.find('class DDX777Core')):]

# Actually, let's do this more carefully by working with the class body
with open(r'<PROJECT_ROOT>\Plugin\src\dsp\DDX777Core.h', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find class boundaries
class_start_line = -1
class_end_line = -1
for i, line in enumerate(lines):
    if 'class DDX777Core' in line:
        class_start_line = i
    if '};' in line and i > 0:
        class_end_line = i

# Find member variable declarations (lines with "double ", "float ", etc. at class scope)
member_lines = []
in_class = False
brace_count = 0
for i, line in enumerate(lines):
    if 'class DDX777Core' in line:
        in_class = True
    if '{' in line:
        brace_count += line.count('{')
    if '}' in line:
        brace_count -= line.count('}')
        if brace_count <= 0 and in_class:
            class_end_line = i
            break
    if in_class:
        stripped = line.strip()
        if re.match(r'^\s*(double|float|bool|int|Rng)\s+\w+\s*=', line.strip()) and ';' in line and '(' not in line:
            print(f'Member at line {i+1}: {line.strip()}')

print('Class start:', class_start_line, 'end:', class_end_line)
print('Done')