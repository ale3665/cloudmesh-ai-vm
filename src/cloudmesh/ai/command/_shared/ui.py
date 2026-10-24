from rich.console import Console
from rich.table import Table

console = Console()


def render_table(
    title: str,
    columns: list[str],
    rows: list[list],
    alignments: list[str] | None = None,
):
    """
    Renders a rich table for CLI output.

    :param title: Table title.
    :param columns: List of column headers.
    :param rows: List of rows (each row is a list of items).
    :param alignments: Optional list of alignments ("left", "center", "right") for each column.
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    for i, col in enumerate(columns):
        # Default alignment is "left" unless specified otherwise
        align = "left"
        if alignments and i < len(alignments):
            align = alignments[i]

        table.add_column(col, justify=align)

    for row in rows:
        table.add_row(*[str(item) for item in row])

    console.print(table)
