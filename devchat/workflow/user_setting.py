from pathlib import Path
import oyaml as yaml
from .schema import UserSettings
from .path import WORKFLOWS_BASE, USER_SETTINGS_FILENAME


def _load_user_settings() -> UserSettings:
    """
    Load the user settings from the settings.yml file.
    """
    settings_path = Path(WORKFLOWS_BASE) / USER_SETTINGS_FILENAME
    if not settings_path.exists():
        return UserSettings()

    with open(settings_path, "r", encoding="utf-8") as file:
        content = yaml.safe_load(file.read())

    if content:
        return UserSettings.parse_obj(content)

    return UserSettings()

USER_SETTINGS = _load_user_settings()
