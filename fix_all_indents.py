# -*- coding: utf-8 -*-
import re

def analyze_and_fix_all_indent_issues(file_path):
    """全面分析并修复所有缩进问题"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f'Total lines: {len(lines)}')

    # 第一阶段：修复超过32个空格的过度缩进
    print('\nPhase 1: Fixing excessive indentation (>32 spaces)...')
    fixed_lines = []
    fixes_phase1 = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue

        indent = len(line) - len(stripped)

        # 修复超过32个空格的过度缩进
        if indent > 32:
            # 查找前5行来确定正确的缩进级别
            target_indent = None
            for j in range(i-1, max(0, i-5), -1):
                prev_stripped = lines[j].lstrip()
                prev_indent = len(lines[j]) - len(prev_stripped)
                if prev_stripped and not prev_stripped.startswith('#') and prev_stripped.strip():
                    if prev_indent < indent:
                        # 找到更小的缩进，说明需要调整
                        target_indent = min(prev_indent + 4, 32)  # 最大不超过32
                        break

            if target_indent is None:
                target_indent = min((indent // 4) * 4, 32)

            if target_indent != indent:
                fixed_line = ' ' * target_indent + stripped
                fixed_lines.append(fixed_line)
                fixes_phase1.append({
                    'line': i + 1,
                    'old_indent': indent,
                    'new_indent': target_indent
                })
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    print(f'Phase 1 fixed: {len(fixes_phase1)} issues')

    # 第二阶段：修复不一致的缩进
    print('\nPhase 2: Fixing inconsistent indentation...')
    fixes_phase2 = []
    final_lines = []

    for i, line in enumerate(final_lines if final_lines else fixed_lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            final_lines.append(line)
            continue

        indent = len(line) - len(stripped)

        # 查找上下文来确定正确的缩进
        context_indents = []
        for j in range(max(0, i-5), i):
            if j < len(fixed_lines):
                ctx_stripped = fixed_lines[j].lstrip()
                ctx_indent = len(fixed_lines[j]) - len(ctx_stripped)
                if ctx_stripped and not ctx_stripped.startswith('#') and ctx_stripped.strip():
                    context_indents.append(ctx_indent)

        if context_indents:
            # 找到最接近的缩进级别
            closest = min(context_indents, key=lambda x: abs(x - indent))
            diff = abs(indent - closest)

            # 如果差异超过8个空格，认为是不一致的
            if diff > 8:
                # 调整到与上下文一致
                fixed_indent = closest + 4 if indent > closest else closest
                if fixed_indent != indent:
                    fixed_line = ' ' * fixed_indent + stripped
                    final_lines.append(fixed_line)
                    fixes_phase2.append({
                        'line': i + 1,
                        'old_indent': indent,
                        'new_indent': fixed_indent
                    })
                else:
                    final_lines.append(line)
            else:
                final_lines.append(line)
        else:
            final_lines.append(line)

    print(f'Phase 2 fixed: {len(fixes_phase2)} issues')

    total_fixes = fixes_phase1 + fixes_phase2

    return fixed_lines, total_fixes

if __name__ == '__main__':
    file_path = 'xinggang.py'

    print('=' * 70)
    print('Comprehensive Indentation Fix Tool')
    print('=' * 70)

    fixed_lines, all_fixes = analyze_and_fix_all_indent_issues(file_path)

    if all_fixes:
        print(f'\nTotal fixes applied: {len(all_fixes)}')

        # Create backup
        backup_path = file_path + '.comprehensive_backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(file_path, 'r', encoding='utf-8') as original:
                f.write(original.read())

        # Save fixed file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)

        print(f'\nBackup saved to: {backup_path}')
        print(f'Fixed file saved to: {file_path}')
    else:
        print('\nNo fixes needed.')

    print('=' * 70)
