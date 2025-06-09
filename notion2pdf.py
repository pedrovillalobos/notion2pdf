import os
import re
import requests
from notion_client import Client
from weasyprint import HTML
from markdownify import markdownify as md
from pathlib import Path
from dotenv import load_dotenv

# ------------------ CONFIGURATION ------------------
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")
OUTPUT_DIR = "output"
# ---------------------------------------------------

notion = Client(auth=NOTION_TOKEN)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def get_blocks(page_id):
    """Recursively get all blocks (with children) from a page."""
    results = []
    next_cursor = None
    while True:
        response = notion.blocks.children.list(page_id, start_cursor=next_cursor)
        results.extend(response['results'])
        if response.get('has_more'):
            next_cursor = response['next_cursor']
        else:
            break
    return results

def get_child_pages(blocks):
    """Return all child page blocks from a list of blocks."""
    return [block for block in blocks if block['type'] == 'child_page']

def convert_blocks_to_html(blocks, img_folder, notion_token):
    """Converts blocks to HTML, including images."""
    html = ""
    for block in blocks:
        btype = block["type"]
        if btype == "paragraph":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<p>{text}</p>"
        elif btype == "heading_1":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<h1>{text}</h1>"
        elif btype == "heading_2":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<h2>{text}</h2>"
        elif btype == "heading_3":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<h3>{text}</h3>"
        elif btype == "bulleted_list_item":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<ul><li>{text}</li></ul>"
        elif btype == "numbered_list_item":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<ol><li>{text}</li></ol>"
        elif btype == "image":
            img_url = block["image"]["file"]["url"] if block["image"]["type"] == "file" else block["image"]["external"]["url"]
            # Download image
            img_filename = sanitize_filename(os.path.basename(img_url.split("?")[0]))
            img_path = os.path.join(img_folder, img_filename)
            if not os.path.exists(img_path):
                headers = {"Authorization": f"Bearer {notion_token}"}
                img_data = requests.get(img_url, headers=headers)
                with open(img_path, "wb") as f:
                    f.write(img_data.content)
            html += f'<img src="{img_path}" style="max-width:100%"><br>'
        elif btype == "code":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            lang = block[btype].get("language", "")
            html += f"<pre><code class='{lang}'>{text}</code></pre>"
        elif btype == "quote":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<blockquote>{text}</blockquote>"
        elif btype == "callout":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<div style='border-left: 4px solid #888; padding-left: 10px; background: #eee'>{text}</div>"
        elif btype == "toggle":
            text = "".join([t["plain_text"] for t in block[btype]["rich_text"]])
            html += f"<details><summary>{text}</summary></details>"
        elif btype == "child_page":
            pass  # Already handled separately
        # Add more block types as needed
    return html

def export_page_to_pdf(page_id, name_prefix="", parent_chain=None):
    # Get page title
    page = notion.pages.retrieve(page_id)
    title = page['properties']['title']['title'][0]['plain_text']
    safe_title = sanitize_filename(title)
    if parent_chain:
        filename = "-".join(parent_chain + [safe_title]) + ".pdf"
    else:
        filename = f"{safe_title}.pdf"

    output_pdf = os.path.join(OUTPUT_DIR, filename)
    img_folder = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(img_folder, exist_ok=True)

    print(f"Exporting: {filename}")

    blocks = get_blocks(page_id)
    html = convert_blocks_to_html(blocks, img_folder, NOTION_TOKEN)
    # Add a title to the top
    html = f"<h1>{title}</h1>\n" + html

    HTML(string=html, base_url='.').write_pdf(output_pdf)

    # Handle child pages recursively
    child_pages = get_child_pages(blocks)
    for child in child_pages:
        child_id = child["id"]
        export_page_to_pdf(child_id, name_prefix=safe_title, parent_chain=(parent_chain or []) + [safe_title])

if __name__ == "__main__":
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    if not NOTION_TOKEN or not PARENT_PAGE_ID:
        raise Exception("NOTION_TOKEN and PARENT_PAGE_ID must be set in your .env file.")
    export_page_to_pdf(PARENT_PAGE_ID)
    print("All done!")