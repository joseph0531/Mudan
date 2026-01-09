#!/usr/bin/env python3

import os
import platform
import subprocess
from typing import Optional, Callable, Dict, Tuple
from utils.logging_helper import set_logger


class GitService:
    """獨立的 Git 服務類，處理所有 Git 相關功能"""
    
    def __init__(self, repo_path: Optional[str] = None, 
                 update_callback: Optional[Callable[[bool, str], None]] = None):
        """
        初始化 Git 服務
        
        Args:
            repo_path: Git 倉庫路徑，如果為 None 則使用當前文件所在目錄
            update_callback: 更新完成後的回調函數，接收 (has_update: bool, commit_hash: str) 作為參數
        """
        if repo_path is None:
            repo_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        
        self._repo_path = repo_path
        self._update_callback = update_callback
        self._logger = set_logger('GitService')
        
    def set_update_callback(self, callback: Callable[[bool, str], None]):
        """
        設置更新回調函數
        
        Args:
            callback: 回調函數，接收 (has_update: bool, commit_hash: str) 作為參數
        """
        self._update_callback = callback
        self._logger.info("Update callback updated")
    
    def _run_git_cmd(self, args: list) -> subprocess.CompletedProcess:
        """
        執行 Git 命令
        
        Args:
            args: Git 命令參數列表
            
        Returns:
            subprocess.CompletedProcess: 命令執行結果
        """
        # Detect the original user
        orig_user = os.environ.get('SUDO_USER') or os.environ.get('USER')
        
        if platform.system() != 'Windows':
            # Only check geteuid on Unix
            if hasattr(os, 'geteuid') and os.geteuid() == 0 and orig_user and orig_user != 'root':
                cmd = ['sudo', '-u', orig_user] + args
            else:
                cmd = args
        else:
            # On Windows, just run as current user
            cmd = args
        
        return subprocess.run(cmd, cwd=self._repo_path, capture_output=True, text=True)
    
    def get_current_commit(self) -> Optional[str]:
        """
        獲取當前 commit hash
        
        Returns:
            Optional[str]: 當前 commit hash，如果失敗則返回 None
        """
        try:
            result = self._run_git_cmd(['git', 'rev-parse', 'HEAD'])
            if result.returncode == 0:
                commit = result.stdout.strip()
                self._logger.info(f"Current commit: {commit}")
                return commit
            else:
                self._logger.error(f"Failed to get current commit: {result.stderr}")
                return None
        except Exception as e:
            self._logger.error(f"Error getting current commit: {e}")
            return None
    
    def pull(self, fast_forward_only: bool = True) -> Tuple[bool, str, str]:
        """
        執行 git pull 操作
        
        Args:
            fast_forward_only: 是否只允許 fast-forward 合併
            
        Returns:
            Tuple[bool, str, str]: (是否成功, stdout, stderr)
        """
        try:
            if fast_forward_only:
                result = self._run_git_cmd(['git', 'pull', '--ff-only'])
            else:
                result = self._run_git_cmd(['git', 'pull'])
            
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if result.returncode == 0:
                self._logger.info(f"Git pull successful: {stdout}")
                if stderr:
                    self._logger.warning(f"Git pull stderr: {stderr}")
                return True, stdout, stderr
            else:
                self._logger.error(f"Git pull failed: {stderr}")
                return False, stdout, stderr
                
        except Exception as e:
            self._logger.error(f"Error during git pull: {e}")
            return False, "", str(e)
    
    def update(self) -> Dict[str, any]:
        """
        執行完整的 Git 更新流程（獲取當前 commit -> pull -> 檢查是否有更新）
        
        Returns:
            Dict[str, any]: 更新結果字典，包含：
                - success: bool - 是否成功
                - has_update: bool - 是否有更新
                - old_commit: str - 更新前的 commit hash
                - new_commit: str - 更新後的 commit hash
                - pull_output: str - pull 操作的輸出
                - pull_error: str - pull 操作的錯誤信息
                - error: str - 錯誤信息（如果失敗）
        """
        try:
            self._logger.info(f"Starting git update in {self._repo_path}")
            
            # Get current commit
            cur_commit = self.get_current_commit()
            if cur_commit is None:
                return {
                    "success": False,
                    "has_update": False,
                    "old_commit": "",
                    "new_commit": "",
                    "pull_output": "",
                    "pull_error": "",
                    "error": "Failed to get current commit"
                }
            
            # Perform pull
            pull_success, pull_output, pull_error = self.pull()
            
            if not pull_success:
                return {
                    "success": False,
                    "has_update": False,
                    "old_commit": cur_commit,
                    "new_commit": cur_commit,
                    "pull_output": pull_output,
                    "pull_error": pull_error,
                    "error": f"Git pull failed: {pull_error}"
                }
            
            # Get new commit
            new_commit = self.get_current_commit()
            if new_commit is None:
                return {
                    "success": False,
                    "has_update": False,
                    "old_commit": cur_commit,
                    "new_commit": cur_commit,
                    "pull_output": pull_output,
                    "pull_error": pull_error,
                    "error": "Failed to get new commit after pull"
                }
            
            has_update = cur_commit != new_commit
            
            if has_update:
                self._logger.info(f"Code updated: {cur_commit} -> {new_commit}")
            else:
                self._logger.info("No update detected")
            
            result = {
                "success": True,
                "has_update": has_update,
                "old_commit": cur_commit,
                "new_commit": new_commit,
                "pull_output": pull_output,
                "pull_error": pull_error,
                "error": ""
            }
            
            # Call callback if set
            if self._update_callback:
                try:
                    self._update_callback(has_update, new_commit)
                except Exception as e:
                    self._logger.error(f"Error in update callback: {e}")
            
            return result
            
        except Exception as e:
            self._logger.error(f"Error during git update: {e}")
            return {
                "success": False,
                "has_update": False,
                "old_commit": "",
                "new_commit": "",
                "pull_output": "",
                "pull_error": "",
                "error": str(e)
            }
    
    def get_repo_path(self) -> str:
        """獲取倉庫路徑"""
        return self._repo_path
    
    def set_repo_path(self, repo_path: str):
        """設置倉庫路徑"""
        self._repo_path = repo_path
        self._logger.info(f"Repository path set to: {repo_path}")
