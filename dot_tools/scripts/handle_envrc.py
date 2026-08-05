#!/usr/bin/env python3
"""
This should solve saving/syncing private `.envrc` files across different devices.
We're going to use some shared (autosynced) encrypted storage for these files.

We can have such cases for .envrc files:

1. .envrc specific for some repository. Eg. some keys or external variables
2. .envrc specific for some directory

Automatic mode will:

1. If we have `.envrc` for current repo/directory but don't have actual link in cwd
   In that case script will create link from `ENVRC_HOME` to current directory
2. If we have `.envrc` that isn't commited and isn't a link
   Move it to `ENVRC_HOME` and replace with link

`handle_envrc migrate` moves the storage from the previous location (`--old`) to the
current `ENVRC_HOME`, re-points all symlinks found under `--root` (default: ~/devel)
and re-approves relinked `.envrc` files with `direnv allow`.
"""

import argparse
import asyncio
import hashlib
import logging
import os
import shutil
import sys

from fan_tools.unix import ExecError, asucc


ENVRC_HOME = 'ENVRC_HOME'
LEGACY_PATH = '~/Yandex.Disk/home/envrc'
BASE_PATH = os.path.expanduser(os.environ.get(ENVRC_HOME, '~/.keys/envrc'))
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('handle_envrc')
ENVRC = '.envrc'
ROOT_DIR: str = ''
SHARED_DIR: str = ''
IGNORE_FILES = ['url']
SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.cache', '.tox', '.mypy_cache'}


def set_root_dir():
    global ROOT_DIR

    if not ROOT_DIR:
        level = 0
        fpath = '.'
        while os.path.dirname(fpath) != '/':
            lvl = ['..' for i in range(level)]
            lvl.append('.git')
            fpath = os.path.join(*lvl)
            if os.path.exists(fpath):
                ROOT_DIR = os.path.abspath(os.path.join(fpath, '..'))
                break
            level += 1
    return ROOT_DIR


def set_shared_dir(args):
    global SHARED_DIR
    if not SHARED_DIR:
        md5 = hashlib.md5(args.url.encode('utf8')).hexdigest()
        SHARED_DIR = os.path.join(BASE_PATH, md5)
    return SHARED_DIR


def parse_args():
    parser = argparse.ArgumentParser(description='Keep .envrc files in-sync')
    parser.add_argument('-m', '--mode', default='auto', choices=['auto'])
    parser.add_argument('file', nargs='?', help='File to store not in git')
    return parser.parse_args()


def parse_migrate_args(argv):
    parser = argparse.ArgumentParser(
        prog='handle_envrc migrate',
        description=f'Move shared storage to `{ENVRC_HOME}` location and re-point all symlinks',
    )
    parser.add_argument('--old', default=LEGACY_PATH, help='previous storage location')
    parser.add_argument(
        '--root',
        dest='roots',
        action='append',
        help='where to search for symlinks, repeatable (default: ~/devel)',
    )
    parser.add_argument('--max-depth', type=int, default=6)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if not args.roots:
        args.roots = ['~/devel']
    return args


def move_and_link():
    pass


def check_env_exists():
    pass


def link():
    pass


async def get_url():
    try:
        _, out, _ = await asucc('git config --get remote.origin.url')
        if len(out) == 1:
            return out[0]
    except ExecError:
        return None


def has_envrc_link():
    return os.path.exists(ENVRC) and os.path.islink(ENVRC)


def has_envrc_file():
    return os.path.exists(ENVRC) and not os.path.islink(ENVRC)


def envrc_exists():
    return os.path.exists(SHARED_DIR)


def create_shared(args):
    if not os.path.exists(SHARED_DIR):
        os.makedirs(SHARED_DIR, exist_ok=True)
        with open(os.path.join(SHARED_DIR, 'url'), 'w') as f:
            f.write(args.url)


def add_file(args, fname):
    if not os.path.exists(fname):
        raise Exception(f'No file: {fname}')
    tgt = os.path.abspath(fname)
    if os.path.islink(tgt):
        print(f'Path is already link: {tgt}')
        return
    bname = '.' + tgt.replace(ROOT_DIR, '')
    print(f'BNAME: {bname} [{ROOT_DIR}] => [{SHARED_DIR}]')
    src = os.path.abspath(os.path.join(SHARED_DIR, bname))
    dsrc = os.path.dirname(src)
    if not os.path.exists(dsrc):
        os.makedirs(dsrc, exist_ok=True)
    ren = shutil.move(tgt, src)
    print(f'Move result: {ren} {tgt} => {src} [{SHARED_DIR}]')
    os.symlink(src, tgt)


