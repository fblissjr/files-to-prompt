# forked files-to-prompt

Concatenate a directory full of files into a single prompt for use with LLMs, with enhanced support for Claude.

For background on Simon's project see [Building files-to-prompt entirely using Claude 3 Opus](https://simonwillison.net/2024/Apr/8/files-to-prompt/).

## Forked Changes

- Added Claude-specific XML output formats
- Introduced metadata support for documents
- Improved file filtering options

## Installation

Install this tool using `pip`:

```bash
pip install -e .
```

## Usage

To use `files-to-prompt`, provide the path to one or more files or directories you want to process:

```bash
files-to-prompt path/to/file_or_directory [path/to/another/file_or_directory ...]
```

This will output the contents of every file, with each file preceded by its relative path and separated by `---`.

### Options

- `--include-hidden`: Include files and folders starting with `.` (hidden files and directories).
  ```bash
  files-to-prompt path/to/directory --include-hidden
  ```

- `--ignore-gitignore`: Ignore `.gitignore` files and include all files.
  ```bash
  files-to-prompt path/to/directory --ignore-gitignore
  ```

- `--ignore <pattern>`: Specify one or more patterns to ignore. Can be used multiple times.
  ```bash
  files-to-prompt path/to/directory --ignore "*.log" --ignore "temp*"
  ```

- `--include <pattern>`: Specify one or more patterns to include. Can be used multiple times.
  ```bash
  files-to-prompt path/to/directory --include "*.py" --include "*.md"
  ```

- `--format <format>`: Specify the output format. Options are "default", "claude-xml", or "claude-xml-b64".
  ```bash
  files-to-prompt path/to/directory --format claude-xml
  ```

- `--metadata <key:value>`: Add metadata to the documents. Can be used multiple times.
  ```bash
  files-to-prompt path/to/directory --metadata "project:MyProject" --metadata "version:1.0"
  ```

### Claude-specific Options

- `--format claude-xml`: Outputs the files in an XML format suitable for Claude.
- `--format claude-xml-b64`: Similar to `claude-xml`, but encodes binary files in base64.

### Example

Suppose you have a directory structure like this:

```
my_directory/
├── file1.txt
├── file2.txt
├── .hidden_file.txt
├── temp.log
└── subdirectory/
    └── file3.txt
```

Running `files-to-prompt my_directory` will output:

```
my_directory/file1.txt
---
Contents of file1.txt
---
my_directory/file2.txt
---
Contents of file2.txt
---
my_directory/subdirectory/file3.txt
---
Contents of file3.txt
---
```

If you run `files-to-prompt my_directory --include-hidden`, the output will also include `.hidden_file.txt`.

If you run `files-to-prompt my_directory --ignore "*.log"`, the output will exclude `temp.log`.

### Claude XML Output Example

Running `files-to-prompt my_directory --format claude-xml` will output:

```xml
<documents>
  <document index="0">
    <source>my_directory/file1.txt</source>
    <document_content>
Contents of file1.txt
    </document_content>
  </document>
  <document index="1">
    <source>my_directory/file2.txt</source>
    <document_content>
Contents of file2.txt
    </document_content>
  </document>
  <document index="2">
    <source>my_directory/subdirectory/file3.txt</source>
    <document_content>
Contents of file3.txt
    </document_content>
  </document>
</documents>
```

This format is designed to be easily parsed by Claude for multi-document tasks.
