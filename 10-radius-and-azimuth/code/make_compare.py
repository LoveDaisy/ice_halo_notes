# ch10 按正文图号拼版 → ../img/compare_radius.png；版本清单 → ../data/compare_radius.json。
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from fig_plate_terrain import P, plt

CHAPTER = Path(__file__).resolve().parents[1]
FIGURES = (
    ('1', 'sky_comparison', '同路、三族、四个太阳高度'),
    ('2', 'solar_circle', '绕太阳转，角距离不变'),
    ('3a', 'terrain_domain', '同一张光学地形'),
    ('3b', 'random_terrain', '随机取向：全局最低点'),
    ('3c', 'plate_terrain', '片晶：纬线上的最低点'),
    ('3d', 'column_terrain', '柱晶：含赤道的带'),
    ('4', 'bravais_prism', '沿棱守恒与截面折射'),
    ('5', 'parhelion_rulers', '角距离与方位差'),
    ('6', 'tangent_direction', '正穿、斜穿与切弧半径'),
    ('7', 'column_sky', '同心圆与真实亮段'),
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(out=None):
    out = Path(out) if out else CHAPTER/'img/compare_radius.png'
    metadata = out.with_suffix('.json') if out.parent != CHAPTER/'img' else CHAPTER/'data/compare_radius.json'
    P.apply_style()
    fig, axes = plt.subplots(5, 2, figsize=(16, 23))
    rows = []
    for ax, (number, name, caption) in zip(axes.flat, FIGURES):
        image = CHAPTER/f'img/{name}.png'
        with Image.open(image) as im:
            ax.imshow(im.convert('RGB'))
        ax.axis('off')
        ax.set_title(f'图 {number}  ·  {caption}', loc='left', color=P.PAL['ink_soft'], fontsize=12, pad=12)
        rows.append(dict(figure=number, image=f'img/{name}.png', sha256=digest(image)))
    fig.subplots_adjust(left=.025, right=.975, bottom=.04, top=.92, wspace=.08, hspace=.20)
    fig.text(.03, .975, 'ch10 圈圈圆圆圈圈 · 十图预览', color=P.PAL['ink_soft'], fontsize=21)
    fig.text(.03, .946, '第十批 · 仅图 5 改为单幅透视球面图，待复审；其余九图保持已认可版本。图 8 已裁定省略。', color=P.PAL['ink_soft'], fontsize=12)
    fig.text(.5, .017, '缩略图用于整体比较；逐图裁定请打开 README 中的原尺寸图。', ha='center', color=P.PAL['ink_soft'], fontsize=11)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180, metadata={'Software': None})
    plt.close(fig)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(dict(schema=1, compare_sha256=digest(out), figures=rows,
                                        optional_pending=[], optional_omitted=['8']), ensure_ascii=False, indent=2)+'\n')
    print(out)
    print(metadata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