async def link_from_shared_env(args):
    # link external files here
    for base, _dirs, files in os.walk(SHARED_DIR):
        if base == SHARED_DIR:
            files = [x for x in files if x not in IGNORE_FILES]
        # print(f'Walk: {base} Dirs: {dirs} Files: {files}')
        dname = '.' + base.replace(SHARED_DIR, '')
        ldir = os.path.abspath(os.path.join(ROOT_DIR, dname))

        if os.path.exists(ldir) and files:
            for fname in files:
                src = os.path.join(base, fname)
                tgt = os.path.join(ldir, fname)
                if os.path.exists(tgt):
                    if os.path.islink(tgt):
                        print(f'Path already linked: {tgt}')
                        continue
                    raise Exception(f'File already exists: {tgt} Ignore overriwriting')
                else:
                    print(f'Link: {src} => {tgt}')
                    os.symlink(src, tgt)
                    if fname == ENVRC:
                        await asucc(f'direnv allow {ldir}')


def iter_symlinks(roots, max_depth):
    for root in roots:
        root = os.path.abspath(os.path.expanduser(root))
        base_depth = root.rstrip('/').count('/')
        for base, dirs, files in os.walk(root):
            if base.count('/') - base_depth >= max_depth:
                dirs[:] = []
            else:
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                fpath = os.path.join(base, fname)
                if os.path.islink(fpath):
                    yield fpath


async def migrate(args):
    old = os.path.abspath(os.path.expanduser(args.old))
    new = BASE_PATH
    if os.path.realpath(old) == os.path.realpath(new):
        log.error(f'Old and new locations are the same: {old}. Set `{ENVRC_HOME}`?')
        exit(1)
    if not os.path.exists(old) and not os.path.exists(new):
        log.error(f'Neither {old} nor {new} exists. Nothing to migrate')
        exit(1)

    if os.path.exists(old):
        print(f'Copy storage: {old} => {new}')
        if not args.dry_run:
            shutil.copytree(old, new, dirs_exist_ok=True)

    prefix = old.rstrip('/') + '/'
    relinked, allowed, missing = 0, 0, 0
    for fpath in iter_symlinks(args.roots, args.max_depth):
        target = os.readlink(fpath)
        if not target.startswith(prefix):
            continue
        new_target = os.path.join(new, target[len(prefix) :])
        if not os.path.exists(new_target) and not args.dry_run:
            log.warning(f'No migrated target for {fpath}: {new_target}')
            missing += 1
            continue
        print(f'Relink: {fpath} => {new_target}')
        relinked += 1
        if os.path.basename(fpath) == ENVRC:
            allowed += 1
        if not args.dry_run:
            os.remove(fpath)
            os.symlink(new_target, fpath)
            if os.path.basename(fpath) == ENVRC:
                await asucc(f'direnv allow {fpath}')
    action = 'Would relink' if args.dry_run else 'Relinked'
    print(f'{action}: {relinked} direnv allowed: {allowed} missing targets: {missing}')
    if not args.dry_run and relinked:
        print(f'Old storage left untouched: {old}. Remove it manually after checking all machines')


async def run(args):
    url = await get_url()
    if url is None:
        log.info('There is no git repo here. Do nothing')
        return
    else:
        print(f'Url is: {url}')
        args.url = url
        set_root_dir()
        set_shared_dir(args)

    if has_envrc_link() and args.file is None:
        return
    elif has_envrc_file() or args.file is not None:
        # handle creation
        create_shared(args)
        if args.file:
            add_file(args, args.file)
        if has_envrc_file():
            add_file(args, ENVRC)

    if envrc_exists():
        await link_from_shared_env(args)


def get_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    return loop


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        args = parse_migrate_args(sys.argv[2:])
        get_loop().run_until_complete(migrate(args))
        return

    args = parse_args()
    if not os.path.exists(BASE_PATH):
        log.error(
            f"`{BASE_PATH}` doesn't exist. Please create it/sync/set variable "
            f'`{ENVRC_HOME}` with correct path'
        )
        exit(1)
    get_loop().run_until_complete(run(args))


if __name__ == '__main__':
    main()
