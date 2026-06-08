import os
import sys
from collections import defaultdict

os.chdir(os.path.dirname(os.path.abspath(__file__)))

exclude_dirs = ('.git', '.idea', '__pycache__', '.vcpkg', 'ncatbot')  # 要排除的目录

def count_string_in_files(search_string, extensions=('.py', '.html', '.js')):
    """
    统计当前目录及子目录中指定扩展名文件中搜索字符串的出现次数
    
    Args:
        search_string: 要搜索的字符串
        extensions: 要搜索的文件扩展名元组
    """
    results = []  # 存储结果：(文件名, 出现次数)
    
    # 遍历当前目录及所有子目录
    for root, dirs, files in os.walk('.'):
        excluded = False
        for exclude_dir in exclude_dirs:
            if exclude_dir in root:
                excluded = True
                break
        if excluded:
            continue
        for file in files:
            # 检查文件扩展名
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                try:
                    print(f"正在搜索{root}, {filepath}， 大小{os.stat(filepath).st_size / 1024:.2f} KB")
                    # 读取文件内容
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 统计字符串出现次数
                    count = content.count(search_string)
                    
                    if count > 0:
                        # 将结果添加到列表
                        relative_path = os.path.relpath(filepath)
                        results.append((relative_path, count))
                        
                except UnicodeDecodeError:
                    # 如果utf-8编码失败，尝试其他编码
                    try:
                        with open(filepath, 'r', encoding='latin-1') as f:
                            content = f.read()
                        
                        count = content.count(search_string)
                        
                        if count > 0:
                            relative_path = os.path.relpath(filepath)
                            results.append((relative_path, count))
                            
                    except:
                        # 如果还是无法读取，跳过该文件
                        pass
                except Exception as e:
                    # 跳过无法读取的文件
                    pass
    
    return results

def main():
    # 检查是否提供了搜索字符串
    search_string = None
    if len(sys.argv) < 2:
        print("用法: python script.py <要搜索的字符串>")
        print("示例: python script.py \"def test_\"")
        search_string = input("请输入要查找的字符串:")
    else:
        search_string = sys.argv[1]
    
    if not search_string:
        print("错误: 搜索字符串不能为空")
        sys.exit(1)
    
    print(f"正在搜索字符串: '{search_string}'")
    print("搜索文件类型: .py, .html, .js")
    print("-" * 50)
    
    # 统计出现次数
    results = count_string_in_files(search_string)
    
    if not results:
        print(f"没有在文件中找到字符串: '{search_string}'")
        return
    
    # 按出现次数降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    # 打印结果
    print(f"找到 {len(results)} 个包含该字符串的文件:")
    print("-" * 50)
    
    total_count = 0
    for filepath, count in results:
        print(f"{filepath}: {count} 次")
        total_count += count
    
    print("-" * 50)
    print(f"总计: {total_count} 次出现")

if __name__ == "__main__":
    main()