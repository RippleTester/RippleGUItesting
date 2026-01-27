from datetime import datetime
from pathlib import Path

from src.utils.file_util import FileUtil
from config import BUILDS_JSON_LINK, APP_NAME_FIREFOX, DATA_DIR
import requests
from bisect import bisect_left


class Build:
    def __init__(self, node=None, buildid=None, channel=None, platform=None, app_version=None, files_url=None):
        self.node = node  # commit changeset "5f5c3d10232a7d3c4da4e4108bd5a4035f6b8524"
        self.buildid = buildid  # 20250529033404
        self.channel = channel  # "nightly"
        self.platform = platform  # linux32
        self.app_version = app_version  # 141.0a1
        self.files_url = files_url  # "https://archive.mozilla.org/pub/firefox/nightly/2025/05/2025-05-29-03-34-04-mozilla-central/"

    def __repr__(self):
        return

    def __str__(self):
        return

    @staticmethod
    def fetch_firefox_builds(app_name=APP_NAME_FIREFOX, filename='builds.json'):
        # also in CrawlUtil
        # API_URL = "https://hg.mozilla.org/mozilla-central/json-firefoxreleases"

        builds = requests.get(BUILDS_JSON_LINK, timeout=10).json()
        # 该接口返回 releases，而我们用 builds 字段名来统一
        # return data.get('builds', [])
        FileUtil.dump_json(Path(DATA_DIR, app_name, f"{filename}"), builds)
        return builds

    @staticmethod
    def group_by_platform(builds):
        """
        按 platform 分组，并按 buildid 字符串（YYYYMMDDHHMMSS）的 lexicographical 顺序排序。
        由于 buildid 使用 ISO-like 数字格式，字符串排序即时间排序。
        返回 dict: { platform: [build_records...] }
        """
        by_plat = {}
        for rec in builds:
            if rec.get("channel") != "nightly":
                continue
            by_plat.setdefault(rec["platform"], []).append(rec)
        for lst in by_plat.values():
            lst.sort(key=lambda r: r["buildid"])
        return by_plat

    @staticmethod
    def find_build_bounds(push_dt_iso, builds_by_plat):
        """
        给定 push datetime 字符串（ISO8601，带或不带 Z），
        计算每个平台上：
          • last_without：最后一个 buildid < push_datetime
          • first_with：第一个 buildid >= push_datetime

        使用字符串 bisect，无需转换到 datetime 列表。

        返回 dict: { platform: { 'last_without': record|None, 'first_with': record|None } }
        """
        # 把 push_dt_iso 转为构建可比较的 buildid_str
        # 例如 "2020-01-29T03:50:12Z" -> "20200129035012"
        dt = datetime.fromisoformat(push_dt_iso.rstrip("Z"))
        push_key = dt.strftime("%Y%m%d%H%M%S")

        # builds = fetch_builds()
        # by_plat = group_by_platform(builds)
        result = {}

        for plat, lst in builds_by_plat.items():
            # 提取每个记录的 buildid 字符串
            keys = [r["buildid"] for r in lst]
            idx = bisect_left(keys, push_key)
            last = lst[idx - 1] if idx > 0 else None
            first = lst[idx] if idx < len(lst) else None
            result[plat] = {"last_without": last, "first_with": first}

        return result

    @staticmethod
    def get_first_with_last_without_buildid_by_push_datetime(push_dt_iso, app_name=APP_NAME_FIREFOX):
        builds = FileUtil.load_json(Path(DATA_DIR, app_name, "builds.json"))
        builds = builds.get("builds", [])
        builds_by_plat = Build.group_by_platform(builds)
        result = Build.find_build_bounds(push_dt_iso, builds_by_plat)
        return result




