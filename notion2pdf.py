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

def export_page_to_pdf(page_id, parent_chain=None):
    # Get page title
    page = notion.pages.retrieve(page_id)
    title = page['properties']['title']['title'][0]['plain_text']
    safe_title = sanitize_filename(title)

    blocks = get_blocks(page_id)
    # Find all child pages (for recursion)
    child_pages = get_child_pages(blocks)

    # Determine if this page has "real" content (not just empty/child_page blocks)
    non_empty_blocks = [
        b for b in blocks
        if not (b["type"] == "child_page" or (
            b["type"] in ["paragraph", "heading_1", "heading_2", "heading_3"]
            and not b[b["type"]]["rich_text"]
        ))
    ]
    has_content = len(non_empty_blocks) > 0

    # Prepare chain for naming/folder
    if parent_chain:
        chain = parent_chain + [safe_title]
    else:
        chain = [safe_title]

    # List to collect which PDFs will be created (for folder pruning)
    created_pdfs = []

    # Export this page if it has content
    if has_content:
        pdf_filename = "-".join(chain) + ".pdf"
        # Folder path for this page's level
        if len(chain) > 1:
            folder = os.path.join(OUTPUT_DIR, *chain[:-1])
        else:
            folder = os.path.join(OUTPUT_DIR, safe_title)
        os.makedirs(folder, exist_ok=True)

        output_pdf = os.path.join(folder, pdf_filename)
        img_folder = os.path.join(OUTPUT_DIR, "images")
        os.makedirs(img_folder, exist_ok=True)

        print(f"Exporting: {os.path.relpath(output_pdf, OUTPUT_DIR)}")
        html = convert_blocks_to_html(blocks, img_folder, NOTION_TOKEN)
        html = f"<h1>{title}</h1>\n" + html
        HTML(string=html, base_url='.').write_pdf(output_pdf)

        created_pdfs.append(output_pdf)

    # Always process child pages recursively
    for child in child_pages:
        child_id = child["id"]
        # Recursive call: pass the current chain for naming/folders
        child_pdfs = export_page_to_pdf(child_id, chain)
        created_pdfs.extend(child_pdfs)

    # If this is a container page (no PDF exported here, only children), create folder only if children PDFs exist
    if not has_content and created_pdfs:
        # Only create folder if it doesn't exist yet (for child PDFs)
        folder = os.path.join(OUTPUT_DIR, *chain)
        if not os.path.exists(folder):
            os.makedirs(folder)
    # If not a container, no folder is created

    # Return list of PDFs created under this node and its children (for parent folder logic)
    return created_pdfs

if __name__ == "__main__":
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    if not NOTION_TOKEN or not PARENT_PAGE_ID:
        raise Exception("NOTION_TOKEN and PARENT_PAGE_ID must be set in your .env file.")
    export_page_to_pdf(PARENT_PAGE_ID)
    print("All done!")