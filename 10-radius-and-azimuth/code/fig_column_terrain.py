# 图 3d：柱晶可取带始终包含赤道 → ../img/column_terrain.png。
from _terrain_layers import cli, main as draw


def main(out=None):
    draw('column', out)


if __name__ == '__main__':
    cli('column')
