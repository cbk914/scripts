import argparse
import os
import subprocess

# Exceute as:
# python update_git.py -d /path/to/directory

def update_git_repositories(dir):
    # Validate input to prevent command injection attacks
    if not isinstance(dir, str) or ";" in dir or "|" in dir:
        raise ValueError("Invalid directory input")
    
    for subdir, dirs, files in os.walk(dir):
        for subdir in dirs:
            repo_path = os.path.join(subdir, subdir)
            if os.path.exists(os.path.join(repo_path, ".git")):
                print("Updating repository:", repo_path)
                try:
                    output = subprocess.check_output(
                        ["git", "pull"], cwd=repo_path
                    )
                    print(output.decode())
                except subprocess.CalledProcessError as e:
                    print(f"Error updating repository {repo_path}: {e.output.decode()}")

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--directory", required=True, help="Directory to update Git repositories in")
args = parser.parse_args()

update_git_repositories(args.directory)

print('¡All GIT have been updated!')
