# 图 3a：3–5 光路的光学定义域与等值线 → ../img/terrain_domain.png。
from _terrain_layers import cli, main as draw


def main(out=None):
    draw('domain', out)


if __name__ == '__main__':
    cli('domain')
