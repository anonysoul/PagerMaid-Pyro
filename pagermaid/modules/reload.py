import contextlib
import importlib
import os

import pagermaid.config
import pagermaid.modules
from pagermaid import logs, help_messages, all_permissions, hook_functions, read_context
from pagermaid.enums import Message
from pagermaid.hook import Hook
from pagermaid.listener import listener
from pagermaid.services import bot, scheduler
from pagermaid.utils import lang


async def reload_all():
    read_context.clear()
    bot.dispatcher.remove_all_handlers()
    bot.job.remove_all_jobs()
    with contextlib.suppress(RuntimeError):
        bot.cancel_all_listener()
    loaded_plugins = list(pagermaid.modules.plugin_list)
    loaded_plugins.extend(iter(pagermaid.modules.module_list))
    # init
    importlib.reload(pagermaid.modules)
    importlib.reload(pagermaid.config)
    help_messages.clear()
    all_permissions.clear()
    for functions in hook_functions.values():
        functions.clear()  # noqa: clear all hooks

    for module_name in pagermaid.modules.module_list:
        try:
            module = importlib.import_module(f"pagermaid.modules.{module_name}")
            if module_name in loaded_plugins:
                importlib.reload(module)
        except BaseException as exception:
            logs.info(f"{lang('module')} {module_name} {lang('error')}: {type(exception)}: {exception}")
    for plugin_name in pagermaid.modules.plugin_list.copy():
        try:
            plugin = importlib.import_module(f"plugins.{plugin_name}")
            if plugin_name in loaded_plugins and os.path.exists(plugin.__file__):
                importlib.reload(plugin)
        except BaseException as exception:
            logs.info(f"{lang('module')} {plugin_name} {lang('error')}: {exception}")
            pagermaid.modules.plugin_list.remove(plugin_name)
    await Hook.load_success_exec()


@listener(is_plugin=False, command="reload",
          need_admin=True,
          description=lang('reload_des'))
async def reload_plugins(message: Message):
    """ To reload plugins. """
    await reload_all()
    await message.edit(lang("reload_ok"))


@scheduler.scheduled_job("cron", hour="4", id="reload.clear_read_context")
async def clear_read_context_cron():
    read_context.clear()
