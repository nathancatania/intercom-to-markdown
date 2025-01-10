# Convert Intercom Help Articles to Markdown

This is a quickie script that will take an article from Intercom, [example](https://help.hnry.io/en/articles/2688758-what-taxes-does-hnry-pay), and convert it to a plaintext Markdown document for use in documentation systems like [Mkdocs](https://squidfunk.github.io/mkdocs-material/) or [Mintlify](https://mintlify.com/).

Use it at your own risk. It is not well tested!

---

## Usage

You will need to install Beautiful Soup 4 before running the script:

```
pip install beautifulsoup4
```

Run the script with a single article:
```
python convert-intercom.py --source https://help.example.com/article
```

Run the script specifying the filename of the output:
```
python convert-intercom.py --source https://help.example.com/article -o my_article.md
```

Run the script with a list of articles to convert:
```
python convert-intercom.py --list path/to/txt/file/containing/urls.txt
```

Export to `.mdx` instead of `.md`:
```
python convert-intercom.py --list path/to/txt/file/containing/urls.txt --format .mdx
```

If providing the script a list, it expects a `.txt` file with each Intercom URL to be converted on a separate line. It will fetch the contents of each URL and output the MD or MDX in the same directory as the script. For example:

```
https://help.glean.com/en/articles/4712824-search-from-wherever-you-work
https://help.glean.com/en/articles/3614013-improve-search-quality-by-giving-feedback-on-results
https://help.glean.com/en/articles/3643252-installing-the-browser-extension
```

By default, the markdown file will be saved as: `article-title.md`, but you can pass `--format .mdx` to save it as `.mdx` instead. This is useful for Mintlify.

For single files, you can overwrite the filename itself by passing the `-o` argument and specifying the desired filename.

## Front Matter
The script will parse the title and subtitle of the Intercom page and set these in the Markdown Front Matter as the values of `title` and `description` respectively.

```
---
title: "This is the article title"
description: "This is the article subtitle"
---
```

## Working
- Headings, bold/italics formatting, `inline code`, ordered/unordered lists, [links](https://example.com)


## Not Working
- Does not handle images or embedded content like iframes
- Does not handle code blocks with ```

## Time Permitting
- Pull images into local images folder. Insert into the markdown.
- Automatically traverse Intercom article trees
- Save files to similar hierarchy as Intercom
- Automatically generate Mintlify mint.json navigation structure that can be copy/pasted
