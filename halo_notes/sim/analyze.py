"""Lumice ``analyze`` 子命令胶水：随机朝向晶体的全天光路分析 CSV → 面序列行 → Φ 类聚合 / 与精确枚举互证。

与 :mod:`.run` 平行（config → subprocess → 解析产物 → ``provenance.json``），但 CLI 形态不同：子命令 ``analyze``、
产物是 CSV（``--csv``）而非渲染图。全部接口事实按 2026-09-15 本地 build（Ice Halo 仓 ``9232bccb``）实测钉死：

- ``max_hits`` = 链的**面数上限（含入射面）**：``max_hits=3`` 最长链 3 面、``=7`` 7 面、``=8`` 8 面（不是 CUDA 后端注释里的
  ``1 + max_hits``）。要对齐精确枚举器 ``max_len``，传 ``max_hits = max_len``
- distinct 链驻留表每 worker **16384 槽**（``src/core/chain_id_table.hpp::kDefaultCapacity``），满后新链被拒进 ``other``
  桶；头部 ``record_full_hits`` 是被拒的**到达次数**（``src/include/lumice.h`` ``truncated_chain_count`` 注释），不是链长
  截断。``--symmetry`` 只改列表分组，producer 侧仍按 finest 驻留；``--workers N`` 合并后同样封顶 16384 行
- CSV：7 行 ``# key: value`` 头（``Lumice raypath analysis`` / ``exported_at`` / ``region`` / ``symmetry`` / ``total_rays`` /
  ``total_energy`` / ``record_full_hits``），列头 ``Raypath,Energy,Cumulative %,+/-``；``+/-`` 是该行 ``1/√count`` 相对噪声
  （百分比），``count = (100 / ±)²``；溢出时末行 ``other (not recorded),E,100.0000,-``
- ``# total_rays`` ≈ 4.9 × ``--rays``（是出射光线段数，即 stderr 进度里的 "raypaths recorded"），provenance 两个都记
- 相邻重复面链（如 ``5-5-6``）实测存在（能量 0.0000、± 100）：凸多面体上不可能连续两次打同一面，是追迹数值边缘产物，
  互证 / 聚合前按 :func:`has_adjacent_repeat` 过滤并单独计数上报，不静默吞掉
"""

from __future__ import annotations

import json
import math
import os
import platform
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from ..geometry import Polyhedron, fold_matrix
from ..geometry.enumerate import RaypathRecord
from ..math import reflection_group as rg
from ..math.signature import PhiClass, phi_class
from . import config as C
from .fetch import LUMICE_VERSION, ensure_lumice, sha256_of
from .run import LumiceError, config_sha256

CSV_NAME = "analysis.csv"
OTHER_LABEL = "other"
ROI_CHOICES = ("sky", "frame", "cone")


# ---------- config ----------


def analysis_config(ratio: float, *, max_len: int, rays: int, sun_altitude: float = 20.0,
                    wavelength: float = 550.0) -> dict[str, Any]:
    """随机朝向单六棱柱、单波长、无多次散射的 ``analyze`` 场景。

    ``ratio`` 是本仓 :class:`~halo_notes.geometry.HexPrism` 口径的 h/a（边长），经 :func:`~.config.hex_prism_height_ratio`
    换算；``max_len`` 是链面数上限（= Lumice ``max_hits``）；``rays`` 写进 ``scene.ray_num``，:func:`run_analysis` 默认
    从这里取 ``--rays``（一个数只写一处）。随机朝向下太阳高度不影响结果，固定一个值记进 config 即可；单波长使
    ``--rays`` 与跨波长总数一致。``render`` 段留空（实测 ``analyze`` 接受）。"""
    if max_len < 1:
        raise ValueError(f"max_len 必须 ≥ 1，收到 {max_len}")
    crystal = C.prism_crystal(1, height=C.hex_prism_height_ratio(ratio), axis=C.random_axis())
    light = C.sun(sun_altitude, spectrum=[{"wavelength": float(wavelength), "weight": 1.0}])
    sc = C.scene(light, int(rays), [C.entry(1)], max_hits=int(max_len))
    return C.build_config([crystal], [], sc, [])


