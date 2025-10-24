#!/usr/bin/env python3
import sys

from time import time

import os
import logging
import re
import subprocess
from argparse import ArgumentParser

logging.basicConfig(format='%(levelname)s: %(message)s',
                    level=logging.INFO)

script_name = os.path.basename(__file__)
log = logging.getLogger(script_name)

parser = ArgumentParser(script_name)
parser.add_argument('--dry-run', action='store_true', required=False)
parser.add_argument('--pre-release', required=False)  # a=alpha, b=beta, rc=release-candidate
parser.add_argument('--add-random-bit', action='store_true', required=False)
parser.add_argument('--ignore-unsaved', action='store_true', required=False)
parser.add_argument('--version', required=False)
args = parser.parse_args()


def main():
    in_dry_run_mode = args.dry_run

    # Check for uv availability
    if not in_dry_run_mode:
        log.info('Checking for uv availability...')
        try:
            subprocess.check_output(['uv', '--version'], stderr=subprocess.STDOUT)
            log.info('uv is available')
        except (subprocess.CalledProcessError, FileNotFoundError):
            log.error('uv is not installed. Please install uv first: https://astral.sh/uv')
            sys.exit(1)

    # Determine the release version
    if args.version:
        release_version = args.version
    else:
        changes = [
            (change_type, file_path)
            for change_type, file_path in [
                re.split(r' +', line.strip())
                for line in subprocess.check_output(['git', 'status', '--short', '-uno'],
                                                    universal_newlines=True).split('\n')
                if line
            ]
            if not file_path.startswith('scripts') and file_path not in ('cloudbuild.yaml', 'Makefile')
        ]
        if changes and not args.ignore_unsaved:
            log.warning('Changes detected:')
            for change_type, file_path in changes:
                log.warning(f' - [{change_type}] {file_path}')
            log.error('Please commit the changes or stash them before running this script.')
            sys.exit(1)

        log.info('Determining the release version...')
        git_version = subprocess.check_output(['git', 'describe'], universal_newlines=True).strip()
        log.info(f'Version/GIT: {git_version}')

        try:
            base_version, revision_number, __ = git_version.split(r'-')
        except ValueError:
            base_version = git_version
            revision_number = '0'

        # Strip 'v' prefix if present (git tags often use v3.1 format)
        base_version = base_version.lstrip('v')

        split_base_version = base_version.split(r'.')
        major_version = split_base_version[0]
        minor_version = split_base_version[1]

        release_version = f'{major_version}.{minor_version}.{revision_number}'

    if args.pre_release:
        release_version = release_version + args.pre_release
        if args.add_random_bit:
            release_version = release_version + str(int(time()))

    log.info(f'Version/Release: {release_version}')

    # Update dnastack.constants
    with open('dnastack/constants.py', 'r') as f:
        content = f.read()
    content = re.sub(r'__version__\s*=\s*[^\s]+', f'__version__ = "{release_version}"', content)
    if in_dry_run_mode:
        log.info(f'dnastack.constants:\n\n{content}')
    else:
        with open('dnastack/constants.py', 'w') as f:
            f.write(content)

    # Update pyproject.toml
    pyproject_file_path = 'pyproject.toml'
    with open(pyproject_file_path, 'r') as f:
        pyproject_content = f.read()
    
    # Replace the version in pyproject.toml
    pyproject_content = re.sub(r'(version\s*=\s*")[^"]+(")', fr'\g<1>{release_version}\g<2>', pyproject_content)
    
    if in_dry_run_mode:
        log.info(f'pyproject.toml (version section):\n\nversion = "{release_version}"')
    else:
        with open(pyproject_file_path, 'w') as f:
            f.write(pyproject_content)

    # Build the package
    if args.dry_run:
        log.warning('The package will not be built because the script is in the dry run mode.')
    else:
        log.info('Building the package with uv...')
        subprocess.call(['uv', 'build'])

    log.info('Cleaning up...')

    subprocess.call(['git', 'checkout', '--', 'pyproject.toml', 'dnastack/constants.py'])

    log.info('Done')


if __name__ == '__main__':
    main()
