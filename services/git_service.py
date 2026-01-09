from utils.logging_helper import set_logger
import os
import platform
import subprocess
import json





class GitService:

    def __init__(self):
        self.logger = set_logger("GitService")

    def git_update(self):
        try:
            path = os.path.abspath(os.path.dirname(__file__))
            self.logger.info(f"Starting git update in {path}")

            # Detect the original user
            orig_user = os.environ.get('SUDO_USER') or os.environ.get('USER')
            self.logger.info(f"Running git as user: {orig_user}")

            def run_git_cmd(args):
                if platform.system() != 'Windows':
                    # Only check geteuid on Unix
                    if hasattr(os, 'geteuid') and os.geteuid() == 0 and orig_user and orig_user != 'root':
                        cmd = ['sudo', '-u', orig_user] + args
                    else:
                        cmd = args
                else:
                    # On Windows, just run as current user
                    cmd = args
                return subprocess.run(cmd, cwd=path, capture_output=True, text=True)

            cur_commit = run_git_cmd(['git', 'rev-parse', 'HEAD']).stdout.strip()
            self.logger.info(f"Current commit: {cur_commit}")

            pull_proc = run_git_cmd(['git', 'pull', '--ff-only'])
            pull_out = pull_proc.stdout.strip()
            pull_err = pull_proc.stderr.strip()
            self.logger.info(f"Git pull output: {pull_out}")
            if pull_err:
                self.logger.warning(f"Git pull error: {pull_err}")

            new_commit = run_git_cmd(['git', 'rev-parse', 'HEAD']).stdout.strip()
            self.logger.info(f"New commit: {new_commit}")

            if cur_commit != new_commit:
                self.logger.info("Code updated, restarting application...")
                if self.is_running:
                    self.stop_main()
                self.start_main()
                status = {"status": "updated", "commit": new_commit}
            else:
                self.logger.info("No update detected.")
                status = {"status": "no_update", "commit": new_commit}
            self.send_status(json.dumps(status))
        except Exception as e:
            self.logger.error(f"Error during git update: {e}")
            self.send_status(f"error:{str(e)}")