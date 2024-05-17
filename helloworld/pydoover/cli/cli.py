import argparse
import inspect
import json
import os
import pathlib
import time
import traceback

from datetime import datetime, timedelta
from getpass import getpass
from typing import Optional

from . import parsers
from .. import __version__
from ..cloud import Processor
from ..cloud.api import Client, Forbidden, NotFound
from ..cloud.api.channel import Task

from .config import ConfigEntry, ConfigManager, NotSet
from .decorators import command, annotate_arg


class CLI:
    def __init__(self):
        parser = argparse.ArgumentParser(prog="doover", description="Tools for helping with doover.")
        parser.add_argument("--version", action="version", version=f"doover {__version__.__version__}")
        parser.set_defaults(callback=parser.print_help)

        subparser = parser.add_subparsers(dest="subcommand", title="Subcommands")
        self.setup_commands(subparser)
        self.args = args = parser.parse_args()

        self.config_manager = ConfigManager()
        self.config_manager.current_profile = getattr(args, "profile", "default")
        self.api: Optional[Client] = None

        if hasattr(args, "agent_id"):
            self.agent_id = args.agent_id if args.agent_id != "default" else None
        else:
            self.agent_id = None

        try:
            args.callback(**{
                k: v for k, v in vars(args).items() if k in inspect.signature(args.callback).parameters.keys()
            })
        except Exception as e:
            self.on_error(e)

    def setup_commands(self, subparser):
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if not getattr(func, "_is_command", False):
                continue

            parser = subparser.add_parser(func._command_name, help=func._command_help)
            parser.set_defaults(callback=func)
            argspec = inspect.signature(func)
            arg_docs = func._command_arg_docs

            for param in argspec.parameters.values():
                kwargs = {"help": arg_docs.get(param.name)}
                param_name = param.name

                if param.default is not inspect.Parameter.empty:
                    kwargs["default"] = param.default
                    kwargs["required"] = False
                    param_name = "--" + param_name
                if param.annotation is not inspect.Parameter.empty:
                    kwargs["type"] = param.annotation

                parser.add_argument(param_name, **kwargs)

            if func._command_setup_api:
                parser.add_argument("--profile", help="Config profile to use.", default="default")
                parser.add_argument("--agent-id", help="Agent ID to use for this request.", default="default")

            parser.add_argument("--enable-traceback", help=argparse.SUPPRESS, default=False, action="store_true")

    def setup_api(self, read: bool = True):
        if read:
            self.config_manager.read()

        config = self.config_manager.current
        if not config:
            raise RuntimeError(f"No configuration found for profile {self.config_manager.current_profile}. "
                               f"Please use a different profile or run `doover login`")

        if self.agent_id is None:
            self.agent_id = config.agent_id

        self.api: Client = Client(
            config.username,
            config.password,
            config.token,
            config.token_expires,
            config.base_url,
            login_callback=self.on_api_login,
        )
        if not (config.token and config.token_expires > datetime.utcnow()):
            self.api.login()

    def on_api_login(self):
        config: ConfigEntry = self.config_manager.current

        config.agent_id = self.api.agent_id
        config.token = self.api.access_token.token
        config.token_expires = self.api.access_token.expires_at

        self.config_manager.write()

        if self.agent_id is None:
            self.agent_id = config.agent_id

    def on_error(self, exception):
        if isinstance(exception, NotFound):
            print("We couldn't find what you're looking for! Perhaps try a different Agent ID, or check your spelling?")

        elif isinstance(exception, Forbidden):
            print("Uh-oh - you don't have access to that. Perhaps try a different Agent ID, or ask for permissions?")

        else:
            print(f"Hmm... something went wrong: {exception}\n\nPerhaps you can understand more than me?")

        if not self.args.enable_traceback:
            print("Try running with --enable-traceback flag to see the full error.")
        else:
            traceback.print_exc()

    @command(description="Login to your doover account with a username / password")
    def login(self):
        username = input("Please enter your username: ").strip()
        password = getpass("Please enter your password: ").strip()
        base_url = input("Please enter the base API URL: ").strip("%").strip("/")
        profile_name = input("Please enter this profile name (defaults to default): ").strip()
        profile = profile_name if profile_name != "" else "default"

        self.config_manager.create(ConfigEntry(
            profile,
            username=username,
            password=password,
            base_url=base_url,
        ))
        self.config_manager.current_profile = profile

        try:
            self.setup_api(read=False)
            # self.api.login()
        except Exception:
            print("Login failed. Please try again.")
            if self.args.enable_traceback:
                traceback.print_exc()
            return self.login()

        self.config_manager.write()
        print("Login successful.")

    @command()
    def configure_token(self):
        """Configure your doover credentials with a long-lived token"""
        self.configure_token_impl()

    def configure_token_impl(
            self, token: str = None, agent_id: str = None, base_url: str = None, expiry=NotSet, overwrite: bool = False
    ):
        if not token:
            token = input("Please enter your agent token: ").strip()
            # self.config_manager.current.token = token.strip()
        if not agent_id:
            agent_id = input("Please enter your Agent ID: ").strip()
            # self.config_manager.agent_id = agent_id.strip()
        if not base_url:
            base_url = input("Please enter your base API url: ").strip("%").strip("/")
            # self.config.base_url = base_url
        if expiry is NotSet:
            print("This token is intended to be a long-lived token."
                  "I will remind you to reconfigure the token when this expiry is exceeded.")
            expiry_days = input("Please enter the number of days (approximately) until expiration: ")
            try:
                expiry = datetime.utcnow() + timedelta(days=int(expiry_days))
            except ValueError:
                print("I couldn't parse that expiry. I will set it to None which means no expiry.")
                expiry = None

            # self.config.token_expiry = expiry

        profile_name = input("Please enter this profile's name [default]: ")
        profile = profile_name or "default"

        if profile in self.config_manager.entries and not overwrite:
            p = input("There's already a config entry with this profile. Do you want to overwrite it? [y/N]")
            if not p.startswith("y"):
                print("Exitting...")
                return

        self.config_manager.create(ConfigEntry(
            profile, token=token, token_expires=expiry, base_url=base_url, agent_id=agent_id
        ))
        self.config_manager.current_profile = profile

        self.setup_api(read=False)
        try:
            self.api.get_agent(self.agent_id)
        except Forbidden:
            print("Agent token was incorrect. Please try again.")
            return self.configure_token_impl(agent_id=agent_id, base_url=base_url, expiry=expiry, overwrite=True)
        except NotFound:
            print("Agent ID or Base URL was incorrect. Please try again.")
            return self.configure_token_impl(token=token, expiry=expiry, overwrite=True)
        except Exception:
            print("Base URL was incorrect. Please try again.")
            return self.configure_token_impl(token=token, agent_id=agent_id, expiry=expiry, overwrite=True)
        else:
            self.config_manager.write()
            print("Successfully configured doover credentials.")

    @staticmethod
    def format_channel_info(channel):
        fmt = f"""
        Channel Name: {channel.name}
        Channel Type: {str(channel.__class__.__name__)}
        Channel ID: {channel.id}

        Agent ID: {channel.agent_id}
        """
        # Agent Name: {channel.fetch_agent()}

        if isinstance(channel, Task) and channel.processor_id is not None:
            proc = channel.fetch_processor()
            fmt += f"""
        Processor ID: {channel.processor_id}
        Processor Name: {proc.name}
        """
        fmt += f"""
        Aggregate: {channel.aggregate}
        """
        return fmt

    @command(description="Get channel info", setup_api=True)
    @annotate_arg("channel_name", "Channel name to get info for")
    def get_channel(self, channel_name: str):
        channel = self.api.get_channel_named(channel_name, self.agent_id)
        print(self.format_channel_info(channel))

    @command(setup_api=True)
    @annotate_arg("channel_name", "Channel name to create")
    def create_channel(self, channel_name: str):
        """Create new channel"""
        channel = self.api.create_channel(channel_name, self.agent_id)
        print(f"Channel created successfully. ID: {channel.id}")
        print(self.format_channel_info(channel))

    @command(setup_api=True)
    @annotate_arg("task_name", "Task channel name to create.")
    @annotate_arg("processor_name", "Processor name for this task to trigger.")
    def create_task(self, task_name: parsers.task_name, processor_name: parsers.processor_name):
        """Create new task channel."""
        processor = self.api.get_channel_named(processor_name, self.agent_id)
        task = self.api.create_task(task_name, self.agent_id, processor.id)
        print(f"Task created successfully. ID: {task.id}")
        print(self.format_channel_info(task))

    @command(setup_api=True)
    def create_processor(self, processor_name: parsers.processor_name):
        """Create new processor channel."""
        processor = self.api.create_processor(processor_name, self.agent_id)
        print(f"Processor created successfully. ID: {processor.id}")
        print(self.format_channel_info(processor))

    @command(setup_api=True)
    @annotate_arg("channel_name", "Channel name to publish to")
    def publish(self, channel_name: str, message: parsers.maybe_json):
        """Publish to a doover channel."""
        try:
            channel = self.api.get_channel_named(channel_name, self.agent_id)
        except NotFound:
            print("Channel name was incorrect. Is it owned by this agent?")
            return

        if isinstance(message, dict):
            print("Successfully loaded message as JSON.")

        channel.publish(message)
        print("Successfully published message.")

    @command(setup_api=True)
    @annotate_arg("processor_name", "Processor channel name to publish to")
    @annotate_arg("package_path", "Path to the package to publish")
    def publish_processor(self, processor_name: parsers.processor_name, package_path: pathlib.Path):
        """Publish processor package to a processor channel."""
        if not package_path.exists():
            print("Package path was incorrect.")
            return

        try:
            channel = self.api.get_channel_named(processor_name, self.agent_id)
        except NotFound:
            print("Channel name was incorrect. Is it owned by this agent?")
            return

        if not isinstance(channel, Processor):
            print("Channel name is not a processor. Try a different name?")
            return

        channel.update_from_package(package_path)
        print("Successfully published new package.")

    @command(setup_api=True)
    @annotate_arg("channel_name", "Channel name to publish to")
    @annotate_arg("poll_rate", "Frequency to check for new messages (in seconds)")
    def follow_channel(self, channel_name: str, poll_rate: int = 5):
        """Follow aggregate of a doover channel"""
        channel = self.api.get_channel_named(channel_name, self.agent_id)
        print(self.format_channel_info(channel))

        while True:
            old_aggregate = channel.aggregate
            channel.update()
            if channel.aggregate != old_aggregate:
                print(channel.aggregate)

            time.sleep(poll_rate)

    @command(setup_api=True)
    @annotate_arg("task_name", "Task name to add the subscription to")
    @annotate_arg("channel_name", "Channel name to subscribe to")
    def subscribe_channel(self, task_name: parsers.task_name, channel_name: str):
        """Add a channel to a task's subscriptions."""
        task = self.api.get_channel_named(task_name, self.agent_id)
        if not isinstance(task, Task):
            print("That wasn't a task channel. Try again?")
            return

        channel = self.api.get_channel_named(channel_name, self.agent_id)
        task.subscribe_to_channel(channel.id)
        print(f"Successfully added {channel_name} to {task.name}'s subscriptions.")

    @command(setup_api=True)
    @annotate_arg("task_name", "Task name to remove the subscription from")
    @annotate_arg("channel_name", "Channel name to unsubscribe from")
    def unsubscribe_channel(self, task_name: parsers.task_name, channel_name: str):
        """Remove a channel to a task's subscriptions."""
        task = self.api.get_channel_named(task_name, self.agent_id)
        if not isinstance(task, Task):
            print("That wasn't a task channel. Try again?")
            return

        channel = self.api.get_channel_named(channel_name, self.agent_id)
        task.unsubscribe_from_channel(channel.id)
        print(f"Successfully removed {channel_name} from {task.name}'s subscriptions.")

    @command(setup_api=True)
    @annotate_arg("config_file", "Deployment config file to use. This is usually a doover_config.json file.")
    def deploy_config(self, config_file: pathlib.Path):
        """Deploy a doover config file to the site."""
        if not config_file.exists():
            print("Config file not found.")
            return

        parent_dir = os.path.dirname(config_file)

        with open(config_file, "r") as config_file:
            data = json.loads(config_file.read())

        print("Read config file.")

        proc_deploy_data = data.get("processor_deployments")
        if proc_deploy_data:
            for processor_data in proc_deploy_data.get("processors", []):
                processor = self.api.create_processor(processor_data["name"], self.agent_id)
                processor.update_from_package(os.path.join(parent_dir, processor_data["processor_package_dir"]))
                processor.update()
                print(f"Created or updated processor {processor.name} with processor data length: {len(processor.aggregate)}")

            for task_data in proc_deploy_data.get("tasks", []):
                processor = self.api.get_channel_named(task_data["processor_name"], self.agent_id)
                task = self.api.create_task(task_data["name"], self.agent_id, processor.id)
                task.publish(task_data["task_config"])
                print(f"Created or updated task {task.name}, and deployed new config.")

                for subscription in task_data.get("subscriptions", []):
                    channel = self.api.create_channel(subscription["channel_name"], self.agent_id)
                    if subscription["is_active"] is True:
                        task.subscribe_to_channel(channel.id)
                        print(f"Added {channel.name} as a subscription to task {task.name}.")
                    else:
                        task.unsubscribe_from_channel(channel.id)
                        print(f"Removed {channel.name} as a subscription from task {task.name}.")

        for entry in data.get("deployment_channel_messages", []):
            channel = self.api.create_channel(entry["channel_name"], self.agent_id)
            channel.publish(entry["channel_message"])
            print(f"Published message to {channel.name}")

        print("Successfully deployed config.")


    def main(self):
        pass
