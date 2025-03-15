import requests
from bs4 import BeautifulSoup
import subprocess
import os

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
        if not link.endswith('.git'):
            link += '.git'
        processed_links.append(link)
    return processed_links


def save_links_to_file(links, filename):
    with open(filename, 'w') as file:
        for link in links:
            file.write(link + '\n')


def clone_repositories(links, repo_dir):
    os.makedirs(repo_dir, exist_ok=True)
    print("Starting to clone GitHub repositories into 'repos/'...")
    for link in links:
        try:
            subprocess.run(['git', 'clone', link], cwd=repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Successfully cloned {link}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {link}: {e}")
        except FileNotFoundError:
            print("Error: 'git' command not found. Please ensure Git is installed.")
            break


def main():
    html_content = fetch_webpage(url)
    if not html_content:
        return

    links = parse_html_for_links(html_content)
    github_links = filter_github_links(links)

    if not github_links:
        print("Warning: No GitHub links found on the page.")
        return

    processed_links = process_links(github_links)
    save_links_to_file(processed_links, 'github_links.txt')
    clone_repositories(processed_links, 'repos')

    print("GitHub links have been saved to github_links.txt and cloning attempted.")


if __name__ == "__main__":
    main()
