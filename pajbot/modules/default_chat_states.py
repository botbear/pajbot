from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import logging
import math

from pajbot.managers.handler import HandlerManager
from pajbot.modules import BaseModule, ModuleSetting

import pytimeparse

if TYPE_CHECKING:
    from pajbot.bot import Bot

from requests import HTTPError

log = logging.getLogger(__name__)


def parse_follower_duration(duration_str: str) -> Optional[int]:
    """Parse an input string (e.g. 2w) and output it as a number of minutes,
    or None if the string was unable to be parsed.
    We ensure the duration returned is no less than 0 and no more than 3 months."""
    if duration_str == "":
        return None

    duration_s: Optional[int | float] = pytimeparse.parse(duration_str)

    if duration_s is None:
        log.error(f"Failed to parse time from {duration_str}")
        return None

    duration_m = max(math.floor(duration_s / 60), 0)

    return min(duration_m, 129600)


class DefaultChatStatesModule(BaseModule):
    ID = __name__.rsplit(".", maxsplit=1)[-1]
    NAME = "Default Chat States"
    DESCRIPTION = "Enforces certain chat states when the streamer goes online/offline"
    CATEGORY = "Moderation"
    ENABLED_DEFAULT = False
    ONLINE_PHRASE = "Goes Online"
    OFFLINE_PHRASE = "Goes Offline"
    NEVER_PHRASE = "Never"
    PHRASE_OPTIONS = [ONLINE_PHRASE, OFFLINE_PHRASE, NEVER_PHRASE]
    SETTINGS = [
        ModuleSetting(
            key="emoteonly",
            label="Enable emote only mode when the stream...",
            type="options",
            required=True,
            default=NEVER_PHRASE,
            options=PHRASE_OPTIONS,
        ),
        ModuleSetting(
            key="subonly",
            label="Enable subscriber only mode when the stream...",
            type="options",
            required=True,
            default=NEVER_PHRASE,
            options=PHRASE_OPTIONS,
        ),
        ModuleSetting(
            key="r9k",
            label="Enable R9K mode when the stream...",
            type="options",
            required=True,
            default=NEVER_PHRASE,
            options=PHRASE_OPTIONS,
        ),
        ModuleSetting(
            key="slow_option",
            label="Enable slow mode when the stream...",
            type="options",
            required=True,
            default=NEVER_PHRASE,
            options=PHRASE_OPTIONS,
        ),
        ModuleSetting(
            key="slow_time",
            label="Amount of seconds to use when setting slow mode",
            type="number",
            required=True,
            placeholder="30",
            default=30,
            constraints={"min_value": 1, "max_value": 1800},
        ),
        ModuleSetting(
            key="followersonly_option",
            label="Enable followers only mode when the stream...",
            type="options",
            required=True,
            default=NEVER_PHRASE,
            options=PHRASE_OPTIONS,
        ),
        ModuleSetting(
            key="followersonly_time",
            label="Amount of time to use when setting followers only mode | Format is number followed by time format. E.g. 30m, 1 week, 5 days 12 hours. Valid time selectors are seconds, minutes, hours, days, and weeks.",
            type="text",
            required=False,
            placeholder="",
            default="",
            constraints={},
        ),
    ]

    def __init__(self, bot: Optional[Bot]) -> None:
        super().__init__(bot)

    def on_stream_start(self, **rest) -> bool:
        if self.bot is None:
            log.warning("on_stream_start failed in DefaultChatStatesModule because bot is None")
            return True

        if self.settings["emoteonly"] == self.ONLINE_PHRASE:
            try:
                self.bot.twitch_helix_api.update_emote_only_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    True,
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update emote only mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update emote only mode.")
                else:
                    log.error(f"Failed to update emote only mode: {e} - {e.response.text}")

        if self.settings["subonly"] == self.ONLINE_PHRASE:
            try:
                self.bot.twitch_helix_api.update_sub_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    True,
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update subscriber only mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update subscriber only mode.")
                else:
                    log.error(f"Failed to update subscriber only mode: {e} - {e.response.text}")

        if self.settings["r9k"] == self.ONLINE_PHRASE:
            try:
                self.bot.twitch_helix_api.update_unique_chat_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    True,
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update unique chat mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update unique chat mode.")
                else:
                    log.error(f"Failed to update unique chat mode: {e} - {e.response.text}")

        if self.settings["slow_option"] == self.ONLINE_PHRASE:
            try:
                self.bot.twitch_helix_api.update_slow_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    True,
                    self.settings["slow_time"],
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update slow mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update slow mode.")
                else:
                    log.error(f"Failed to update slow_mode: {e} - {e.response.text}")

        if self.settings["followersonly_option"] == self.ONLINE_PHRASE:
            duration_m = parse_follower_duration(self.settings["followersonly_time"])

            try:
                self.bot.twitch_helix_api.update_follower_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    state=True,
                    duration_m=duration_m,
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update follower mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update follower mode.")
                else:
                    log.error(f"Failed to update follower_mode: {e} - {e.response.text}")

        return True

    def on_stream_stop(self, **rest) -> bool:
        if self.bot is None:
            log.warning("on_stream_stop failed in DefaultChatStatesModule because bot is None")
            return True

        if self.settings["emoteonly"] == self.OFFLINE_PHRASE:
            try:
                self.bot.twitch_helix_api.update_emote_only_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    True,
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update emote only mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update emote only mode.")
                else:
                    log.error(f"Failed to update emote only mode: {e} - {e.response.text}")

        if self.settings["subonly"] == self.OFFLINE_PHRASE:
            try:
                self.bot.twitch_helix_api.update_sub_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    True,
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update subscriber only mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update subscriber only mode.")
                else:
                    log.error(f"Failed to update subscriber only mode: {e} - {e.response.text}")

        if self.settings["r9k"] == self.OFFLINE_PHRASE:
            try:
                self.bot.twitch_helix_api.update_unique_chat_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    True,
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update unique chat mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update unique chat mode.")
                else:
                    log.error(f"Failed to update unique chat mode: {e} - {e.response.text}")

        if self.settings["slow_option"] == self.OFFLINE_PHRASE:
            try:
                self.bot.twitch_helix_api.update_slow_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    True,
                    self.settings["slow_time"],
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update slow mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update slow mode.")
                else:
                    log.error(f"Failed to update slow_mode: {e} - {e.response.text}")

        if self.settings["followersonly_option"] == self.OFFLINE_PHRASE:
            duration_m = parse_follower_duration(self.settings["followersonly_time"])

            try:
                self.bot.twitch_helix_api.update_follower_mode(
                    self.bot.streamer.id,
                    self.bot.bot_user.id,
                    self.bot.bot_token_manager,
                    state=True,
                    duration_m=duration_m,
                )
            except HTTPError as e:
                if e.response.status_code == 401:
                    log.error(f"Failed to update follower mode, unauthorized: {e} - {e.response.text}")
                    self.bot.send_message("Error: The bot must be re-authed in order to update follower mode.")
                else:
                    log.error(f"Failed to update follower_mode: {e} - {e.response.text}")

        return True

    def enable(self, bot: Optional[Bot]) -> None:
        HandlerManager.add_handler("on_stream_start", self.on_stream_start)
        HandlerManager.add_handler("on_stream_stop", self.on_stream_stop)

    def disable(self, bot: Optional[Bot]) -> None:
        HandlerManager.remove_handler("on_stream_start", self.on_stream_start)
        HandlerManager.remove_handler("on_stream_stop", self.on_stream_stop)