# ---------- CSV ----------


@dataclass(frozen=True)
class AnalysisHeader:
    """CSV ``#`` 头部；``raw`` 保留全部 ``key: value`` 原文（含未来新增的键）。"""

    region: str
    symmetry: str
    total_rays: int
    total_energy: float
    record_full_hits: int
    exported_at: str
    raw: dict[str, str] = field(repr=False)


@dataclass(frozen=True)
class AnalysisRow:
    """CSV 一行。``other`` 桶行用 ``faces=()`` + ``is_other=True`` 表示（下游一律按 ``is_other`` 分流，不用 ``len(faces)``
    猜）；``noise_pct`` 在 ``+/-`` 列非数字（``other`` 行的 ``-``）时为 ``None``。"""

    faces: tuple[int, ...]
    is_other: bool
    energy_pct: float
    cumulative_pct: float
    noise_pct: float | None
    raw: str = field(repr=False)

    @property
    def label(self) -> str:
        return OTHER_LABEL if self.is_other else "-".join(map(str, self.faces))

    @property
    def count(self) -> float | None:
        """由 ``+/-``（``1/√count`` 的百分比）反推的命中数；``other`` 行或 ± 为 0 时为 ``None``。"""
        if self.noise_pct is None or self.noise_pct <= 0:
            return None
        return (100.0 / self.noise_pct) ** 2

    @property
    def has_adjacent_repeat(self) -> bool:
        return has_adjacent_repeat(self.faces)


def has_adjacent_repeat(faces: Sequence[int]) -> bool:
    """面序列里是否出现连续相同面（追迹数值边缘产物的判据）。"""
    return any(a == b for a, b in zip(faces, faces[1:]))


def parse_raypath(text: str) -> tuple[int, ...]:
    """``3-5`` → ``(3, 5)``。多晶体 ``C1(3-5)`` / 多层 ``a -> b`` 形态本模块不支持（单晶体单层专用），直接报错。"""
    s = text.strip()
    if "(" in s or "->" in s:
        raise ValueError(f"只支持单晶体单层的面序列，收到多晶体 / 多层形态：{text!r}")
    try:
        return tuple(int(tok) for tok in s.split("-"))
    except ValueError as exc:
        raise ValueError(f"无法解析面序列 {text!r}") from exc


def _float_or_none(tok: str) -> float | None:
    try:
        return float(tok)
    except ValueError:
        return None


def parse_analysis_csv(text: str) -> tuple[AnalysisHeader, list[AnalysisRow]]:
    """纯函数解析 ``analyze`` 的 CSV 全文；头部键缺失或列头不符时报错（格式变了要响亮地知道）。"""
    raw: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    for i, line in enumerate(lines):
        if not line.startswith("#"):
            break
        body = line[1:].strip()
        if ":" in body:
            k, v = body.split(":", 1)
            raw[k.strip()] = v.strip()
    else:
        i = len(lines)
    if i >= len(lines) or lines[i].strip() != "Raypath,Energy,Cumulative %,+/-":
        got = lines[i] if i < len(lines) else "<EOF>"
        raise ValueError(f"列头不是 'Raypath,Energy,Cumulative %,+/-'：{got!r}")
    missing = [k for k in ("region", "symmetry", "total_rays", "total_energy", "record_full_hits") if k not in raw]
    if missing:
        raise ValueError(f"CSV 头部缺少键 {missing}；已解析 {sorted(raw)}")
    header = AnalysisHeader(
        region=raw["region"], symmetry=raw["symmetry"], total_rays=int(raw["total_rays"]),
        total_energy=float(raw["total_energy"]), record_full_hits=int(raw["record_full_hits"]),
        exported_at=raw.get("exported_at", ""), raw=raw,
    )
    rows: list[AnalysisRow] = []
    for line in lines[i + 1:]:
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) != 4:
            raise ValueError(f"数据行应为 4 列：{line!r}")
        label, energy, cum, noise = (p.strip() for p in parts)
        is_other = label.startswith(OTHER_LABEL)
        faces = () if is_other else parse_raypath(label)
        rows.append(AnalysisRow(faces, is_other, float(energy), float(cum), _float_or_none(noise), line))
    return header, rows


