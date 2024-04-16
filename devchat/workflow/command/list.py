import rich_click as click


@click.command(help="List all local workflows.", name="list")
def list_workflows():
    click.echo("will list all local workflows.")
    # TODO:
