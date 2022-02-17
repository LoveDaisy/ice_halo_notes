#!/usr/local/bin/python3

import json
import logging
import shutil
import concurrent.futures
from pathlib import Path
from socket import timeout
from subprocess import (Popen, PIPE)
from threading import Timer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s](%(thread)d): %(message)s')

CWD = Path(__file__).parent.resolve()
TEMPLATE_PATH = CWD.joinpath('template.json')
DATA_PATH = CWD.joinpath('halo image')
BIN_PATH = CWD.joinpath('IceHaloEndless')

# All raypaths less than 3 faces
# RAYPATH_INFO = [
#     {'raypath': [1], 'intensity':[2, 10], 'num': 10},
#     {'raypath': [1, 2], 'intensity':[], 'num': 0},
#     {'raypath': [1, 2, 1], 'intensity':[2, 10], 'num': 10},
#     {'raypath': [1, 2, 3], 'intensity':[10, 50], 'num': 60},
#     {'raypath': [1, 3], 'intensity':[2, 10], 'num': 30},
#     {'raypath': [1, 3, 2], 'intensity':[10], 'num': 30},
#     {'raypath': [3], 'intensity':[10], 'num': 10},
#     {'raypath': [3, 1], 'intensity':[], 'num': []},
#     {'raypath': [3, 1, 2], 'intensity':[], 'num': []},
#     {'raypath': [3, 1, 5], 'intensity':[1, 10], 'num': 30},
#     {'raypath': [3, 1, 6], 'intensity':[2, 10], 'num': 30},
#     {'raypath': [3, 4, 5], 'intensity':[], 'num': []},
#     {'raypath': [3, 5], 'intensity':[10, 50], 'num': 200},
#     {'raypath': [3, 5, 7], 'intensity':[], 'num': []},
#     {'raypath': [3, 5, 8], 'intensity':[], 'num': []},
#     {'raypath': [3, 6], 'intensity':[], 'num': []},
#     {'raypath': [3, 6, 3], 'intensity':[], 'num': []},
#     {'raypath': [3, 6, 4], 'intensity':[], 'num': []},
# ]
RAYPATH_INFO = [
    {'raypath': [1], 'intensity':[10], 'num': 20},
    # {'raypath': [1, 2], 'intensity':[10], 'num': 20},
    {'raypath': [1, 2, 1], 'intensity':[10], 'num': 20},
    {'raypath': [1, 2, 3], 'intensity':[10], 'num': 20},
    {'raypath': [1, 3], 'intensity':[10], 'num': 20},
    {'raypath': [1, 3, 2], 'intensity':[10], 'num': 20},
    {'raypath': [3], 'intensity':[10], 'num': 20},
    {'raypath': [3, 1], 'intensity':[10], 'num': 20},
    {'raypath': [3, 1, 2], 'intensity':[10], 'num': 20},
    {'raypath': [3, 1, 5], 'intensity':[10], 'num': 20},
    {'raypath': [3, 1, 6], 'intensity':[10], 'num': 20},
    {'raypath': [3, 4, 5], 'intensity':[10], 'num': 20},
    {'raypath': [3, 5], 'intensity':[10], 'num': 20},
    {'raypath': [3, 5, 7], 'intensity':[10], 'num': 20},
    {'raypath': [3, 5, 8], 'intensity':[10], 'num': 20},
    # {'raypath': [3, 6], 'intensity':[10], 'num': 20},
    {'raypath': [3, 6, 3], 'intensity':[10], 'num': 20},
    {'raypath': [3, 6, 4], 'intensity':[10], 'num': 20},
]


def run_cmd(cmd: str, timeout: float) -> tuple:
    logging.info(f'Running cmd: {cmd}')
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

    ret, std_out, std_err = -1, None, None
    timer = Timer(timeout, proc.kill)
    try:
        timer.start()
        std_out, std_err = proc.communicate()
    finally:
        timer.cancel()
        ret = proc.returncode
        if ret != 0:
            logging.error(f'run cmd FAILED! ret: {ret}')
            logging.error(f'{cmd}')
            logging.info(f'stdout: {std_out.decode()}')
            logging.error(f'stderr: {std_err.decode()}')

    return ret, std_out, std_err


if __name__ == '__main__':
    with open(TEMPLATE_PATH, mode='r') as fp:
        config_template = json.load(fp)

    run_idx = 0
    sub_folder = DATA_PATH.joinpath(f'{run_idx:02d}')
    sub_folder.mkdir(parents=True, exist_ok=True)
    config_template['data_folder'] = f'{sub_folder.resolve()}'

    sun_alt = 80
    config_template['sun']['altitude'] = sun_alt

    exe_res = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for rp_info in RAYPATH_INFO:
            raypath = rp_info['raypath']
            config_template['ray_path_filter'][1]['path'] = raypath

            for intensity in rp_info['intensity']:
                config_template['render']['intensity_factor'] = intensity

                config_str = f'rp{"-".join([str(x) for x in raypath])}_rnd1.0_s{sun_alt}_i{intensity}'
                curr_config_file = sub_folder.joinpath(f'{config_str}.json')
                config_template['main_image_name'] = f'{config_str}.jpg'

                with open(curr_config_file, mode='w') as fp:
                    json.dump(config_template, fp)

                logging.info(f'submitting config: {curr_config_file}')
                cmd = f'"{BIN_PATH}" -f "{curr_config_file}" -n {rp_info["num"]}'
                exe_res.append(executor.submit(run_cmd, cmd, timeout=60))

    logging.info('Results:')
    for f in concurrent.futures.as_completed(exe_res):
        logging.info(f.result(timeout=.5)[0])