# ---------- 跑 CLI ----------


@dataclass
class AnalysisResult:
    header: AnalysisHeader
    rows: list[AnalysisRow]
    provenance: dict[str, Any]
    wall_clock_s: float
    out_dir: Path

    @property
    def csv_path(self) -> Path:
        return self.out_dir / CSV_NAME

    @property
    def config_path(self) -> Path:
        return self.out_dir / "config.json"


def _git_head(start: Path) -> str | None:
    """从二进制所在目录向上找 ``.git``，返回该仓 HEAD；找不到 / git 不可用返回 ``None``。"""
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            try:
                out = subprocess.run(["git", "-C", str(parent), "rev-parse", "HEAD"], capture_output=True, text=True,
                                     timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                return None
            return out.stdout.strip() or None
    return None


def run_analysis(
    config: Mapping[str, Any],
    out_dir: Path | str,
    *,
    roi: str = "sky",
    symmetry: str = "none",
    rays: int | None = None,
    seed: int | None = None,
    workers: int | None = None,
    backend: str | None = None,
    timeout: float | None = None,
    bin: Path | None = None,
) -> AnalysisResult:
    """跑一次 ``Lumice analyze``：``out_dir/config.json`` + ``analysis.csv`` + ``lumice.log`` + ``provenance.json``。

    ``rays`` 缺省取 ``config["scene"]["ray_num"]``（仍显式传 ``--rays``，命令行自解释）。``symmetry`` 传给 ``--symmetry``
    原样（``none`` / P、B、D 的组合）。``local_build``：``bin`` 显式给出或走了 ``LUMICE_BIN`` 覆盖 ⇒ True，此时不填
    ``LUMICE_VERSION``（那是 release 版本号，填了就是谎称），改记二进制所在 git 仓的 HEAD + sha256 + mtime。"""
    if roi not in ROI_CHOICES:
        raise ValueError(f"roi 只能是 {ROI_CHOICES}，收到 {roi!r}")
    if symmetry != "none" and (not symmetry or set(symmetry.upper()) - set("PBD")):
        raise ValueError(f"symmetry 只能是 'none' 或 P/B/D 的组合，收到 {symmetry!r}")
    if rays is None:
        rays = config["scene"]["ray_num"]
    if isinstance(rays, bool) or not isinstance(rays, int) or rays <= 0:
        raise TypeError(f"rays 必须是正整数（analyze 不接 'infinite'），收到 {rays!r}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    local_build = bin is not None or bool(os.environ.get("LUMICE_BIN"))
    binary = Path(bin) if bin is not None else ensure_lumice()
    cfg_path = out_dir / "config.json"
    cfg_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    csv_path = out_dir / CSV_NAME
    if csv_path.exists():
        csv_path.unlink()          # out_dir 归本次分析独占，别让上次的 CSV 冒充结果

    cmd = [str(binary), "analyze", "-f", str(cfg_path), "--roi", roi, "--symmetry", symmetry, "--rays", str(rays),
           "--csv", str(csv_path)]
    if seed is not None:
        cmd += ["--seed", str(seed)]
    if workers is not None:
        cmd += ["--workers", str(workers)]
    if backend is not None:
        cmd += ["--backend", backend]

    t0 = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    wall = time.monotonic() - t0
    log_path = out_dir / "lumice.log"
    log_path.write_text(f"$ {' '.join(cmd)}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}\n")
    if proc.returncode != 0:
        tail = "\n".join(log_path.read_text().splitlines()[-30:])
        raise LumiceError(f"Lumice analyze 退出码 {proc.returncode}（命令 {' '.join(cmd)}）；log 尾部：\n{tail}")
    if not csv_path.is_file():
        raise LumiceError(f"Lumice analyze 退出码 0 但没写 {csv_path}；log：{log_path}")
    header, rows = parse_analysis_csv(csv_path.read_text())

    provenance = {
        "local_build": local_build,
        "lumice_version": None if local_build else LUMICE_VERSION,
        "lumice_bin": str(binary),
        "lumice_bin_sha256": sha256_of(binary),
        "lumice_bin_mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(binary.stat().st_mtime)),
        "lumice_git_head": _git_head(binary.resolve().parent) if local_build else None,
        "config_sha256": config_sha256(config),
        "config": json.loads(json.dumps(config)),
        "roi": roi,
        "symmetry": symmetry,
        "rays": rays,
        "seed": seed,
        "workers": workers,
        "backend": backend,
        "cli_args": cmd[1:],
        "csv": csv_path.name,
        "header": dict(header.raw),
        "total_rays": header.total_rays,
        "total_energy": header.total_energy,
        "record_full_hits": header.record_full_hits,
        "n_rows": len(rows),
        "wall_clock_s": round(wall, 3),
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
    }
    (out_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    return AnalysisResult(header=header, rows=rows, provenance=provenance, wall_clock_s=wall, out_dir=out_dir)


def load_analysis(out_dir: Path | str) -> AnalysisResult:
    """读回 :func:`run_analysis` 落盘的产物（不重跑）。"""
    out_dir = Path(out_dir)
    header, rows = parse_analysis_csv((out_dir / CSV_NAME).read_text())
    prov = json.loads((out_dir / "provenance.json").read_text())
    return AnalysisResult(header=header, rows=rows, provenance=prov, wall_clock_s=prov.get("wall_clock_s", 0.0),
                          out_dir=out_dir)


# ---------- Φ 类聚合 ----------


@dataclass
class AggregatedClass:
    """一个 Φ 类的 MC 聚合：能量份额（%）、由 ± 反推的命中数之和、finest 行数、PBD 代表数、最亮一行。"""

    energy_pct: float = 0.0
    count: float = 0.0
    n_rows: int = 0
    reps: set[tuple[int, ...]] = field(default_factory=set)
    brightest: AnalysisRow | None = None

    def add(self, row: AnalysisRow, rep: tuple[int, ...]) -> None:
        self.energy_pct += row.energy_pct
        self.count += row.count or 0.0
        self.n_rows += 1
        self.reps.add(rep)
        if self.brightest is None or row.energy_pct > self.brightest.energy_pct:
            self.brightest = row


def usable_rows(rows: Iterable[AnalysisRow]) -> list[AnalysisRow]:
    """进入互证 / 聚合的行：非 ``other``、长度 > 1（单面外反射不在 34 类框架内）、无相邻重复面。"""
    return [r for r in rows if not r.is_other and len(r.faces) > 1 and not r.has_adjacent_repeat]


def classify_rows(crystal: Polyhedron, rows: Iterable[AnalysisRow]) -> dict[PhiClass, AggregatedClass]:
    """按 Φ 类聚合 MC 行（与 ``enumerate_signatures.classify()`` 同一套 ``phi_class(crystal, fold_matrix(...), a, b)``
    调用）。key 是 :class:`PhiClass`（相等只看楔角 + 指纹），调用方用 ``PhiRow.phi_class`` 直接查表；``phi_class``
    内部已用 D6h 规范化，聚合前不需再做 PBD 归约。行先经 :func:`usable_rows` 过滤。"""
    out: dict[PhiClass, AggregatedClass] = {}
    for row in usable_rows(rows):
        faces = row.faces
        cls = phi_class(crystal, fold_matrix(crystal, faces), faces[0], faces[-1])
        out.setdefault(cls, AggregatedClass()).add(row, min(rg.pbd_orbit(faces)))
    return out


# ---------- 互证：MC 证据链与精确枚举证据链第一次相遇 ----------
# 锚点：ch10/11 姿态族任务复用时从这里进——输入只有 AnalysisRow 列表与 RaypathRecord 列表，不依赖六棱柱。


@dataclass
class CrosscheckResult:
    """``violations`` 非空就是本任务最重要的输出（枚举器漏判或判据错），调用方必须显式报出，不允许静默丢弃。"""

    violations: list[tuple[AnalysisRow, tuple[int, ...]]]      # (MC 行, 其 PBD 代表)：MC 命中但不在精确可达集
    seen: dict[tuple[int, ...], float]                           # 精确可达且 MC 命中的代表 → 该轨道 MC 能量份额之和
    unseen: list[RaypathRecord]                                  # 精确可达（长度 ≤ mc_max_len）但 MC 未命中
    uncovered: list[RaypathRecord]                               # 精确可达但长度 > mc_max_len，MC 未覆盖
    dropped_adjacent_repeat: list[AnalysisRow]                   # 相邻重复面行（不进互证）
    other_energy_pct: float                                      # ``other`` 桶能量份额
    single_face_energy_pct: float                                # 单面外反射行能量份额（不进互证）

    @property
    def dropped_energy_pct(self) -> float:
        return sum(r.energy_pct for r in self.dropped_adjacent_repeat)

    @property
    def ok(self) -> bool:
        return not self.violations


def crosscheck(rows: Iterable[AnalysisRow], exact: Iterable[RaypathRecord], *, mc_max_len: int) -> CrosscheckResult:
    """MC 命中集 ⊆ 精确可达集？``exact`` 是 ``enumerate_raypaths(..., symmetry_orbit=rg.pbd_orbit)`` 的记录（每条
    ``faces`` 已是 PBD 轨道的字典序最小代表）；MC 每行取 ``min(rg.pbd_orbit(faces))`` 对比。``mc_max_len`` 是 MC 侧
    的链面数上限（``analysis_config`` 的 ``max_len``），精确侧更长的记录归 ``uncovered`` 而非 ``unseen``。"""
    rows = list(rows)
    exact_by_rep = {rec.faces: rec for rec in exact if rec.length > 1}
    dropped = [r for r in rows if not r.is_other and len(r.faces) > 1 and r.has_adjacent_repeat]
    violations: list[tuple[AnalysisRow, tuple[int, ...]]] = []
    seen: dict[tuple[int, ...], float] = {}
    for row in usable_rows(rows):
        rep = min(rg.pbd_orbit(row.faces))
        if rep in exact_by_rep:
            seen[rep] = seen.get(rep, 0.0) + row.energy_pct
        else:
            violations.append((row, rep))
    unseen = [rec for rep, rec in exact_by_rep.items() if rep not in seen and rec.length <= mc_max_len]
    uncovered = [rec for rep, rec in exact_by_rep.items() if rep not in seen and rec.length > mc_max_len]
    unseen.sort(key=lambda r: (-r.area_sr, r.faces))
    uncovered.sort(key=lambda r: (-r.area_sr, r.faces))
    violations.sort(key=lambda t: -t[0].energy_pct)
    return CrosscheckResult(
        violations=violations, seen=seen, unseen=unseen, uncovered=uncovered, dropped_adjacent_repeat=dropped,
        other_energy_pct=sum(r.energy_pct for r in rows if r.is_other),
        single_face_energy_pct=sum(r.energy_pct for r in rows if not r.is_other and len(r.faces) == 1),
    )


# ---------- 秩相关 ----------


def spearman_rho(x: Sequence[float], y: Sequence[float]) -> float:
    """Spearman 秩相关（并列取平均秩）；长度 < 2 或任一侧全并列时返回 ``nan``。"""
    if len(x) != len(y):
        raise ValueError("x / y 长度不一致")
    if len(x) < 2:
        return math.nan

    def ranks(v: Sequence[float]) -> np.ndarray:
        a = np.asarray(v, dtype=float)
        order = np.argsort(a, kind="stable")
        r = np.empty(len(a))
        i = 0
        while i < len(a):
            j = i
            while j + 1 < len(a) and a[order[j + 1]] == a[order[i]]:
                j += 1
            r[order[i:j + 1]] = (i + j) / 2 + 1
            i = j + 1
        return r

    rx, ry = ranks(x), ranks(y)
    if rx.std() == 0 or ry.std() == 0:
        return math.nan
    return float(np.corrcoef(rx, ry)[0, 1])


__all__ = ["AggregatedClass", "AnalysisHeader", "AnalysisResult", "AnalysisRow", "CSV_NAME", "CrosscheckResult",
           "analysis_config", "classify_rows", "crosscheck", "has_adjacent_repeat", "load_analysis",
           "parse_analysis_csv", "parse_raypath", "run_analysis", "spearman_rho", "usable_rows"]
