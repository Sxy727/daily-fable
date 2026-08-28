# -*- coding: utf-8 -*-
"""
PWA 图标生成脚本（一次性运行）
生成米白底 + 赭红圆点（印章感）的 PNG 图标，纯标准库实现。

运行：python scripts/make_icon.py
输出：app/icon-180.png（iOS 主屏幕）、app/icon-192.png、app/icon-512.png（Android）
"""

import struct
import zlib

# 颜色取自 docs/design-spec.md
BG = (247, 244, 238)   # 米白宣纸色
FG = (166, 75, 42)     # 赭红


def make_png(path, size, scale=4):
    """先放大 scale 倍绘制再缩回，实现圆点边缘抗锯齿"""
    big = size * scale
    r = big * 0.30          # 圆点半径
    c = big / 2.0           # 圆心

    # 在放大图上画圆
    big_px = []
    for y in range(big):
        row = []
        for x in range(big):
            row.append(FG if (x - c) ** 2 + (y - c) ** 2 <= r * r else BG)
        big_px.append(row)

    # 缩回目标尺寸（每 scale×scale 块取平均色）
    rows = []
    for y in range(size):
        row = bytearray([0])   # PNG 每行开头一个过滤类型字节
        for x in range(size):
            rs = gs = bs = 0
            for dy in range(scale):
                for dx in range(scale):
                    px = big_px[y * scale + dy][x * scale + dx]
                    rs += px[0]
                    gs += px[1]
                    bs += px[2]
            n = scale * scale
            row += bytes((rs // n, gs // n, bs // n))
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8bit RGB
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b""))


if __name__ == "__main__":
    make_png("app/icon-192.png", 192)
    make_png("app/icon-512.png", 512)
    make_png("app/icon-180.png", 180)
    print("图标生成完成：app/icon-180.png / icon-192.png / icon-512.png")
