import re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from mtwlib import Ssh
from settings import USERNAME, PASSWORD


def exec_commands(host, commands):
    results = {}
    with Ssh(host, USERNAME, PASSWORD, colored=False) as ssh:
        with ssh.safe_mode():
            for cmd in commands:
                ssh.send(cmd+'\r\n')
                time.sleep(0.1)
                output = ssh.read_all()
                results[cmd] = search.group(1) if (search := re.search(
                    r'{}(?:[\r\n]*)(.*?)(?:[\r\n]*)\[{}'.format(
                        cmd+'\r\n',
                        USERNAME
                    ),
                    output,
                    re.MULTILINE | re.DOTALL
                )) else output
    return {host: results}


def run_template(body):
    results = {}
    with ThreadPoolExecutor() as executor:
        futures = []
        for host in body['hosts']:
            futures.append(
                executor.submit(exec_commands, host, body['commands'])
            )
        for future in as_completed(futures):
            try:
                results.update(future.result())
            finally:  # TODO add exceptions handling
                pass
        return results, 200
