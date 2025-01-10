from bs4 import BeautifulSoup
import re
import requests
import argparse
from urllib.parse import urlparse
import os


def sanitize_filename(title):
    """Convert a title into a valid filename."""
    print(f"Sanitizing title: {title}")
    filename = title.lower()
    filename = filename.replace(" ", "-")
    filename = re.sub(r"[^a-z0-9-]", "-", filename)
    filename = re.sub(r"-+", "-", filename)
    filename = filename.strip("-")
    final_filename = filename + ".mdx"
    print(f"Generated filename: {final_filename}")
    return final_filename


def fetch_content(source):
    """Fetch content from either a URL or local file."""
    print(f"Fetching content from: {source}")
    parsed = urlparse(source)
    if parsed.scheme and parsed.netloc:
        print("Source is a URL, fetching via HTTP...")
        try:
            response = requests.get(source)
            response.raise_for_status()
            print("Successfully fetched URL content")
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            raise Exception(f"Error fetching URL: {str(e)}")

    print("Source is a file path, reading file...")
    try:
        with open(source, "r", encoding="utf-8") as file:
            content = file.read()
            print("Successfully read file content")
            return content
    except Exception as e:
        print(f"Error reading file: {e}")
        raise Exception(f"Error reading file: {str(e)}")


def get_iframe_tag(element):
    """Extract just the opening iframe tag."""
    iframe_str = str(element)
    end_of_opening_tag = iframe_str.find(">") + 1
    return iframe_str[:end_of_opening_tag]


def process_text_with_formatting(element, is_heading=False):
    """Process text content while preserving formatting."""
    if isinstance(element, str):
        return element.replace("’", "'")

    if element.name == "iframe":
        return get_iframe_tag(element)

    # For headings, skip all formatting
    if is_heading:
        return element.get_text().strip()

    # Special handling for code elements
    if element.name == "code":
        # Check if code is directly wrapped in b or i tags
        parent = element.parent
        if parent and parent.name in ["b", "strong", "i", "em"]:
            return f"`{element.get_text().strip()}`"

    # Build formatted text
    text = ""
    for child in element.children:
        if isinstance(child, str):
            text += child.replace("’", "'")
        elif child.name == "code":
            # Check if code is directly wrapped in b or i tags
            parent = child.parent
            if parent and parent.name in ["b", "strong", "i", "em"]:
                text += f"`{child.get_text().strip()}`"
            else:
                text += f"`{process_text_with_formatting(child)}`"
        elif child.name in ["b", "strong"]:
            text += f"**{process_text_with_formatting(child)}**"
        elif child.name in ["i", "em"]:
            text += f"*{process_text_with_formatting(child)}*"
        elif child.name == "a":
            link_text = process_text_with_formatting(child)
            href = child.get("href", "")
            text += f"[{link_text}]({href})"
        elif child.name == "iframe":
            text += get_iframe_tag(child)
        else:
            text += process_text_with_formatting(child)

    return text.strip()


def process_list_item(li, level=0):
    """Process a single list item and its nested content."""
    indent = "    " * level
    content = []

    # Get the main text content
    p = li.find("p", recursive=False)
    if p:
        text = process_text_with_formatting(p)
    else:
        # Get direct text content
        text = process_text_with_formatting(li)

    content.append(text)

    # Look for nested lists
    nested_lists = li.find_all(["ul", "ol"], recursive=False)
    for nested_list in nested_lists:
        nested_content = process_list(nested_list, level + 1)
        content.extend(nested_content)

    return content


def process_list(list_element, level=0):
    """Process a list element (ul/ol) and return formatted lines."""
    print(f"Processing {'ordered' if list_element.name == 'ol' else 'unordered'} list at level {level}")
    result = []
    indent = "    " * level

    for i, li in enumerate(list_element.find_all("li", recursive=False)):
        marker = f"{i+1}. " if list_element.name == "ol" else "* "
        content_parts = process_list_item(li, level)

        # Add the first part with the list marker
        result.append(f"{indent}{marker}{content_parts[0]}")

        # Add any remaining parts (from nested lists) with proper indentation
        result.extend(content_parts[1:])

    return result


