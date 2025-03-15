#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

def main():
    # Initialize colorama (for colorful console output)
    init(autoreset=True)

    # Set up logging to file and console
    logging.basicConfig(
        filename='scrape_clone.log',
        filemode='a',  # Append to existing log file
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create a second handler to also log INFO+ messages to the console in plain text
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    url = "https://inventory.raw.pm/tools.html"
    output_file = "github_repos.txt"

    # -------------------------------------------------------------------------
    # STEP 1: Fetch the webpage
    # -------------------------------------------------------------------------
    logging.info("Fetching webpage: %s", url)
    print(f"{Fore.YELLOW}[!] Fetching webpage...{Style.RESET_ALL}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info("Successfully fetched webpage.")
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching URL '%s': %s", url, e)
        print(f"{Fore.RED}[!] Error fetching URL: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # STEP 2: Parse the HTML to collect category -> list of GitHub URLs
    # -------------------------------------------------------------------------
    soup = BeautifulSoup(response.text, "html.parser")
    categories = soup.find_all("h3")

    category_links = {}

    for cat in categories:
        try:
            category_name = cat.get_text(strip=True)
            links_container = cat.find_next_sibling()
            if not links_container:
                # If there's no container for links, skip this category
                logging.warning("No link container for category '%s'", category_name)
                continue

            # Gather GitHub links
            links = links_container.find_all("a", href=True)
            github_links = []
            for link in links:
                try:
                    href = link['href']
                    if "github.com" in href:
                        github_links.append(href)
                except Exception as link_err:
                    # If one link fails, log and skip this link
                    logging.error("Error parsing link in category '%s': %s", category_name, link_err)
                    continue

            if github_links:
                category_links[category_name] = github_links

        except Exception as cat_err:
            # Log error and move to next category
            logging.error("Error processing category '%s': %s", cat, cat_err)
            print(f"{Fore.RED}[!] Error processing category {cat}: {cat_err}{Style.RESET_ALL}")
            continue

    # -------------------------------------------------------------------------
    # STEP 3: Write all GitHub links to a text file
    # -------------------------------------------------------------------------
    logging.info("Writing all found GitHub repos to '%s'.", output_file)
    print(f"{Fore.YELLOW}[!] Writing all GitHub repos to {output_file}...{Style.RESET_ALL}")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for cat, links in category_links.items():
                for repo in links:
                    f.write(repo + "\n")
        logging.info("Successfully wrote GitHub repos to '%s'.", output_file)
        print(f"{Fore.GREEN}[+] Successfully wrote all repos to {output_file}{Style.RESET_ALL}")
    except Exception as e:
        logging.error("Error writing to file '%s': %s", output_file, e)
        print(f"{Fore.RED}[!] Error writing to file: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # STEP 4: Clone repositories into category-based directories
    # -------------------------------------------------------------------------
    for cat, links in category_links.items():
        # Make a filesystem-safe category directory name
        safe_category_dir = "".join([c if c.isalnum() or c in " ._-" else "_" for c in cat])

        logging.info("Processing category '%s' -> directory '%s'.", cat, safe_category_dir)
        print(f"{Fore.BLUE}[!] Processing category: {cat}{Style.RESET_ALL}")

        # Create category directory if it does not exist
        try:
            if not os.path.exists(safe_category_dir):
                os.makedirs(safe_category_dir)
                logging.info("Directory created: '%s'.", safe_category_dir)
        except Exception as e:
            logging.error("Failed to create directory '%s': %s", safe_category_dir, e)
            print(f"{Fore.RED}[!] Failed to create directory {safe_category_dir}: {e}{Style.RESET_ALL}")
            # Continue to the next category rather than exiting
            continue

        # Move into category directory
        original_dir = os.getcwd()
        os.chdir(safe_category_dir)

        # Clone each repository
        for repo_url in links:
            repo_name = repo_url.strip().split("/")[-1]

            # If the folder already exists, skip
            if os.path.exists(repo_name):
                logging.info("Skipping (already cloned): %s", repo_url)
                print(f"{Fore.CYAN}[-] Skipping (already cloned): {repo_url}{Style.RESET_ALL}")
                continue

            logging.info("Cloning repository: %s", repo_url)
            print(f"{Fore.YELLOW}[!] Cloning: {repo_url}{Style.RESET_ALL}")

            try:
                result = subprocess.run(
                    ["git", "clone", repo_url],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    logging.info("Successfully cloned: %s", repo_url)
                    print(f"{Fore.GREEN}[+] Successfully cloned: {repo_url}{Style.RESET_ALL}")
                else:
                    logging.error("Failed to clone '%s': %s", repo_url, result.stderr.strip())
                    print(f"{Fore.RED}[!] Failed to clone {repo_url}{Style.RESET_ALL}")
                    print(f"{Fore.RED}    Error: {result.stderr.strip()}{Style.RESET_ALL}")

            except Exception as e:
                logging.error("Exception while cloning '%s': %s", repo_url, e)
                print(f"{Fore.RED}[!] Exception while cloning {repo_url}: {e}{Style.RESET_ALL}")

        # Return to original directory
        os.chdir(original_dir)

    logging.info("All repositories processed.")
    print(f"{Fore.MAGENTA}[!] Done. All repositories processed.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
