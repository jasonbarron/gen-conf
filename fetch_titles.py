#!/usr/bin/env python3
"""
Script to fetch and update conference talk titles from churchofjesuschrist.org
Reads markdown files with "No Title Found" entries and updates them with actual titles.
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path


def fetch_title_from_url(url):
    """
    Fetch the title of a conference talk from the given URL.

    Args:
        url: The URL to fetch the title from

    Returns:
        The title string or None if not found
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try multiple methods to find the title
        # Method 1: Look for h1 with specific class
        title_elem = soup.find('h1', class_='title')
        if title_elem:
            return title_elem.get_text(strip=True)

        # Method 2: Look for any h1 in the main content
        title_elem = soup.find('h1')
        if title_elem:
            return title_elem.get_text(strip=True)

        # Method 3: Look for meta og:title
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content']

        # Method 4: Look for page title and clean it
        if soup.title:
            title = soup.title.get_text(strip=True)
            # Remove common suffixes
            title = re.sub(r'\s*[-–—]\s*The Church of Jesus Christ.*$', '', title)
            return title

        return None

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def update_titles_in_file(file_path, dry_run=False):
    """
    Update all "No Title Found" entries in the markdown file with actual titles.

    Args:
        file_path: Path to the markdown file
        dry_run: If True, only show what would be updated without making changes
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"Error: File {file_path} not found")
        return

    print(f"Reading {file_path}...")
    content = file_path.read_text(encoding='utf-8')

    # Find all "No Title Found" entries with their URLs
    # Pattern: ## No Title Found\n\n**Speaker:**...\n\n**Calling:**...\n\n**Year:**...\n\n**Season:**...\n\n**URL:** (url)
    pattern = r'## No Title Found\n\n\*\*Speaker:\*\* (.+?)\n\n\*\*Calling:\*\* (.+?)\n\n\*\*Year:\*\* (\d+)\n\n\*\*Season:\*\* (.+?)\n\n\*\*URL:\*\* (.+?)(?=\n)'

    matches = list(re.finditer(pattern, content))
    print(f"Found {len(matches)} talks with 'No Title Found'")

    if len(matches) == 0:
        print("No entries to update!")
        return

    updated_content = content
    updates_made = 0

    for i, match in enumerate(matches, 1):
        url = match.group(5)
        speaker = match.group(1)

        print(f"\n[{i}/{len(matches)}] Fetching title for {speaker}...")
        print(f"  URL: {url}")

        title = fetch_title_from_url(url)

        if title:
            print(f"  Title: {title}")

            if not dry_run:
                # Replace "No Title Found" with the actual title
                old_text = match.group(0)
                new_text = old_text.replace("## No Title Found", f"## {title}")
                updated_content = updated_content.replace(old_text, new_text, 1)
                updates_made += 1
        else:
            print(f"  Could not fetch title")

        # Be nice to the server - add a small delay between requests
        if i < len(matches):
            time.sleep(0.5)

    if dry_run:
        print(f"\n=== DRY RUN ===")
        print(f"Would update {len([m for m in matches if fetch_title_from_url(m.group(5))])} titles")
    else:
        if updates_made > 0:
            print(f"\nWriting updates to {file_path}...")
            file_path.write_text(updated_content, encoding='utf-8')
            print(f"Successfully updated {updates_made} titles!")
        else:
            print("\nNo updates were made.")


def main():
    """Main function to run the script."""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch and update conference talk titles')
    parser.add_argument('file', help='Path to the markdown file to update')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without making changes')

    args = parser.parse_args()

    update_titles_in_file(args.file, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