def convert_intercom_to_markdown(html_content):
    """Convert Intercom article HTML to Markdown format."""
    print("Starting HTML to Markdown conversion")

    soup = BeautifulSoup(html_content, "html.parser")
    print("HTML parsed successfully")

    # Extract article title and subtitle
    headers = soup.find_all("header", class_="mb-1 font-primary text-2xl font-bold leading-10 text-body-primary-color")
    if not headers:
        title = "Untitled Article"
        subtitle = None
        print(f"No title found, using default: {title}")
    else:
        title = headers[-1].get_text().strip()
        print(f"Found article title: {title}")

        # Try to find subtitle
        subtitle_div = headers[-1].find_next_sibling("div", class_="text-md font-normal leading-normal text-body-secondary-color")
        if subtitle_div and subtitle_div.find("p"):
            subtitle = subtitle_div.find("p").get_text().strip()
            print(f"Found article subtitle: {subtitle}")
        else:
            subtitle = None
            print("No subtitle found")

    # Find the main article content
    article = soup.find("article")
    if not article:
        print("No article content found!")
        return "No article content found.", title

    print("Found article content, processing blocks...")

    # Initialize markdown content with frontmatter
    markdown_content = ["---", f"title: {title}"]
    if subtitle:
        markdown_content.append(f"description: {subtitle}")
    markdown_content.extend(["---", ""])

    # Track the current block type for better spacing
    previous_block_type = None

    # Process each block in the article
    for block in article.find_all(recursive=False):
        print(f"\nProcessing block: {block.name}")

        # Find lists within the current block
        lists = block.find_all(["ul", "ol"], recursive=False)
        if lists:
            print(f"Found {len(lists)} list(s) in block")
            for list_elem in lists:
                print(f"Processing {list_elem.name} list")
                markdown_list = process_list(list_elem)
                markdown_content.extend(["\n"] + markdown_list + [""])
                print(f"Generated {len(markdown_list)} markdown lines for list")

        elif block.find("h4"):
            heading = block.find("h4")
            heading_text = process_text_with_formatting(heading, is_heading=True)
            print(f"Processing h4: {heading_text}")
            markdown_content.append(f"\n##### {heading_text}\n")

        elif block.find("h3"):
            heading = block.find("h3")
            heading_text = process_text_with_formatting(heading, is_heading=True)
            print(f"Processing h3: {heading_text}")
            markdown_content.append(f"\n#### {heading_text}\n")
        elif block.find("h2"):
            heading = block.find("h2")
            heading_text = process_text_with_formatting(heading, is_heading=True)
            print(f"Processing h2: {heading_text}")
            markdown_content.append(f"\n### {heading_text}\n")

        elif block.find("h1"):
            heading = block.find("h1")
            heading_text = process_text_with_formatting(heading, is_heading=True)
            print(f"Processing h1: {heading_text}")
            markdown_content.append(f"\n## {heading_text}\n")

        elif block.find("h1"):
            heading = block.find("h1")
            heading_text = process_text_with_formatting(heading, is_heading=True)
            print(f"Processing h1: {heading_text}")
            markdown_content.append(f"\n## {heading_text}\n")

        elif block.find("p"):
            p = block.find("p")
            processed_text = process_text_with_formatting(p)
            if processed_text:
                print(f"Processing paragraph: {processed_text[:50]}...")
                markdown_content.append(f"\n{processed_text}\n")

    print("Cleaning up markdown content...")
    final_content = "\n".join(markdown_content)
    final_content = re.sub(r"\n{3,}", "\n\n", final_content)

    print("Conversion completed successfully")
    return final_content, title


def process_single_article(source, output=None):
    """Process a single article and save to markdown."""
    try:
        html_content = fetch_content(source)
        markdown_output, title = convert_intercom_to_markdown(html_content)

        if output:
            output_path = output
            print(f"Using specified output path: {output_path}")
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filename = sanitize_filename(title)
            output_path = os.path.join(script_dir, filename)
            print(f"Using generated output path: {output_path}")

        print("Saving markdown content...")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_output)

        return True, f"Successfully saved to {output_path}"

    except Exception as e:
        return False, str(e)


def process_url_list(list_file):
    """Process multiple URLs from a list file."""
    print(f"\nProcessing URLs from list file: {list_file}")
    try:
        with open(list_file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"Found {len(urls)} URLs to process")

        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n=== Processing URL {i}/{len(urls)}: {url} ===")
            success, message = process_single_article(url)
            results.append((url, success, message))

        print("\n=== Processing Summary ===")
        successful = sum(1 for _, success, _ in results if success)
        print(f"Successfully processed: {successful}/{len(urls)} articles")

        if len(urls) - successful > 0:
            print("\nFailed URLs:")
            for url, success, message in results:
                if not success:
                    print(f"- {url}: {message}")

    except Exception as e:
        print(f"Error processing list file: {str(e)}")
        exit(1)


def main():
    parser = argparse.ArgumentParser(description="Convert Intercom article to Markdown")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", help="URL or file path of the Intercom article")
    group.add_argument("--list", help="File containing list of URLs to process")
    parser.add_argument("-o", "--output", help="Output file path (optional, only used with --source)")
    args = parser.parse_args()

    if args.list:
        process_url_list(args.list)
    else:
        print("\n=== Starting Intercom to Markdown Conversion ===")
        success, message = process_single_article(args.source, args.output)
        if not success:
            print(f"\nError: {message}")
            exit(1)
        else:
            print(f"\nSuccess! {message}")


if __name__ == "__main__":
    main()
