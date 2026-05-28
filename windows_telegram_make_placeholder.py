import ctypes
import os
from datetime import datetime

# ------------------- 你只需要改这 2 行 -------------------
SOURCE_PATH = "E:\\NAS\\telegram"
TARGET_PATH = "D:\\projects\\telegram_media_downloader\\downloads"
# -------------------------------------------------------


def printd(*args: any, **kwargs: any):
    print(f"[{datetime.now().strftime('%H:%M:%S')}]", *args, **kwargs)


# Windows API 定义（用于设置稀疏文件）
DeviceIoControl = ctypes.windll.kernel32.DeviceIoControl
FSCTL_SET_SPARSE = 0x000900C4


def create_sparse_file(target_path, file_size):
    """创建 NTFS 稀疏文件，大小一致，占用 0 空间"""
    # 打开文件（读写模式，无共享，创建新文件）
    handle = ctypes.windll.kernel32.CreateFileW(
        target_path,
        0x10000000 | 0x40000000,  # GENERIC_WRITE | GENERIC_READ
        0,
        None,
        2,
        0x80,
        None,
    )

    if handle == -1:
        print(f"❌ 无法创建文件: {target_path}")
        return False

    try:
        # 设置为稀疏文件
        DeviceIoControl(
            handle,
            FSCTL_SET_SPARSE,
            None,
            0,
            None,
            0,
            ctypes.byref(ctypes.c_ulong()),
            None,
        )

        # 设置文件大小（不会占用空间）
        ctypes.windll.kernel32.SetFilePointerEx(handle, file_size, None, 0)
        ctypes.windll.kernel32.SetEndOfFile(handle)

        return True
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def main():
    printd(f"{SOURCE_PATH} -> {TARGET_PATH}")

    # 检查源路径是否存在
    if not os.path.exists(SOURCE_PATH):
        printd(f"错误: 源路径 {SOURCE_PATH} 不存在")
        return

    # 递归遍历源目录
    file_paths = []
    for root, _, files in os.walk(SOURCE_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, SOURCE_PATH)
            dst_path = os.path.join(TARGET_PATH, rel_path)
            if os.path.exists(dst_path):
                # printd(f"跳过: 已存在同名文件 {rel_path}")
                continue

            file_paths.append(file_path)

    total = len(file_paths)
    width = len(str(total))
    fail_count = 0
    for i in range(total):

        def printdp(*args: any, **kwargs: any):
            printd(f"[{i+1:>{width}}/{total}]", *args, **kwargs)

        file_path = file_paths[i]
        rel_path = os.path.relpath(file_path, SOURCE_PATH)
        dst_path = os.path.join(TARGET_PATH, rel_path)
        size = os.path.getsize(file_path)  # 获取原文件大小

        # 创建目标目录
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        # printdp(f"创建: 稀疏文件 {rel_path}")

        # 创建稀疏文件
        if not create_sparse_file(dst_path, size):
            printd(f"❌ 创建失败: {rel_path}")
            fail_count += 1

    printd(f"完成. 成功：{total - fail_count} 失败：{fail_count}")


if __name__ == "__main__":
    main()
