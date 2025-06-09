# Notion2PDF

A simple python script to export Notion pages (and their children) to PDF with hierarchy and images.

## System Requirements

- Python 3.11 (installed via Conda)
- Homebrew (for system libraries)
- Notion integration token (create one [here](https://www.notion.so/profile/integrations))

## How to Use it:

### 1. System Libraries (Intel Mac)

Before setting up the Python environment, install required libraries:

```sh
brew install cairo pango gdk-pixbuf libffi
```

Add this to your ~/.zshrc or ~/.bash_profile:

```sh
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

Tip: On some Intel Macs, Homebrew might use /usr/local/lib instead of /opt/homebrew/lib.
If you get errors, try:

```sh
export DYLD_LIBRARY_PATH="/usr/local/lib:$DYLD_LIBRARY_PATH"
```

Reload your shell:

```sh
source ~/.zshrc
# or
source ~/.bash_profile
```

### 2. Set Up the Conda Environment

Clone the repo and set up Conda:

```sh
git clone <repo-url>
cd notion2pdf
conda env create -f environment.yml
conda activate notion2pdf
```

### 3. Configure Notion Credentials

Rename the .env_example to .env file in the project root:

```sh
NOTION_TOKEN=your_notion_token_here
PARENT_PAGE_ID=your_parent_page_id_here
```

### 4. Run the Script

```sh
python notion2pdf.py
```

The exported PDFs will appear in the output/ directory.

## Troubleshooting

• WeasyPrint or cairo errors: Double-check you installed all Homebrew dependencies and set the correct DYLD_LIBRARY_PATH.
• Apple Silicon Mac: Most likely uses /opt/homebrew/lib. Intel Macs may use /usr/local/lib.

### Python Dependencies

These are installed automatically with Conda/pip:
• notion-client
• weasyprint
• requests
• markdownify
• python-dotenv

### Output

• PDFs are exported to the output/ folder.
• Add output/ and .env to your .gitignore to avoid pushing them to git.
