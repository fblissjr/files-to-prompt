import os
import click
from fnmatch import fnmatch
from . import xml_formatter


def should_ignore(path, gitignore_rules, ignore_patterns, include_patterns):
    basename = os.path.basename(path)

    if include_patterns and not any(
        fnmatch(basename, pattern) for pattern in include_patterns
    ):
        return True

    if any(fnmatch(basename, pattern) for pattern in ignore_patterns):
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
):
    filepaths = []

    if os.path.isfile(path):
        if not should_ignore(path, [], ignore_patterns, include_patterns):
            filepaths.append(path)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                files = [f for f in files if not f.startswith(".")]

            if not ignore_gitignore:
                gitignore_rules.extend(read_gitignore(root))
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore(
                        os.path.join(root, d),
                        gitignore_rules,
                        ignore_patterns,
                        include_patterns,
                    )
                ]
                files = [
                    f
                    for f in files
                    if not should_ignore(
                        os.path.join(root, f),
                        gitignore_rules,
                        ignore_patterns,
                        include_patterns,
                    )
                ]

            filepaths.extend([os.path.join(root, f) for f in files])

    return filepaths


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--include-hidden", is_flag=True, help="Include files and folders starting with ."
)
@click.option(
    "--ignore-gitignore",
    is_flag=True,
    help="Ignore .gitignore files and include all files",
)
@click.option(
    "ignore_patterns",
    "--ignore",
    multiple=True,
    default=[],
    help="List of patterns to ignore",
)
@click.option(
    "include_patterns",
    "--include",
    multiple=True,
    default=[],
    help="List of patterns to include (takes precedence over ignore patterns)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["default", "claude-xml", "claude-xml-b64"]),
    default="default",
    help="Output format",
)
@click.option(
    "--metadata", multiple=True, help="Metadata for documents, in key:value format"
)
@click.version_option()
def cli(
    paths,
    include_hidden,
    ignore_gitignore,
    ignore_patterns,
    include_patterns,
    output_format,
    metadata,
):
    """
    Takes one or more paths to files or directories and outputs every file,
    recursively, in the specified format.
    """
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
            include_patterns,
        )
        all_filepaths.extend(filepaths)

    metadata_dict = dict(item.split(":") for item in metadata) if metadata else None

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
