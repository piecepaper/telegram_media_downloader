import os

from windows_telegram_placeholder import create_sparse_file, line

# ------------------- 你只需要改这 2 行 -------------------
SOURCE_PATH = "\\\\192.168.5.100\\外接存储-st16000nm000j-2tw103\\NAS\\telegram"
TARGET_PATH = "D:\\projects\\telegram_media_downloader\\downloads"
# -------------------------------------------------------


def main():
    line.print(f"{SOURCE_PATH} -> {TARGET_PATH}")

    # 检查源路径是否存在
    if not os.path.exists(SOURCE_PATH):
        line.print(f"错误: 源路径 {SOURCE_PATH} 不存在")
        return

    # 递归遍历源目录
    file_paths = []
    for root, _, files in os.walk(SOURCE_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, SOURCE_PATH)
            dst_path = os.path.join(TARGET_PATH, rel_path)
            if os.path.exists(dst_path):
                # line.print(f"跳过: 已存在同名文件 {rel_path}")
                continue

            file_paths.append(file_path)

    total = len(file_paths)
    width = len(str(total))
    fail_count = 0
    for i in range(total):
        file_path = file_paths[i]
        rel_path = os.path.relpath(file_path, SOURCE_PATH)
        dst_path = os.path.join(TARGET_PATH, rel_path)
        size = os.path.getsize(file_path)  # 获取原文件大小

        # 创建目标目录
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        # 1.隐藏文件名名字 2.名字太长了
        file_name, file_suffix = rel_path.rsplit(".", 1)
        file_name = file_name.split('-', 1)[0]
        show_path = f"{file_name}- ****.{file_suffix}"
        line.update(f"[{i+1:>{width}}/{total}] 创建稀疏文件 {show_path}")

        # 创建稀疏文件
        if not create_sparse_file(dst_path, size):
            fail_count += 1
            line.update_break(f"❌ 创建失败: {rel_path}")

    line.update_break(f"完成. 成功：{total - fail_count} 失败：{fail_count}")


if __name__ == "__main__":
    main()
