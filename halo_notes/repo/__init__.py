"""仓库形态工具：git 划界规则（``layout``）与各章重生成入口（``regen``）。

``layout`` 只用标准库（≥ Python 3.9），pre-push 钩子与 filter-repo 回调可在不装 uv 环境的上下文里直接 import。
"""
