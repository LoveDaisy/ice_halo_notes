# 图 3b：随机取向可到达全局最低点 → ../img/random_terrain.png。
from _terrain_layers import cli, main as draw


def main(out=None):
    draw('random', out)


if __name__ == '__main__':
    cli('random')
