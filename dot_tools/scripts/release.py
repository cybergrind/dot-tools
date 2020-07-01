#!/usr/bin/env python3
import argparse
import json
import re
from glob import glob
from os.path import exists
from subprocess import run, PIPE


parser = argparse.ArgumentParser(description='release tool')
parser.add_argument('-c', '--commit', action='store_true')
parser.add_argument('-n', '--no-upload', action='store_true', default=False)
parser.add_argument('-v', '--version')
parser.add_argument('branch')
args = parser.parse_args()


def cmd(command):
    out = (run(command, stdout=PIPE, check=True, shell=True)
           .stdout.decode('utf8').split('\n'))
    return [x for x in out if x]


def git_file(branch, name):
    return '\n'.join(cmd('git show {}:{}'.format(branch, name)))


def parse_python_version(branch):
    rex = re.compile('version=.(\d+.\d+.\d+).')
    r = rex.findall(git_file(branch, 'setup.py'))
    if r:
        return r[0]
    rex = re.compile('__version__ = .(\d+.\d+.\d+).')
    for f in glob('*/__init__.py'):
        r = rex.findall(git_file(branch, f))
        if r:
            return r[0]


def parse_version(branch):
    if args.version:
        return args.version
    elif exists('package.json'):
        return json.loads(git_file(branch, 'package.json'))['version']
    elif exists('setup.py'):
        version = parse_python_version(branch)
        if version:
            return version
        else:
            print('Cannot determine version. Please pass it with `-v` option')
            exit(1)
    raise NotImplementedError


def prompt(question):
    if input('{} Y/n:\n'.format(question)).lower() == 'y':
        return True


def commit_cmd(command):
    if args.commit:
        cmd(command)
    else:
        print('Skip command: {}'.format(command))


def get_current_branch():
    return cmd('git rev-parse --abbrev-ref HEAD')[0]


def get_tag():
    return parse_version(args.branch)


def checkout(branch):
    cmd('git checkout {}'.format(branch))


def tag_exists(tag):
    tags = cmd('git tag -l')
    return tag in tags


def merge(branch):
    commit_cmd('git merge --ff-only {}'.format(branch))


def push():
    commit_cmd('git push')


def tag_create(tag):
    commit_cmd('git tag -am {0} {0}'.format(tag))


def tags_push():
    commit_cmd('git push --tags')


def npm_publish():
    if exists('.npmignore') and not exists('.npmnotpublic'):
        commit_cmd('npm publish')


def pypi_publish():
    commit_cmd('rm -rf dist/*')
    commit_cmd('hatch build')
    commit_cmd('hatch release')


def publish():
    if exists('package.json'):
        npm_publish()
    elif exists('setup.py'):
        pypi_publish()


def release_run():
    tag = get_tag()

    if tag_exists(tag):
        print('Tag {!r} is already exists'.format(tag))
        exit(1)

    merge(args.branch)
    push()
    tag_create(tag)
    tags_push()
    if not args.no_upload:
        publish()


def main():
    print('Args: {}'.format(args))
    curr_branch = get_current_branch()
    if curr_branch == 'HEAD':
        print('Cannot operate in detached branch')
        exit(1)
    elif curr_branch not in ('master', 'staging'):
        if not prompt('Do you want go with {!r}'.format(curr_branch)):
            exit(0)

    if not exists('package.json') and not exists('setup.py'):
        print('We support only node/pypi libraries releases for now')
        exit(1)

    release_run()


if __name__ == '__main__':
    main()
