import click
from .main import main as main_from_argparse  # 导入修改后的main函数

@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
))
@click.pass_context
def click_main(ctx):
    """调用基于argparse的CLI程序，传递参数列表。"""
    main_from_argparse(ctx.args)
