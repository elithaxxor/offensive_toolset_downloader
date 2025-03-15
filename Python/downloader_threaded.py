import requests
from bs4 import BeautifulSoup
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "https://inventory.raw.pm/tools.html"

def fetch_webpage(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch the webpage: {e}")
        return None


def parse_html_for_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.find_all('a', href=True)


def filter_github_links(links):
    github_links = [link['href'] for link in links if 'github.com' in link['href']]
    return github_links


def process_links(github_links):
    processed_links = []
    for link in github_links:
        # Ensure the link ends with '.git'
        if not link.endswith('.git'):
            link += '.git'
        processed_links.append(link)
    return processed_links


def save_links_to_file(links, filename):
    with open(filename, 'w') as file:
        for link in links:
            file.write(link + '\n')


def _clone_single_repo(link, repo_dir):
    """
    Function run by each thread to clone a single repo.
    Returns a tuple (success: bool, link: str, message: str).
    """
    try:
        subprocess.run(
            ['git', 'clone', link],
            cwd=repo_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return (True, link, "Successfully cloned")
    except subprocess.CalledProcessError as e:
        return (False, link, f"Failed to clone: {e}")
    except FileNotFoundError:
        # Happens if 'git' command is not found
        return (False, link, "Error: 'git' command not found. Please ensure Git is installed.")


def clone_repositories(links, repo_dir, max_workers=5):
    """
    Clone repositories in parallel using ThreadPoolExecutor.
    :param links: List of repo links to clone.
    :param repo_dir: Directory to clone into.
    :param max_workers: Number of threads to use concurrently.
    """
    os.makedirs(repo_dir, exist_ok=True)
    print(f"Starting to clone GitHub repositories into '{repo_dir}/' using up to {max_workers} threads...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_link = {
            executor.submit(_clone_single_repo, link, repo_dir): link
            for link in links
        }

        for future in as_completed(future_to_link):
            success, link, message = future.result()
            if success:
                print(f"[OK] {link} -> {message}")
            else:
                print(f"[FAIL] {link} -> {message}")
            results.append((success, link, message))

    # Additional optional logging or handling can be done with `results`
    print("All clone tasks completed.")


def main():
    html_content = fetch_webpage(url)
    if not html_content:
        return  # Could not fetch webpage; abort

    links = parse_html_for_links(html_content)
    github_links = filter_github_links(links)

    if not github_links:
        print("Warning: No GitHub links found on the page.")
        return

    processed_links = process_links(github_links)
    save_links_to_file(processed_links, 'github_links.txt')

    # Clone repositories in parallel using threads
    clone_repositories(processed_links, 'repos', max_workers=5)

    print("GitHub links have been saved to 'github_links.txt' and cloning attempted.")


if __name__ == "__main__":
    main()
