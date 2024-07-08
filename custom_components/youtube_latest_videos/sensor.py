import aiohttp
from datetime import timedelta
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN

SCAN_INTERVAL = timedelta(minutes=10)
LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    username = entry.data["username"]
    coordinator = YouTubeDataUpdateCoordinator(hass, username)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([YouTubeLatestVideosSensor(coordinator)], True)

class YouTubeDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, username: str):
        self.username = username
        super().__init__(
            hass,
            LOGGER,
            name="YouTube Latest Videos",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        url = f"https://henrikhjelm.se/api/youtube.php?user={self.username}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

class YouTubeLatestVideosSensor(SensorEntity):
    def __init__(self, coordinator: YouTubeDataUpdateCoordinator):
        self.coordinator = coordinator
        self._attr_name = f"YouTube Latest Videos ({coordinator.username})"
        self._attr_unique_id = f"youtube_latest_videos_{coordinator.username}"
        self._state = None

    @property
    def state(self):
        if self.coordinator.data and "videos" in self.coordinator.data:
            self._state = len(self.coordinator.data["videos"])
        return self._state

    @property
    def extra_state_attributes(self):
        if self.coordinator.data and "videos" in self.coordinator.data:
            first_video = self.coordinator.data["videos"][0] if self.coordinator.data["videos"] else None
            if first_video:
                return {
                    "img": first_video["img"],
                    "video": first_video["video"],
                    "url": f"https://www.youtube.com/watch?v={first_video['video']}",
                    "username": self.coordinator.data.get("username"),
                }
        return {}

    async def async_update(self):
        await self.coordinator.async_request_refresh()
