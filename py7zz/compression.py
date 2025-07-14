"""
压缩算法接口模块

为 py7zz 提供类似现代压缩库的简单接口，用于单数据流压缩。
这是对 SevenZipFile 归档功能的补充，不是替代。
"""

import tempfile
from pathlib import Path
from typing import Union

from .core import run_7z


def compress(data: Union[str, bytes], 
             algorithm: str = "lzma2",
             level: int = 5) -> bytes:
    """
    压缩单个数据块，类似 zstd.compress()
    
    Args:
        data: 要压缩的数据
        algorithm: 压缩算法 (lzma2, lzma, ppmd, bzip2, deflate)
        level: 压缩级别 (0-9)
        
    Returns:
        压缩后的字节数据
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # 写入临时文件
        input_file = tmpdir_path / "input.dat"
        input_file.write_bytes(data)
        
        # 压缩为 7z 单文件归档
        output_file = tmpdir_path / "output.7z"
        args = [
            "a", str(output_file),
            str(input_file),
            f"-mx{level}",
            f"-m0={algorithm}",
            "-ms=off"  # 关闭固实模式
        ]
        
        run_7z(args)
        
        # 读取压缩结果
        return output_file.read_bytes()


def decompress(data: bytes) -> bytes:
    """
    解压单个数据块，类似 zstd.decompress()
    
    Args:
        data: 压缩的字节数据
        
    Returns:
        解压后的字节数据
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # 写入压缩数据
        input_file = tmpdir_path / "input.7z"
        input_file.write_bytes(data)
        
        # 解压
        output_dir = tmpdir_path / "output"
        args = ["x", str(input_file), f"-o{output_dir}", "-y"]
        
        run_7z(args)
        
        # 找到解压的文件
        output_files = list(output_dir.glob("*"))
        if not output_files:
            raise ValueError("No files found in archive")
        
        # 返回第一个文件的内容
        return output_files[0].read_bytes()


class Compressor:
    """
    压缩器类，提供类似 zstd.ZstdCompressor 的接口
    """
    
    def __init__(self, algorithm: str = "lzma2", level: int = 5):
        self.algorithm = algorithm
        self.level = level
    
    def compress(self, data: Union[str, bytes]) -> bytes:
        """压缩数据"""
        return compress(data, self.algorithm, self.level)


class Decompressor:
    """
    解压器类，提供类似 zstd.ZstdDecompressor 的接口
    """
    
    def decompress(self, data: bytes) -> bytes:
        """解压数据"""
        return decompress(data)


# 便捷函数，模仿现代压缩库
def lzma2_compress(data: Union[str, bytes], level: int = 5) -> bytes:
    """LZMA2 压缩"""
    return compress(data, "lzma2", level)


def lzma2_decompress(data: bytes) -> bytes:
    """LZMA2 解压"""
    return decompress(data)


def bzip2_compress(data: Union[str, bytes], level: int = 5) -> bytes:
    """BZIP2 压缩"""
    return compress(data, "bzip2", level)


def bzip2_decompress(data: bytes) -> bytes:
    """BZIP2 解压"""
    return decompress(data)