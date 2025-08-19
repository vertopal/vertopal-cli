"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

from pathlib import Path
from configparser import ConfigParser


class Config:
    """Provides read and write methods for accessing global user config file.

    The configuration file is INI-structured located in user's home directory.
    More info about INI file and its structure:
    https://en.wikipedia.org/wiki/INI_file#Example

    Attributes:
        PATH (Path): Path to the configuration file.
        _config (ConfigParser): Holds an instance `ConfigParser` class.

    Usage:
    
        >>> from vertopal.utils.config import Config
        >>> Config.write("api", "appid", "my-app-id")
        >>> Config.read("api", "appid")
        'my-app-id'
    """

    PATH: Path = Path().home() / ".vertopal"
    _config: ConfigParser = ConfigParser()

    @classmethod
    def read(cls, section: str, key: str) -> str:
        """Read from config file.

        Args:
            section (str): Specify the config section.
            key (str): Specify the key of the option.

        Raises:
            Exception: If there is an error in reading config option.

        Returns:
            str: The value of the config option.
        """

        cls._create_if_not_exists()
        cls._load()
        try:
            return cls._config[section][key]
        except KeyError:
            cls.write(section, key, "")
            return ""
        except Exception as exc:
            raise LookupError("reading config failed") from exc

    @classmethod
    def write(cls, section: str, key: str, value: str) -> None:
        """Write to config file.

        Args:
            section (str): Specify the config section.
            key (str): Specify the key of the option.
            value (str): Specify the value of the option.
        """

        cls._load()
        if section not in cls._config.sections():
            cls._config[section] = {}
        cls._config[section][key] = value
        with open(cls.PATH, "w", encoding="utf-8") as configfile:
            cls._config.write(configfile)

    @classmethod
    def _load(cls) -> None:
        """Read and parse configuration file to `Config._config`.

        Returns:
            None
        """

        cls._config.read(cls.PATH)

    @classmethod
    def _create_if_not_exists(cls) -> None:
        """Create configuration file if not exists.

        Returns:
            None
        """

        if not cls.PATH.exists():
            cls.PATH.touch()
