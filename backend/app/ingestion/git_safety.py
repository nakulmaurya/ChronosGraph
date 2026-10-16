"""Noninteractive Git subprocess defaults; not an untrusted-repository sandbox."""
import os


def git_environment():
    # Do not honor caller-selected gitdirs, indexes, config injection or askpass.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT='0', GIT_PAGER='cat', GIT_ATTR_NOSYSTEM='1',
               GIT_OPTIONAL_LOCKS='0')
    return env


def git_command():
    return ['git', '-c', 'core.hooksPath='+os.devnull, '-c', 'core.fsmonitor=false',
            '-c', 'core.attributesFile='+os.devnull, '-c', 'credential.helper=',
            '-c', 'init.templateDir=', '-c', 'protocol.allow=never',
            '-c', 'protocol.https.allow=always', '-c', 'protocol.file.allow=always']
