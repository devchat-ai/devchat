import click


@click.command(help="Run a workflow.", name="run")
def run_workflow(workflow_name: str, user_input: str):
    # TODO: Replace `devchat route` with this command(`devchat workflow run`) later
    pass
