"""
Copyright (c) Cutleast
"""

import logging
import os
import platform
from email.message import Message
from pathlib import Path
from typing import Optional
from urllib.parse import SplitResult, urlsplit, urlunsplit

import requests as req
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from cutleast_core_lib.core.filesystem.utils import add_suffix

from .multithreading.progress import ProgressUpdate, UpdateCallback, update
from .utilities.scale import scale_value


class Downloader(QObject):
    """
    Class for downloading files from the internet.
    """

    log: logging.Logger = logging.getLogger("Downloader")

    __stop_signal: Signal = Signal()

    __running: bool = False

    __user_agent: str
    __chunk_size: int
    __timeout: int

    def __init__(
        self,
        user_agent: Optional[str] = None,
        chunk_size: int = 1024 * 1024,
        timeout: int = 5,
    ) -> None:
        """
        Args:
            user_agent (Optional[str], optional):
                The user agent to use for the download requests. Defaults to None.
            chunk_size (int, optional):
                The size of each chunk to download in bytes. Defaults to 1 MiB.
            timeout (int, optional):
                The timeout for the download requests in seconds. Defaults to 5 seconds.
        """

        super().__init__()

        self.__stop_signal.connect(self.__stop_download)

        app_name: str = QApplication.applicationName()
        app_version: str = QApplication.applicationVersion()

        if user_agent is None:
            self.__user_agent = (
                f"{app_name}/{app_version} ({platform.system()} {platform.version()}; "
                f"{platform.architecture()[0]})"
            )
        else:
            self.__user_agent = user_agent

        self.__chunk_size = chunk_size
        self.__timeout = timeout

    def download(
        self,
        download_url: str,
        dest_folder: Path,
        file_name: Optional[str] = None,
        progress_callback: Optional[UpdateCallback] = None,
    ) -> Path:
        """
        Downloads a file from the internet and saves it at a specified location.
        The data is written to a temporary file first, which is renamed to the final
        filename after the download is complete.

        Args:
            download_url (str): Direct download URL to file.
            dest_folder (Path): Folder, to which the file gets downloaded to.
            file_name (str, optional):
                Name of downloaded file, only required if the server doesn't return it.
            progress_callback (Optional[UpdateCallback], optional):
                Optional function or method to call with a ProgressUpdate. Defaults to None.

        Returns:
            Path: Path to downloaded file.
        """

        headers: dict[str, str] = {"User-Agent": self.__user_agent}
        url_parts: SplitResult = urlsplit(download_url)
        safe_download_url: str = urlunsplit(
            (url_parts.scheme, url_parts.netloc, url_parts.path, "", "")
        )

        with req.Session() as session:
            stream: req.Response = session.get(
                download_url, stream=True, headers=headers, timeout=self.__timeout
            )

            total_size = int(stream.headers.get("Content-Length", "0"))

            content_disposition: Optional[str] = stream.headers.get(
                "Content-Disposition"
            )
            if content_disposition and file_name is None:
                header = Message()
                header["Content-Disposition"] = content_disposition
                file_name = header.get_filename()

            if file_name is None:
                self.log.debug(f"No filename in response from '{safe_download_url}'.")
                raise ValueError("No filename given!")

            dl_path: Path = dest_folder / file_name
            tmp_path: Path = add_suffix(dl_path, ".part")

            self.log.info(
                f"Downloading '{file_name}' from '{safe_download_url}' to "
                f"'{dest_folder}'..."
            )

            if total_size == 0:
                self.log.warning(
                    "Total file size unknown. No progress information available!"
                )

            if dl_path.is_file():
                if dl_path.stat().st_size == total_size and total_size > 0:
                    self.log.info("File already downloaded.")
                    return dl_path
                else:
                    os.remove(dl_path)
                    self.log.warning(f"Removed already existing file from '{dl_path}'!")

            if tmp_path.is_file():
                if tmp_path.stat().st_size == total_size and total_size > 0:
                    self.log.info("File already downloaded.")
                    tmp_path.rename(dl_path)
                    return dl_path
                else:
                    os.remove(tmp_path)
                    self.log.warning(
                        f"Removed already existing temporary file from '{tmp_path}'!"
                    )

            self.__running = True
            current_size: int = 0
            with tmp_path.open("wb") as output_file:
                for data in stream.iter_content(self.__chunk_size):
                    if self.__running:
                        output_file.write(data)
                        current_size += len(data)
                    else:
                        break

                    update(
                        progress_callback,
                        ProgressUpdate(
                            status_text=(
                                self.tr("Downloading '{0}'...").format(file_name)
                                + f" ({scale_value(current_size)} / "
                                + f"{scale_value(total_size)})"
                            ),
                            value=current_size,
                            maximum=total_size,
                        ),
                    )

        if self.__running and (current_size == total_size or total_size == 0):
            tmp_path.rename(dl_path)
            self.log.info("Download complete!")

        else:
            self.log.warning("Download incomplete!")
            dl_path.unlink(missing_ok=True)
            tmp_path.unlink(missing_ok=True)

        return dl_path

    def __stop_download(self) -> None:
        self.__running = False

    def stop(self) -> None:
        """
        Thread-safe method to send a stop signal to the running download.
        """

        self.__stop_signal.emit()
