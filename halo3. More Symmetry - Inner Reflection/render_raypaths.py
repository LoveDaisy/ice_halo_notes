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
SUN_ALT_LIST = [2, 5, 15, 30, 60, 75]


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

    raypaths = []
    with open('labeled_raypaths_5.csv', 'r') as fp:
        for line in fp:
            raypaths.append([int(x) for x in line.split(',')])

    exe_res = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for sun_alt in SUN_ALT_LIST:
            config_template['sun']['altitude'] = sun_alt
            for rp in raypaths:
                curr_raypath_label = rp[0]
                curr_raypath = [x for x in rp[1:] if x > 0]
                config_str = f'l{curr_raypath_label}_rp{"-".join([str(x) for x in curr_raypath])}_plt0.2_s{sun_alt}'
                curr_config_file = sub_folder.joinpath(f'{config_str}.json')
                config_template['main_image_name'] = f'{config_str}.jpg'
                config_template['ray_path_filter'][1]['path'] = curr_raypath
                
                with open(curr_config_file, mode='w') as fp:
                    json.dump(config_template, fp)


                logging.info(f'submitting config: {curr_config_file}')
                cmd = f'"{BIN_PATH}" -f "{curr_config_file}" -n 1'
                exe_res.append(executor.submit(run_cmd, cmd, timeout=60))

    logging.info('Results:')
    for f in concurrent.futures.as_completed(exe_res):
        logging.info(f.result(timeout=.5)[0])
