"""Lumice（冰晕仿真器 CLI）胶水层：拉钉版本二进制 → 写 config → 跑 CLI → 收图 + 出处 sidecar。

- :mod:`.fetch`   按 ``LUMICE_VERSION`` 从 GitHub release 拉 ``Lumice`` 二进制到 ``<repo>/.lumice/``（gitignore）
- :mod:`.config`  按 v4.5.1 ``doc/configuration.md`` 生成 ``crystal / filter / scene / render`` 四段 config
- :mod:`.run`     调 CLI、收图、写 ``provenance.json``（版本 / 二进制与 config 的 sha256 / 墙钟 / 平台）
- :mod:`.compose` Lumice 输出与 matplotlib 标注、``halo_notes.draw`` inset 的合成
- :mod:`.analyze` ``Lumice analyze`` 子命令（4.6.x，本地 build）：随机朝向光路分析 CSV → Φ 类聚合 / 与精确枚举互证
"""
