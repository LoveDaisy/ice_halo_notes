# 9.1 按正文图号组装待审比较版 → ../img/compare_orientation.png；版本清单 → ../data/compare_orientation.json。
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

import _orientation_fig as F

CHAPTER = Path(__file__).resolve().parents[1]
FIGURES = (
    ('1', 'axis_angle_ball', '轴角球与对应姿态'),
    ('2a', 'column_torus', '柱晶与 Parry'),
    ('2b', 'plate_lowitz', '片晶与 Lowitz'),
    ('3', 'tori_section', '两环面 · B 错层剖切'),
    ('4a', 'euler_sampling', '等步长与均匀取向'),
    ('4b', 'euler_density', '两极相对密度发散'),
    ('5a', 'sun_rotation', '绕太阳转，u 不变'),
    ('5b', 'angle_fibers', '局部辅助候选 · 参考起点的坏点'),
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(out=None):
    out = Path(out) if out else CHAPTER/'img/compare_orientation.png'
    metadata = out.with_suffix('.json') if out.parent != CHAPTER/'img' else CHAPTER/'data/compare_orientation.json'
    F.P.apply_style()
    fig, axes = plt.subplots(4, 2, figsize=(16, 22))
    rows = []
    for ax, (number, name, caption) in zip(axes.flat, FIGURES):
        image = CHAPTER/f'img/{name}.png'
        with Image.open(image) as im:
            ax.imshow(im.convert('RGB'))
        ax.axis('off')
        ax.set_title(f'图 {number}  ·  {caption}', loc='left', color=F.INK, fontsize=12, pad=12)
        rows.append(dict(figure=number, image=f'img/{name}.png', sha256=digest(image)))
    fig.subplots_adjust(left=.025, right=.975, bottom=.055, top=.91, wspace=.08, hspace=.18)
    fig.text(.03, .965, '9.1 姿态空间的形状 · 全篇必需图待审预览', color=F.INK, fontsize=21)
    fig.text(.03, .93, '第六批 · 8 张新图版。1a/b 合并；5b 降为局部辅助候选；全部待重新审看，4c 去留待裁定。', color=F.INK, fontsize=12)
    fig.text(.5, .023, '缩略图用于对照整体；逐图裁定请打开 README 中对应的原尺寸图片。', ha='center', color=F.INK, fontsize=11)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, metadata={'Software': None})
    plt.close(fig)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(dict(schema=1, compare_sha256=digest(out), figures=rows,
                                        optional_pending=['4c']), ensure_ascii=False, indent=2)+'\n')
    print(out)
    print(metadata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
