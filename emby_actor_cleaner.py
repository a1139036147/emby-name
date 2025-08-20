#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emby 演员信息重命名工具

功能：
- 遍历 Emby 数据库中所有演员(Person)
- 检测名字里是否包含 '/'，如果有则只保留第一个 '/' 前的部分作为新名字
- 调用 Emby API 执行重命名

使用示例：
python emby_actor_cleaner.py rename --server http://127.0.0.1:8096 --api-key <KEY>
"""
import argparse
import os
import sys
import time
import urllib.parse
import requests

REQUEST_TIMEOUT = 20
SLEEP_BETWEEN_CALLS = 0.05

class EmbyClient:
    def __init__(self, base_url: str, api_key: str, user_id: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.user_id = user_id
        self.session = requests.Session()
        self.session.headers.update({
            "X-Emby-Token": api_key,
            "X-Emby-Authorization": "MediaBrowser Client=EmbyActorRenamer, Device=Script, DeviceId=actor-cleaner, Version=1.0.0"
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path if path.startswith('/emby') else '/emby'+path}"

    def get(self, path: str, params: dict | None = None) -> dict:
        url = self._url(path)
        resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, json_body: dict | None = None, params: dict | None = None):
        url = self._url(path)
        resp = self.session.post(url, json=json_body, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp

    def update_person(self, item_id: str, new_name: str) -> bool:
        """Update person name.

        Returns True on success, False if the person was not found (HTTP 404).
        Other HTTP errors are raised.
        """
        try:
            data = self.get(f"/emby/Items/{item_id}")
            data["Name"] = new_name
            self.post(f"/emby/Items/{item_id}", json_body=data)
            return True
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return False
            raise

    def iter_persons(self, limit: int | None = None):
        start = 0
        returned = 0
        while True:
            params = {
                "StartIndex": start,
                "Limit": 200,
                "Fields": "ProviderIds,SortName,Overview",
            }
            if self.user_id:
                params["UserId"] = self.user_id
            data = self.get("/emby/Persons", params=params)
            items = data.get("Items", [])
            if not items:
                break
            for it in items:
                yield it
                returned += 1
                if limit and returned >= limit:
                    return
            start += len(items)
            time.sleep(SLEEP_BETWEEN_CALLS)


def rename_persons(client: EmbyClient, dry_run: bool = False, limit: int | None = None):
    persons = list(client.iter_persons(limit=limit))
    changes: list[dict] = []
    not_found: list[str] = []
    for p in persons:
        name = p.get("Name", "")
        if "/" in name:
            new_name = name.split("/")[0].strip()
            if new_name and new_name != name:
                if dry_run:
                    changes.append({"id": p["Id"], "old": name, "new": new_name, "action": "would_rename"})
                else:
                    try:
                        success = client.update_person(p["Id"], new_name)
                        if success:
                            changes.append({"id": p["Id"], "old": name, "new": new_name, "action": "renamed"})
                        else:
                            not_found.append(p["Id"])
                            print(f"[!] 未找到该 Id {p['Id']}")
                    except Exception as e:
                        changes.append({"id": p["Id"], "old": name, "new": new_name, "action": "error", "error": str(e)})
    return changes, not_found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emby 演员重命名工具")
    parser.add_argument("--server", default=os.getenv("EMBY_URL"), help="Emby 服务器地址")
    parser.add_argument("--api-key", default=os.getenv("EMBY_API_KEY"), help="Emby API Key")
    parser.add_argument("--user-id", default=os.getenv("EMBY_USER_ID"), help="（可选）UserId")
    parser.add_argument("--limit", type=int, default=None, help="最多处理多少个 Person")
    parser.add_argument("--dry-run", action="store_true", help="演练模式，不写入，仅输出")
    args = parser.parse_args(argv)

    if not args.server or not args.api_key:
        print("[!] 需要 --server 与 --api-key 参数，或设置环境变量 EMBY_URL/EMBY_API_KEY", file=sys.stderr)
        return 2

    client = EmbyClient(args.server, args.api_key, args.user_id)
    changes, missing = rename_persons(client, dry_run=args.dry_run, limit=args.limit)

    print(f"[i] 共检测到 {len(changes)} 个需要改名的演员")
    for c in changes:
        print(f"[{c['action']}] {c['old']} -> {c['new']}")
    if missing:
        print(f"[!] 共 {len(missing)} 个 Id 未找到: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
