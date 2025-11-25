import os
import shutil
import subprocess
import tempfile
import logging

log = logging.getLogger(__name__)

class RepoLoader:
    def __init__(self, cache_dir="repo_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def fetch_repo(self, repo_url):
        """Clones a repository to a temporary directory and returns the path."""
        # Validate URL format
        if not repo_url or not repo_url.startswith(("http://", "https://")):
            return None, "Invalid URL format. Please provide a full repository URL (e.g., https://github.com/username/repo)"
        
        # Remove .git suffix for URL validation but keep original for git clone
        clean_url = repo_url.rstrip("/").replace(".git", "")
        url_parts = clean_url.split("/")
        
        # Check if URL has at least username/repo structure
        if len(url_parts) < 5:  # https://github.com/username/repo
            return None, "Incomplete URL. Format should be: https://github.com/username/repository-name"
        
        repo_name = url_parts[-1]
        target_dir = os.path.join(self.cache_dir, repo_name)
        
        # Clean existing
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
            
        # Method 1: Try Git Clone
        git_error = None
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, target_dir], 
                check=True, 
                capture_output=True,
                text=True
            )
            log.info(f"Successfully cloned {repo_url}")
            return target_dir, None
        except FileNotFoundError:
            git_error = "Git is not installed in the container"
            log.warning(f"{git_error}. Falling back to ZIP download.")
        except subprocess.CalledProcessError as e:
            git_error = f"Git clone failed: {e.stderr}"
            log.warning(f"{git_error}. Falling back to ZIP download.")
            
        # Method 2: ZIP Download (Fallback)
        try:
            import requests
            import zipfile
            import io
            
            # Use clean URL (without .git) for ZIP download
            base_url = clean_url
            
            # Try multiple common branch names
            branches = ["main", "master", "dev", "develop", "trunk"]
            last_error = None
            
            for branch in branches:
                zip_url = f"{base_url}/archive/refs/heads/{branch}.zip"
                try:
                    log.info(f"Attempting to download from {zip_url}")
                    r = requests.get(zip_url, timeout=15)
                    if r.status_code == 200:
                        z = zipfile.ZipFile(io.BytesIO(r.content))
                        z.extractall(self.cache_dir)
                        # The zip usually extracts to 'repo-branch', so we need to find it and rename/move
                        extracted_name = z.namelist()[0].split('/')[0]
                        extracted_path = os.path.join(self.cache_dir, extracted_name)
                        
                        if os.path.exists(target_dir):
                             shutil.rmtree(target_dir)
                        shutil.move(extracted_path, target_dir)
                        log.info(f"Successfully downloaded repo from {branch} branch")
                        return target_dir, None
                    elif r.status_code == 404:
                        last_error = f"Branch '{branch}' not found"
                        log.debug(f"{last_error} at {zip_url}")
                    else:
                        last_error = f"HTTP {r.status_code} for branch '{branch}'"
                        log.debug(f"{last_error}")
                except requests.exceptions.RequestException as e:
                    last_error = f"Network error: {str(e)}"
                    log.debug(f"Request failed for {zip_url}: {e}")
                except Exception as e:
                    last_error = f"Error processing {branch}: {str(e)}"
                    log.debug(f"Failed to download from {zip_url}: {e}")
                    continue
            
            # All attempts failed
            error_msg = f"Failed to download repository.\n\n"
            if git_error:
                error_msg += f"Git error: {git_error}\n\n"
            error_msg += f"ZIP download error: {last_error}\n\nPlease check:\n"
            error_msg += "1. Repository URL is correct and complete\n"
            error_msg += "2. Repository is public (private repos require authentication)\n"
            error_msg += "3. Network connectivity from Docker container"
            
            return None, error_msg
            
        except ImportError:
            return None, f"Git error: {git_error}\n\n'requests' library is missing. Please rebuild Docker image with updated requirements.txt"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

    def get_file_tree(self, repo_path):
        """Returns a list of all files in the repo."""
        file_list = []
        for root, dirs, files in os.walk(repo_path):
            # Skip .git
            if ".git" in dirs:
                dirs.remove(".git")
                
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                file_list.append(rel_path)
        return sorted(file_list)

    def read_file(self, repo_path, rel_path):
        """Reads the content of a specific file."""
        full_path = os.path.join(repo_path, rel_path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
