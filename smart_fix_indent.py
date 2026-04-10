import re
from collections import defaultdict

def detect_indentation_patterns(lines):
    """检测文件中的缩进模式"""
    indent_counts = defaultdict(int)

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped and not stripped.startswith('#'):
            # 只统计4的倍数
            if indent % 4 == 0:
                indent_counts[indent] += 1

    return indent_counts

def find_inconsistent_indents(lines):
    """查找不一致的缩进"""
    problems = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped and not stripped.startswith('#'):
            # 检查是否不是4的倍数
            if indent % 4 != 0:
                problems.append({
                    'line': i + 1,
                    'indent': indent,
                    'type': 'not_divisible_by_4',
                    'text': stripped[:60]
                })

            # 检查是否异常高（超过36个空格）
            if indent > 36:
                problems.append({
                    'line': i + 1,
                    'indent': indent,
                    'type': 'excessive_indent',
                    'text': stripped[:60]
                })

    return problems

def smart_fix_indentation(lines):
    """智能修复缩进问题"""
    fixed_lines = []
    fixes = []

    # 分析周围的缩进模式来确定正确的缩进
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue

        # 如果缩进不是4的倍数
        if indent % 4 != 0:
            # 找到前5行和后5行的非注释非空行
            context_indents = []
            for j in range(max(0, i-5), min(len(lines), i+5)):
                if j == i:
                    continue
                ctx_stripped = lines[j].lstrip()
                ctx_indent = len(lines[j]) - len(ctx_stripped)
                if ctx_stripped and not ctx_stripped.startswith('#') and ctx_stripped.strip():
                    context_indents.append(ctx_indent)

            if context_indents:
                # 取最常见的缩进值
                from collections import Counter
                most_common = Counter([c for c in context_indents if c % 4 == 0]).most_common(1)

                if most_common:
                    expected_indent = most_common[0][0]
                    if indent != expected_indent:
                        fixed_line = ' ' * expected_indent + stripped
                        fixed_lines.append(fixed_line)
                        fixes.append({
                            'line': i + 1,
                            'old_indent': indent,
                            'new_indent': expected_indent,
                            'text': stripped[:50]
                        })
                    else:
                        fixed_lines.append(line)
                else:
                    # 无法确定，使用4的倍数近似
                    fixed_indent = (indent // 4) * 4
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

    return fixed_lines, fixes

def fix_excessive_indentation(lines):
    """修复过度缩进"""
    fixed_lines = []
    fixes = []

    # 使用栈来跟踪缩进级别
    indent_stack = []

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue

        # 如果缩进超过32个空格（8层嵌套已经是很多了）
        if indent > 32:
            # 分析上下文
            # 查找前10行来确定缩进应该是什么
            target_indent = None

            for j in range(i-1, max(0, i-10), -1):
                prev_stripped = lines[j].lstrip()
                prev_indent = len(lines[j]) - len(prev_stripped)
                if prev_stripped and not prev_stripped.startswith('#') and prev_stripped.strip():
                    # 假设正确的缩进应该与上下文相近
                    # 但要考虑到这是嵌套代码块
                    if prev_indent < indent:
                        # 找到更小的缩进，说明我们可能多了一层嵌套
                        target_indent = prev_indent + 4
                        break

            if target_indent is None:
                # 使用4的倍数
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

def fix_all_indent_issues(file_path):
    """修复所有缩进问题"""
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f'文件总行数: {len(lines)}')

    # 第一步：修复非4倍数的缩进
    print('\n第一步：修复非4倍数的缩进...')
    lines, fixes1 = smart_fix_indentation(lines)
    print(f'  修复了 {len(fixes1)} 处问题')

    # 第二步：修复过度缩进
    print('\n第二步：修复过度缩进...')
    lines, fixes2 = fix_excessive_indentation(lines)
    print(f'  修复了 {len(fixes2)} 处问题')

    # 统计
    all_fixes = fixes1 + fixes2

    # 显示部分修复详情
    if all_fixes:
        print(f'\n总计修复了 {len(all_fixes)} 处缩进问题')
        print('\n前20处修复详情：')
        for fix in all_fixes[:20]:
            print(f"  行 {fix['line']:4d}: {fix['old_indent']:2d}空格 -> {fix['new_indent']:2d}空格 | {fix['text']}")

    return lines, all_fixes

if __name__ == '__main__':
    file_path = 'xinggang.py'

    print('=' * 70)
    print('Python 文件缩进智能修复工具')
    print('=' * 70)

    fixed_lines, all_fixes = fix_all_indent_issues(file_path)

    # 创建备份
    backup_path = file_path + '.indented_backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        with open(file_path, 'r', encoding='utf-8') as original:
            f.write(original.read())

    print(f'\n原始文件已备份到: {backup_path}')

    # 保存修复后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    print(f'修复后的文件已保存到: {file_path}')
    print('=' * 70)
