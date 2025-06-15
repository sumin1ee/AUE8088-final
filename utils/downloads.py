# YOLOv5 🚀 by Ultralytics, AGPL-3.0 license
"""Download utils."""

import logging
import subprocess
import urllib
from pathlib import Path

import requests
import torch


def is_url(url, check=True):
    """Determines if a string is a URL and optionally checks its existence online, returning a boolean."""
    try:
        url = str(url)
        result = urllib.parse.urlparse(url)
        assert all([result.scheme, result.netloc])  # check if is url
        return (urllib.request.urlopen(url).getcode() == 200) if check else True  # check if exists online
    except (AssertionError, urllib.request.HTTPError):
        return False


def gsutil_getsize(url=""):
    """
    Returns the size in bytes of a file at a Google Cloud Storage URL using `gsutil du`.

    Returns 0 if the command fails or output is empty.
    """
    output = subprocess.check_output(["gsutil", "du", url], shell=True, encoding="utf-8")
    return int(output.split()[0]) if output else 0


def url_getsize(url="https://ultralytics.com/images/bus.jpg"):
    """Returns the size in bytes of a downloadable file at a given URL; defaults to -1 if not found."""
    response = requests.head(url, allow_redirects=True)
    return int(response.headers.get("content-length", -1))


def curl_download(url, filename, *, silent: bool = False) -> bool:
    """Download a file from a url to a filename using curl."""
    silent_option = "sS" if silent else ""  # silent
    proc = subprocess.run(
        [
            "curl",
            "-#",
            f"-{silent_option}L",
            url,
            "--output",
            filename,
            "--retry",
            "9",
            "-C",
            "-",
        ]
    )
    return proc.returncode == 0


def safe_download(file, url, url2=None, min_bytes=1e0, error_msg=""):
    """
    Downloads a file from a URL (or alternate URL) to a specified path if file is above a minimum size.

    Removes incomplete downloads.
    """
    from utils.general import LOGGER

    file = Path(file)
    assert_msg = f"Downloaded file '{file}' does not exist or size is < min_bytes={min_bytes}"
    try:  # url1
        LOGGER.info(f"Downloading {url} to {file}...")
        torch.hub.download_url_to_file(url, str(file), progress=LOGGER.level <= logging.INFO)
        assert file.exists() and file.stat().st_size > min_bytes, assert_msg  # check
    except Exception as e:  # url2
        if file.exists():
            file.unlink()  # remove partial downloads
        LOGGER.info(f"ERROR: {e}\nRe-attempting {url2 or url} to {file}...")
        # curl download, retry and resume on fail
        curl_download(url2 or url, file)
    finally:
        if not file.exists() or file.stat().st_size < min_bytes:  # check
            if file.exists():
                file.unlink()  # remove partial downloads
            LOGGER.info(f"ERROR: {assert_msg}\n{error_msg}")
        LOGGER.info("")


def attempt_download(file, repo="ultralytics/yolov5", release="v7.0"):
    """Downloads a file from GitHub release assets or via direct URL if not found locally, supporting backup
    versions.
    """
    from utils.general import LOGGER

    def github_assets(repository, version="latest"):
        # Return GitHub repo tag (i.e. 'v7.0') and assets (i.e. ['yolov5s.pt', 'yolov5m.pt', ...])
        if version != "latest":
            version = f"tags/{version}"  # i.e. tags/v7.0
        response = requests.get(f"https://api.github.com/repos/{repository}/releases/{version}").json()  # github api
        return response["tag_name"], [x["name"] for x in response["assets"]]  # tag, assets

    file = Path(str(file).strip().replace("'", ""))
    if not file.exists():
        # URL specified
        name = Path(urllib.parse.unquote(str(file))).name  # decode '%2F' to '/' etc.
        if str(file).startswith(("http:/", "https:/")):  # download
            url = str(file).replace(":/", "://")  # Pathlib turns :// -> :/
            file = name.split("?")[0]  # parse authentication https://url.com/file.txt?auth...
            if Path(file).is_file():
                LOGGER.info(f"Found {url} locally at {file}")  # file already exists
            else:
                safe_download(file=file, url=url, min_bytes=1e5)
            return file

        # GitHub assets
        assets = [f"yolov5{size}{suffix}.pt" for size in "nsmlx" for suffix in ("", "6", "-cls", "-seg")]  # default
        try:
            tag, assets = github_assets(repo, release)
        except Exception:
            try:
                tag, assets = github_assets(repo)  # latest release
            except Exception:
                try:
                    tag = subprocess.check_output("git tag", shell=True, stderr=subprocess.STDOUT).decode().split()[-1]
                except Exception:
                    tag = release

        if name in assets:
            file.parent.mkdir(parents=True, exist_ok=True)  # make parent dir (if required)
            safe_download(
                file,
                url=f"https://github.com/{repo}/releases/download/{tag}/{name}",
                min_bytes=1e5,
                error_msg=f"{file} missing, try downloading from https://github.com/{repo}/releases/{tag}",
            )

    return str(file)


def attempt_download_v8(file, repo="ultralytics/assets", release="latest"):
    def github_assets(repository: str, tag: str = "latest"):
        """지정 repo 의 release (tag) 에 포함된 asset 목록 리턴"""
        if tag != "latest":
            tag = f"tags/{tag}"
        r = requests.get(f"https://api.github.com/repos/{repository}/releases/{tag}").json()
        return r["tag_name"], [a["name"] for a in r["assets"]]

    file = Path(str(file).strip().replace("'", ""))

    # 1) 이미 존재하면 바로 반환 ---------------------------------------------------
    if file.exists():
        return str(file)

    # 2) URL 이 직접 들어왔을 때 ---------------------------------------------------
    if is_url(file):
        name = Path(urllib.parse.unquote(str(file))).name.split("?")[0]
        safe_download(name, str(file), min_bytes=min_bytes)
        return name

    # 3) GitHub release 에서 다운로드 ----------------------------------------------
    name = file.name
    # v8 계열에서 흔히 쓰는 가중치 이름 패턴
    common_assets = [
        f"yolov8{sz}{suf}.pt"
        for sz in ("n", "s", "m", "l", "x")
        for suf in ("", "-seg", "-cls", "-pose")
    ]

    try:
        tag, remote_assets = github_assets(repo, release)
    except Exception as e:
        LOGGER.warning(f"GitHub API 접속 실패: {e}")
        remote_assets = []

    # 요청 파일이 release 자산에 없더라도, common_assets 안에 있으면 진행
    if (name in remote_assets) or (name in common_assets):
        dest = file if file.suffix else file.with_suffix(".pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://github.com/{repo}/releases/download/{tag}/{name}"
        safe_download(dest, url, min_bytes=min_bytes,
                      error_msg=f"{name} 다운로드 실패. 수동으로 받아서 {dest} 위치에 두세요.")
        return str(dest)

    # 4) 여기까지 오면 찾을 수 없는 파일 --------------------------------------------
    raise FileNotFoundError(f"❌ '{name}' 을(를) {repo} release 에서 찾지 못했습니다.")