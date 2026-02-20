import subprocess
import os

def clone_plugin(repo_url: str):
    plugin_name = repo_url.split("/")[-1].replace(".git", "")
    target_path = f"plugins/{plugin_name}"
    
    if os.path.exists(target_path):
        print(f"Plugin '{plugin_name}' already exists. Skipping.")
        return

    print(f"Cloning plugin from {repo_url} into {target_path}...")
    subprocess.run(["git", "clone", repo_url, target_path], check=True)
    print("Cloning finished.")
