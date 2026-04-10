# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_inconsistent_indentation(lines):
    """修复不一致的缩进"""
    fixed_lines = []
    fixes = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue

        # 查找前10行和后5行的上下文来确定正确的缩进级别
        context_indents = []
        for j in range(max(0, i-10), i):
            ctx_stripped = lines[j].lstrip()
            ctx_indent = len(lines[j]) - len(ctx_stripped)
            if ctx_stripped and not ctx_stripped.startswith('#') and ctx_stripped.strip():
                context_indents.append(ctx_indent)

        for j in range(i+1, min(len(lines), i+5)):
            ctx_stripped = lines[j].lstrip()
            ctx_indent = len(lines[j]) - len(ctx_stripped)
            if ctx_stripped and not ctx_stripped.startswith('#') and ctx_stripped.strip():
                context_indents.append(ctx_indent)

        if context_indents:
            # 找到最接近的上下文缩进级别
            closest_indent = None
            min_diff = float('inf')

            for ctx_indent in context_indents:
                diff = abs(ctx_indent - indent)
                if diff < min_diff:
                    min_diff = diff
                    closest_indent = ctx_indent

            # 如果当前缩进与上下文不一致
            if closest_indent is not None and abs(indent - closest_indent) > 4:
                # 检查是否是过度缩进（超过上下文太多）
                if indent > closest_indent + 8:
                    fixed_indent = closest_indent + 4
                    fixed_line = ' ' * fixed_indent + stripped
                    fixed_lines.append(fixed_line)
                    fixes.append({
                        'line': i + 1,
                        'old_indent': indent,
                        'new_indent': fixed_indent,
                        'text': stripped[:50]
                    })
                else:
                    fixed_lines.append(line)
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

    lines, fixes = fix_inconsistent_indentation(lines)

    if fixes:
        print(f'Fixed {len(fixes)} inconsistent indentation issues:')
        for fix in fixes:
            print(f"Line {fix['line']:4d}: {fix['old_indent']:2d} spaces -> {fix['new_indent']:2d} spaces | {fix['text']}")

        backup_path = file_path + '.backup_inconsistent'
        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(file_path, 'r', encoding='utf-8') as original:
                f.write(original.read())

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print()
        print(f'Backup saved to: {backup_path}')
        print(f'Fixed file saved to: {file_path}')
    else:
        print('No inconsistent indentation issues found.')
