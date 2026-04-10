import re

def analyze_and_fix_indentation(file_path):
    """分析并修复Python文件的缩进问题"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    problem_count = 0
    total_fixes = 0

    # 分析缩进模式
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # 检查是否有过多缩进（超过40个空格）
        if indent > 40 and stripped and not stripped.startswith('#'):
            # 计算应该的缩进（使用4空格缩进）
            # 基于上下文推断正确的缩进级别
            expected_indent = (indent // 4) * 4

            # 如果是异常的多余缩进，尝试修正
            if indent % 4 == 0 and indent > 40:
                # 检查上下文来确定真正的缩进级别
                # 通常过多的缩进是因为嵌套if语句
                # 正常情况下，Python代码不会超过20层嵌套
                # 所以超过40个空格的缩进很可能是错误的

                # 找到最近的非注释非空行来推断正确的缩进
                correct_indent = None
                for j in range(i-1, -1, -1):
                    prev_stripped = lines[j].lstrip()
                    prev_indent = len(lines[j]) - len(prev_stripped)
                    if prev_stripped and not prev_stripped.startswith('#'):
                        # 假设正确的缩进应该与前一行相近
                        # 但由于这是代码块内部，缩进应该相同
                        correct_indent = prev_indent
                        break

                if correct_indent is not None and indent > correct_indent + 20:
                    # 发现了异常的多余缩进
                    fixed_line = ' ' * correct_indent + stripped
                    fixed_lines.append(fixed_line)
                    total_fixes += 1
                    problem_count += 1
                    print(f'行 {i+1}: 缩进从 {indent} 修正为 {correct_indent}')
                else:
                    fixed_lines.append(line)
            else:
                # 非4的倍数的缩进也修正
                fixed_indent = (indent // 4) * 4
                fixed_line = ' ' * fixed_indent + stripped
                fixed_lines.append(fixed_line)
                total_fixes += 1
                problem_count += 1
                print(f'行 {i+1}: 缩进从 {indent} 修正为 {fixed_indent}')
        elif indent % 4 != 0 and stripped and not stripped.startswith('#'):
            # 修正非4倍数的缩进
            fixed_indent = (indent // 4) * 4
            if fixed_indent != indent:
                fixed_line = ' ' * fixed_indent + stripped
                fixed_lines.append(fixed_line)
                total_fixes += 1
                problem_count += 1
                print(f'行 {i+1}: 缩进从 {indent} 修正为 {fixed_indent}')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return fixed_lines, problem_count, total_fixes

if __name__ == '__main__':
    file_path = 'xinggang.py'

    print('=' * 60)
    print('开始分析并修复缩进问题')
    print('=' * 60)

    fixed_lines, problem_count, total_fixes = analyze_and_fix_indentation(file_path)

    print('\n' + '=' * 60)
    print(f'分析完成！')
    print(f'发现问题行数: {problem_count}')
    print(f'总修正次数: {total_fixes}')
    print('=' * 60)

    # 保存修复后的文件
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        with open(file_path, 'r', encoding='utf-8') as original:
            f.write(original.read())

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    print(f'\n原始文件已备份到: {backup_path}')
    print(f'修复后的文件已保存到: {file_path}')
