#!/usr/bin/python
from argparse import ArgumentParser
from collections import OrderedDict
from contextlib import contextmanager
from os import getcwd, chdir
from os.path import basename
from subprocess import Popen, PIPE

from jinja2 import Environment, BaseLoader

TEMPLATE = "".join(open('template.jinja', 'r').readlines())


def __get_args():
    parser = ArgumentParser(description='formats differences between branches')
    parser.add_argument('branch', help='two branches to compare', nargs=2)
    parser.add_argument('repo', help='path to repository. defaults to cwd', nargs='?',
                        default=getcwd())
    return parser.parse_args()


@contextmanager
def __wd(chdir_path):
    old_path = getcwd()
    chdir(chdir_path)
    yield
    chdir(old_path)


@contextmanager
def __checkout(branch, repo_path=None):
    if not repo_path:
        repo_path = getcwd()
    with __wd(repo_path):
        out, err = Popen("git status".split(), stdout=PIPE, stderr=PIPE).communicate()
        oldbranch = None
        for line in [line.strip() for line in out.splitlines()]:
            if line.lower().startswith('on branch'):
                oldbranch = line.split()[-1]
                break
        out, _ = Popen("git checkout {}".format(branch).split(),
                       stdout=PIPE, stderr=PIPE).communicate()
        yield
        out, _ = Popen("git checkout {}".format(oldbranch).split(),
                       stdout=PIPE, stderr=PIPE).communicate()


def __get_differences(branch1, branch2, repo_path):
    cmd = "git diff-tree -r --diff-filter=ADM {} {}".format(branch1, branch2)
    with __wd(repo_path):
        proc = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
    lines = filter(lambda x: x, [line[1:].strip() for line in out.splitlines()])
    res_dict = OrderedDict()
    for line in lines:
        mode1, mode2, hash1, hash2, change, fpath = line.split()
        res_dict[fpath] = change
    return res_dict


def __files_from_branch(branch, repo_path):
    excluded = ['.git', '.pyc', '.idea']
    flist = set()
    with __checkout(branch, repo_path):
        out, _ = Popen("find -type f".split(), stdout=PIPE, stderr=PIPE).communicate()
        lines = [line.strip() for line in out.splitlines()]
        for line in lines:
            if not any([exc in line for exc in excluded]):
                flist.add(line[2:])
    return flist


def __get_all_files(branch1, branch2, repo_path):
    files1 = __files_from_branch(branch1, repo_path)
    files2 = __files_from_branch(branch2, repo_path)
    return files1 | files2


def get_modifications(branch1, branch2, repo_path):
    diffs = __get_differences(branch1, branch2, repo_path)
    all_ = __get_all_files(branch1, branch2, repo_path)
    changed_set = set(diffs.keys())
    all_files = all_ | changed_set
    return_dict = OrderedDict()
    for _file in sorted(all_files):
        info = diffs.get(_file)
        if not info:
            return_dict[_file] = "U"
        else:
            return_dict[_file] = info
    return return_dict


def render(rendered, repo_name, branch1, branch2):
    rtemplate = Environment(loader=BaseLoader).from_string(TEMPLATE)
    kv_data = [(k, v) for k, v in rendered.items()]
    b1, b2, m, u = 0, 0, 0, 0
    for _, status in kv_data:
        if status == 'A':
            b2 += 1
        elif status == 'D':
            b1 += 1
        elif status == 'M':
            m += 1
        elif status == 'U':
            u += 1
    rendered = rtemplate.render(files=kv_data, branch1=branch1, branch2=branch2, repo=repo_name,
                                b1=b1, b2=b2, u=u, m=m)
    print(rendered)


if __name__ == '__main__':
    args = __get_args()
    br1, br2 = args.branch
    path = args.repo
    data = get_modifications(br1, br2, path)
    repository_name = basename(path)
    if not repository_name:
        repository_name = path.split('/')[-2]
    render(data, repository_name, br1, br2)
