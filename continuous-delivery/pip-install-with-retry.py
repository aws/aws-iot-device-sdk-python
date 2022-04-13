import time
import sys
import subprocess

DOCS = """Given cmdline args, executes: python3 -m pip install [args...]
Keeps retrying until the new version becomes available in pypi (or we time out)"""
if len(sys.argv) < 2:
    sys.exit(DOCS)

RETRY_INTERVAL_SECS = 10
GIVE_UP_AFTER_SECS = 60 * 15

pip_install_args = [sys.executable, '-m', 'pip', 'install'] + sys.argv[1:]

start_time = time.time()
while True:
    print(subprocess.list2cmdline(pip_install_args))
    result = subprocess.run(pip_install_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    stdout = result.stdout.decode().strip()
    if stdout:
        print(stdout)

    if result.returncode == 0:
        # success
        sys.exit(0)

    if "could not find a version" in stdout.lower():
        elapsed_secs = time.time() - start_time
        if elapsed_secs < GIVE_UP_AFTER_SECS:
            # try again
            print("Retrying in", RETRY_INTERVAL_SECS, "secs...")
            time.sleep(RETRY_INTERVAL_SECS)
            continue
        else:
            print("Giving up on retries after", int(elapsed_secs), "total secs.")

    # fail
    sys.exit(result.returncode)
