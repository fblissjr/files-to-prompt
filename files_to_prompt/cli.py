import os
import click
from fnmatch import fnmatch
from datetime import datetime, timedelta  # Added for days logic
from . import xml_formatter


def should_ignore(path, gitignore_rules, ignore_patterns, include_patterns):
    basename = os.path.basename(path)

    # Fix: Ensure patterns are processed correctly
    if include_patterns and not any(
        fnmatch(basename, pattern) for pattern in include_patterns
    ):
        print(
            f"Excluding {basename} because it does not match include patterns {include_patterns}"
        )
        return True

    if any(fnmatch(basename, pattern) for pattern in ignore_patterns):
        print(
            f"Excluding {basename} because it matches ignore patterns {ignore_patterns}"
        )
        return True

    for rule in gitignore_rules:
        if fnmatch(basename, rule):
            return True
        if os.path.isdir(path) and fnmatch(basename + "/", rule):
            return True

    return False


def read_gitignore(path):
    gitignore_path = os.path.join(path, ".gitignore")
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


def process_path(
    path,
    include_hidden,
    ignore_gitignore,
    gitignore_rules,
    ignore_patterns,
    include_patterns,
    days=None,  # New parameter for days logic
):
    filepaths = []
    current_time = datetime.now()  # Track current time for date comparison

    # Walk through all files and directories in the given path
    if os.path.isfile(path):
        file_modified_time = datetime.fromtimestamp(
            os.path.getmtime(path)
        )  # Get modified time
        basename = os.path.basename(path)
        if (
            not days or (current_time - file_modified_time).days <= days
        ) and not should_ignore(path, [], ignore_patterns, include_patterns):
            filepaths.append(path)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            # Optionally exclude hidden directories and files
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                files = [f for f in files if not f.startswith(".")]

            # Apply .gitignore rules if requested
            if not ignore_gitignore:
                gitignore_rules.extend(read_gitignore(root))

            # Filter files according to patterns
            for file in files:
                file_path = os.path.join(root, file)
                file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                # Check file against days filter and pattern inclusion/exclusion
                if not days or (current_time - file_modified_time).days <= days:
                    if not should_ignore(
                        file_path, gitignore_rules, ignore_patterns, include_patterns
                    ):
                        filepaths.append(file_path)

    return filepaths


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--include-hidden", is_flag=True, help="Include hidden files.")
@click.option("--ignore-gitignore", is_flag=True, help="Ignore .gitignore rules.")
@click.option("--ignore-patterns", multiple=True, help="Patterns to ignore.")
@click.option(
    "--include-patterns", multiple=True, help="Patterns to include."
)  # Passed as a tuple by click
@click.option(
    "--output-format",
    type=click.Choice(["plain", "claude-xml", "claude-xml-b64"]),
    default="plain",
    help="Output format.",
)
@click.option("--metadata", multiple=True, help="Metadata to include.")
@click.option(
    "--days",
    type=int,
    default=None,
    help="Filter files modified in the last 'days' days.",
)
def cli(
    paths,
    include_hidden,
    ignore_gitignore,
    ignore_patterns,
    include_patterns,  # Ensure this is passed correctly
    output_format,
    metadata,
    days,
):
    """
    CLI tool to process files and optionally format them in different ways.
    """
    # Ensure include_patterns is a list
    include_patterns = list(include_patterns)

    if not paths:
        paths = [os.getcwd()]  # Use current directory if no paths provided

    gitignore_rules = []
    all_filepaths = []

    for path in paths:
        if not os.path.exists(path):
            raise click.BadArgumentUsage(f"Path does not exist: {path}")
        if not ignore_gitignore:
            gitignore_rules.extend(read_gitignore(os.path.dirname(path)))
        filepaths = process_path(
            path,
            include_hidden,
            ignore_gitignore,
            gitignore_rules,
            ignore_patterns,
            include_patterns,  # Passed correctly here
            days=days,  # Pass days argument
        )
        all_filepaths.extend(filepaths)

    metadata_dict = dict(item.split(":") for item in metadata) if metadata else None

    if not all_filepaths:
        click.echo("No files matched the specified criteria.", err=True)
        return

    if output_format in ["claude-xml", "claude-xml-b64"]:
        xml_root = xml_formatter.create_document_xml(
            all_filepaths,
            base64_encode_binary=(output_format == "claude-xml-b64"),
            metadata=metadata_dict,
        )
        click.echo(xml_formatter.write_document_xml(xml_root))
    else:
        if metadata_dict:
            click.echo("Metadata:")
            for key, value in metadata_dict.items():
                click.echo(f"  {key}: {value}")
            click.echo()

        for file_path in all_filepaths:
            try:
                with open(file_path, "r") as f:
                    file_contents = f.read()
                click.echo(file_path)
                click.echo("---")
                click.echo(file_contents)
                click.echo()
                click.echo("---")
            except UnicodeDecodeError:
                warning_message = (
                    f"Warning: Skipping file {file_path} due to UnicodeDecodeError"
                )
                click.echo(click.style(warning_message, fg="red"), err=True)


if __name__ == "__main__":
    cli()
