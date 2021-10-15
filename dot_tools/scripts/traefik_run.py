#!/usr/bin/env python3
import argparse
import logging
from itertools import chain

from fan_tools.python import rel_path
from fan_tools.unix import succ

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('traefik_run')


def parse_args():
    parser = argparse.ArgumentParser(description='runs local traefik')
    parser.add_argument('cmd', nargs='?', default=['up', '-d'])
    parser.add_argument('-u', '--usage', action='store_true')
    return parser.parse_args()


def run_traefik(args):
    compose = rel_path('../resources/traefik.compose.yaml')
    cmd = ' '.join(args.cmd)

    full_cmd = f'docker-compose -p traefik -f {compose} {cmd}'
    log.debug(f'Run: {full_cmd}')
    code, out, err = succ(full_cmd)
    for line in chain(out, err):
        print(line)


HOW = '''
# Example for labels section below:
# you need to change Host + `pl_prod` to something else
# for local server you don't need to have redirect and can omit websecure part

# labels:

    - "traefik.enable=true"
    - "traefik.http.routers.pl_prod_http.rule=Host(`perfectlabel.io`)"
    - "traefik.http.routers.pl_prod_http.entrypoints=web"
    - "traefik.http.routers.pl_prod_http.middlewares=pl_prod_http"

# this for https:

    - "traefik.http.routers.pl_prod.entrypoints=websecure"
    - "traefik.http.routers.pl_prod.rule=Host(`perfectlabel.io`)"
    - "traefik.http.routers.pl_prod.tls.certresolver=lets"
    - "traefik.http.routers.pl_prod.tls=true"

# redirect http => https
    - "traefik.http.middlewares.pl_prod_http.redirectscheme.scheme=https"

'''


def print_how():
    print(HOW)


def main():
    args = parse_args()
    if args.usage:
        print_how()
    else:
        run_traefik(args)


if __name__ == '__main__':
    main()
