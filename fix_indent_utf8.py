# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_excessive_indentation(lines):
    """修复过度缩进"""
    fixed_lines = []
    fixes = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue

        if indent > 32:
            target_indent = None

            for j in range(i-1, max(0, i-10), -1):
                prev_stripped = lines[j].lstrip()
                prev_indent = len(lines[j]) - len(prev_stripped)
                if prev_stripped and not prev_stripped.startswith('#') and prev_stripped.strip():
                    if prev_indent < indent:
                        target_indent = prev_indent + 4
                        break

            if target_indent is None:
                target_indent = (indent // 4) * 4

            if target_indent != indent:
                fixed_line = ' ' * target_indent + stripped
                fixed_lines.append(fixed_line)
                fixes.append({
                    'line': i + 1,
                    'old_indent': indent,
                    'new_indent': target_indent,
                    'text': stripped[:50]
                })
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return fixed_lines, fixes

if __name__ == '__main__':
    file_path = 'xinggang.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f'File: {file_path}')
    print(f'Total lines: {len(lines)}')
    print()

    lines, fixes = fix_excessive_indentation(lines)

    if fixes:
        print(f'Fixed {len(fixes)} indentation issues')
        for fix in fixes:
            print(f"Line {fix['line']:4d}: {fix['old_indent']:2d} spaces -> {fix['new_indent']:2d} spaces")

        backup_path = file_path + '.backup_indent'
        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(file_path, 'r', encoding='utf-8') as original:
                f.write(original.read())

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print()
        print(f'Backup saved to: {backup_path}')
        print(f'Fixed file saved to: {file_path}')
    else:
        print('No excessive indentation issues found.')
