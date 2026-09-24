"""系列级共享数学：S² / S³ 均匀采样与最近邻角距离（:mod:`sampling`）、最近邻角距离的解析 pdf 与两种数值算法
（:mod:`density`）。

对称性模块（C6 / D6 置换表示 ``group``、内反射群 12 矩阵权威表 ``reflection_group``、signature 规范型与 Φ 分类
``signature``、ch3 光路 ground truth 清单解析 ``ground_truth``、柱晶姿态 ``attitude``）自 2026-09-24 起由
:mod:`lumice_integral.symmetry` 提供（公开名称 1:1），本包不再持有副本；``attitude.sun_vector`` 对应
:func:`lumice_integral.camera.sun_direction`。

与 :mod:`halo_notes.draw` 无依赖关系：draw 管几何与渲染，这里只管数字。
"""
