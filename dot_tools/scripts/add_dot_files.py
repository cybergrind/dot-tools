#!/usr/bin/env python3
import argparse
import logging
from fan_tools.python import rel_path
from pathlib import Path


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('add_dot_files')


TMPL_DIR = rel_path('../templates/')


TEMPLATES = {
    TMPL_DIR / 'editorconfig.tmpl': {
        'path': Path('.editorconfig'),
    },
    TMPL_DIR / 'pyproject.tmpl': {
        'path': Path('pyproject.toml'),
    },
    TMPL_DIR / 'projectile.tmpl': {
        'path': Path('.projectile'),
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description='DESCRIPTION')
    # parser.add_argument('-m', '--mode', default='auto', choices=['auto', 'manual'])
    # parser.add_argument('-l', '--ll', dest='ll', action='store_true', help='help')
    return parser.parse_args()


def create_templates(args):
    for src, dct in TEMPLATES.items():
        if dct['path'].exists():
            print(f'Skip writting {dct["path"]}. Already exists')
            continue
        print(f'Writting {dct["path"]}')
        dct['path'].write_bytes(src.read_bytes())


def main():
    args = parse_args()
    create_templates(args)


if __name__ == '__main__':
    main()
