from setuptools import setup
from Cython.Build import cythonize

setup(
    name="encode",
    version="1.0.0",
    ext_modules=cythonize(
        "encode.py",
        compiler_directives={"language_level": "3"},
    ),
    install_requires=[
        "cryptography",
    ],
    packages=[],        # 不打包任何包目录
    py_modules=[],      # 不打包任何 .py 文件（只打编译后的 .so/.pyd）
)