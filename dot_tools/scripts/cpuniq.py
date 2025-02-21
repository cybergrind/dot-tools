#!/usr/bin/env python3
import argparse
import logging
import shutil
from pathlib import Path
from subprocess import run
from uuid import uuid4


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('cpuniq')


def parse_args():
    parser = argparse.ArgumentParser(
        description='copy file, preserve name if can and make uniq if cannot'
    )
    parser.add_argument(
        '-m', '--mode', default='copy', choices=['copy', 'move', 'cp', 'mv'], help='copy or move'
    )
    parser.add_argument('files', nargs='+', help='src')
    parser.add_argument('dst', nargs=1)
    parser.add_argument('-v', '--verbose', default=False, action='store_true')

    return parser.parse_args()


def gen():
    yield ''
    while True:
        uuid = uuid4().hex
        yield f'.{uuid}'


def identical_files(src: Path, dst: Path):
    """
    1. by size
    2. by hash
    """
    try:
        if not dst.exists():
            return False
        if src.stat().st_size != dst.stat().st_size:
            return False
        sha_src = run(['sha1sum', src], capture_output=True).stdout.split()[0]
        sha_dst = run(['sha1sum', dst], capture_output=True).stdout.split()[0]
        if sha_src != sha_dst:
            return False
        return True
    except Exception:
        log.exception('Error while comparing files')
        return False


def copy(src: Path, dst_dir: Path, args):
    if not src.exists():
        log.error(f'File does not exist: {src}')
        return None

    if src.parent == dst_dir:
        log.info(f'File is already in target dir: {src} => {dst_dir}')
        return src

    dst_path = src
    for suffix in gen():
        new_name = f'{src.stem}{suffix}{src.suffix}'
        dst_path = Path(dst_dir, new_name)
        log.info(f'Checking: {dst_path} vs {src}')

        if identical_files(src, dst_path):
            log.debug(f'Identical files: {src} => {dst_path}')
            if args.mode in ['move', 'mv']:
                src.unlink()

            return dst_path

        if dst_path.exists():
            continue
        break

    log.debug(f'Moving: {src} => {dst_path}')
    if args.mode in ['move', 'mv']:
        shutil.move(src, dst_path)
    else:
        shutil.copy(src, dst_path)
    return dst_path


def main():
    args = parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARN)

    dst = Path(args.dst[0])
    if not dst.exists():
        log.error(f'Destination does not exist: {dst}')
        exit(1)

    for fname in args.files:
        src = Path(fname)
        copy(src, dst, args)


if __name__ == '__main__':
    main()
