import argparse
import sys

# 全局字典用于存储所有命令的引用
commands = {}

# Command类，用于存储单个命令的信息
class Command:
    def __init__(self, name, help):
        global commands
        self.parser = None
        self.func = None
        self.name = name
        self.help = help
        self.options = []
        commands[name] = self

    def add_option(self, option):
        self.options.append(option)

    @staticmethod
    def option(*args, **kwargs):
        def decorator(func):
            if not hasattr(func, 'command_args'):
                setattr(func, 'command_args', [])
            func.command_args.append(("option", args, kwargs))
            return func
        return decorator

    @staticmethod
    def argument(*args, **kwargs):
        def decorator(func):
            if not hasattr(func, 'command_args'):
                setattr(func, 'command_args', [])
            func.command_args.append(("argument", args, kwargs))
            return func
        return decorator

    def register(self, subparsers):
        if not self.parser:
            self.parser = subparsers.add_parser(self.name, help=self.help)
            for option_type, args, kwargs in self.options:
                is_flag = kwargs.pop('is_flag', None)
                if is_flag:
                    kwargs['action'] = 'store_true'  # 如果是标志，则设置此动作
                else:
                    nargs = kwargs.pop('multiple', None)
                    if nargs:
                        kwargs['nargs'] = '+'  # 表示至少需要一个参数，或'*'允许零个参数
                required = kwargs.pop('required', None)
                if required is not None:
                    kwargs['required'] = required

                if option_type == "option":
                    self.parser.add_argument(*args, **kwargs)
                elif option_type == "argument":
                    self.parser.add_argument(*args, **kwargs)
            self.parser.set_defaults(func=self.func)

# 命令装饰器工厂，每个命令通过这个工厂创建
def command(name, help=""):
    def decorator(func):
        cmd = Command(name, help)
        cmd.func = func  # 将处理函数直接赋值给 Command 实例

        # 注册命令参数
        for option in getattr(func, 'command_args', []):
            cmd.add_option(option)

        commands[name] = cmd  # 将命令实例添加到全局命令字典中
        return func
    return decorator
