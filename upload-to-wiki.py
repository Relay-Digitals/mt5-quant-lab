#!/usr/bin/env python3
"""Bulk upload markdown files to Wiki.js via GraphQL.

Usage:
  python3 upload-to-wiki.py
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

WIKI_URL = "http://192.168.0.190:3000/graphql"
JWT = Path("/Users/ben/Downloads/AI-Selfhosted/wiki-jwt").read_text().strip()
LOCAL = Path("/Users/ben/Downloads/AI-Selfhosted")

# (local file, wiki path, title, description, tags)
PAGES = [
    (
        "INFRASTRUCTURE-OVERVIEW.md",
        "infrastructure/overview",
        "Infrastructure Overview",
        "Snapshot semua CT, endpoint, DNS, dan resource Proxmox lab",
        ["infrastructure", "overview", "proxmox"],
    ),
    (
        "SETUP.md",
        "services/stable-diffusion/setup",
        "Stable Diffusion (OpenVINO) — Setup",
        "Stable Diffusion 1.5 + SDXL-Turbo via OpenVINO di Intel iGPU",
        ["stable-diffusion", "openvino", "image-gen", "setup"],
    ),
    (
        "WAHA-SETUP.md",
        "services/whatsapp-bot/setup",
        "WhatsApp Bot (WAHA) — Setup Runbook",
        "Setup self-hosted WhatsApp HTTP API dari nol sampai aktif kirim OTP",
        ["whatsapp", "waha", "otp", "setup"],
    ),
    (
        "WAHA-API.md",
        "services/whatsapp-bot/api-reference",
        "WhatsApp Bot (WAHA) — API Reference",
        "Reference semua endpoint REST WAHA dengan curl/Python/Node example",
        ["whatsapp", "waha", "api", "reference"],
    ),
    (
        "BROWSER-MCP-SETUP.md",
        "services/browser-automation/setup",
        "Browser Automation — Setup Runbook",
        "Setup Browserless + Playwright MCP server untuk script & LLM agent",
        ["browser", "playwright", "mcp", "browserless", "setup"],
    ),
    (
        "BROWSER-MCP-API.md",
        "services/browser-automation/api-reference",
        "Browser Automation — API Reference",
        "Reference Browserless REST/WS + Playwright MCP tools + code examples",
        ["browser", "playwright", "mcp", "browserless", "api", "reference"],
    ),
    (
        "POSTAL-SETUP.md",
        "services/mail-server/setup",
        "Postal SMTP Server — Setup Runbook",
        "Self-hosted Postal SMTP multi-tenant relay di Proxmox LXC",
        ["mail", "smtp", "postal", "setup"],
    ),
    (
        "POSTAL-API.md",
        "services/mail-server/api-reference",
        "Postal SMTP Server — API Reference",
        "REST API + SMTP submission + webhook + DNS setup + IP warming",
        ["mail", "smtp", "postal", "api", "reference"],
    ),
]


def gql(query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        WIKI_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {JWT}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode(), "status": e.code}


CREATE_MUTATION = """
mutation CreatePage(
  $content: String!
  $description: String!
  $editor: String!
  $isPublished: Boolean!
  $isPrivate: Boolean!
  $locale: String!
  $path: String!
  $tags: [String]!
  $title: String!
) {
  pages {
    create(
      content: $content
      description: $description
      editor: $editor
      isPublished: $isPublished
      isPrivate: $isPrivate
      locale: $locale
      path: $path
      tags: $tags
      title: $title
    ) {
      responseResult { succeeded errorCode slug message }
      page { id title path }
    }
  }
}
"""


def main() -> int:
    rc = 0
    print(f"Wiki.js: {WIKI_URL}")
    print(f"Uploading {len(PAGES)} pages\n")

    for filename, path, title, description, tags in PAGES:
        fp = LOCAL / filename
        if not fp.exists():
            print(f"  SKIP {filename} (not found)")
            rc = 1
            continue

        content = fp.read_text()
        size_kb = len(content) / 1024

        result = gql(
            CREATE_MUTATION,
            {
                "content": content,
                "description": description,
                "editor": "markdown",
                "isPublished": True,
                "isPrivate": False,
                "locale": "en",
                "path": path,
                "tags": tags,
                "title": title,
            },
        )

        if "error" in result:
            print(f"  FAIL {filename} -> /{path}  ({size_kb:.1f}KB): HTTP {result['status']}")
            print(f"        {result['error'][:200]}")
            rc = 1
            continue

        data = result.get("data", {}).get("pages", {}).get("create", {})
        rr = data.get("responseResult", {})

        if rr.get("succeeded"):
            page = data.get("page", {})
            print(f"  OK   {filename}  ->  /{path}  ({size_kb:.1f}KB)  id={page.get('id')}")
        else:
            print(f"  FAIL {filename} -> /{path}  ({size_kb:.1f}KB)")
            print(f"        {rr.get('errorCode')}: {rr.get('message')}")
            rc = 1

    print()
    list_q = '{ pages { list { id title path } } }'
    final = gql(list_q, {})
    pages_now = final.get("data", {}).get("pages", {}).get("list", [])
    print(f"Total pages in wiki now: {len(pages_now)}")
    for p in pages_now:
        print(f"  - /{p['path']}   {p['title']}")

    return rc


if __name__ == "__main__":
    sys.exit(main())
