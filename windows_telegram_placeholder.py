import ctypes
import math
import os
import shutil
import time
from datetime import datetime

# ------------------- 你只需要改这 2 行 -------------------
SOURCE_PATH = "D:\\projects\\telegram_media_downloader\\downloads"
TARGET_PATH = "E:\\NAS\\telegram"
# -------------------------------------------------------


class UpdateLine:
    __update_len = 0

    def print(self, *values: object):
        if self.__update_len > 0:
            self.__new()

        print(self.__strtime(), *values)

    # 更新当前行
    def update(self, context: str):
        # 清除之前的内容
        if self.__update_len > 0:
            print(f"\r{"".ljust(self.__update_len * 2)}", end="", flush=True)

        context = f"{self.__strtime()} {context}"
        print(f"\r{context}", end="", flush=True)

        self.__update_len = len(context)

    # 更新并换行
    def update_break(self, context: str):
        self.update(context)
        self.__new()

    def __new(self):
        print()
        self.__update_len = 0

    def __strtime(self):
        return f"[{datetime.now().strftime('%H:%M:%S')}]"


line = UpdateLine()


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
        ctypes.windll.kernel32.DeviceIoControl(
            handle,
            0x000900C4,
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


def is_sparse_file(file_path: str) -> bool:
    """判断文件是否为 NTFS 稀疏文件"""
    FILE_ATTRIBUTE_SPARSE_FILE = 0x00000200
    attr = ctypes.windll.kernel32.GetFileAttributesW(file_path)
    if attr == 0xFFFFFFFF:
        return False
    return (attr & FILE_ATTRIBUTE_SPARSE_FILE) != 0


def main():
    line.print(f"{SOURCE_PATH} -> {TARGET_PATH}")

    # 检查源路径是否存在
    if not os.path.exists(SOURCE_PATH):
        line.print(f"错误: 源路径 {SOURCE_PATH} 不存在")
        return

    while True:
        curtime = time.time()
        run()
        nexttime = math.floor(curtime / 3600) * 3600 + 3600
        line.print(f"下次执行时间: [{datetime.fromtimestamp(nexttime).strftime('%H:%M:%S')}]")
        time.sleep(nexttime - time.time())


def run():
    # 递归遍历源目录
    file_paths = []
    for root, _, files in os.walk(SOURCE_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            if is_sparse_file(file_path):
                # line.print(f"跳过: 稀疏文件 {rel_path}")
                continue

            file_paths.append(file_path)

    total = len(file_paths)
    if total == 0:
        line.print("没有需要处理的文件.")
        return

    width = len(str(total))
    fail_count = 0
    for i in range(total):
        file_path = file_paths[i]
        rel_path = os.path.relpath(file_path, SOURCE_PATH)
        dst_path = os.path.join(TARGET_PATH, rel_path)
        size = os.path.getsize(file_path)  # 获取原文件大小

        # 创建目标目录
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        line.update(f"[{i+1:>{width}}/{total}] 移动文件 {rel_path}")

        # 使用 shutil.move 跨磁盘也可以处理
        shutil.move(file_path, dst_path)

        # 创建稀疏文件
        if not create_sparse_file(file_path, size):
            fail_count += 1
            line.update_break(f"❌ 创建失败: {rel_path}")

    line.update_break(f"完成. 成功：{total - fail_count} 失败：{fail_count}")


if __name__ == "__main__":
    main()
