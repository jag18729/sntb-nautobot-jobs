"""Pure checks for the synthetic fabric report. No Nautobot imports, so it is testable anywhere.

Input is a list of plain dicts, one per device:
    {"name": str, "role": str|None, "location": str|None, "primary_ip": str|None, "interfaces": int}
`primary_ip` is the bare host address (no mask).
"""

from __future__ import annotations

import ipaddress

LAB_NET = ipaddress.ip_network("10.99.0.0/16")
NAME_PREFIX = "syn-"


def check_fabric(devices: list[dict]) -> tuple[list[str], list[str]]:
    """Return (report_lines, problems). Any problem means the Job should fail."""
    report: list[str] = []
    problems: list[str] = []

    if not devices:
        # an empty answer must fail: a check that cannot fire looks the same as one that passes
        return report, ["no devices found (wrong tag, or the lab is empty)"]

    seen: dict[str, str] = {}
    for d in sorted(devices, key=lambda x: x["name"]):
        name = d["name"]
        ip = d.get("primary_ip")
        report.append(
            f"{name}: role={d.get('role')} location={d.get('location')} "
            f"primary_ip={ip} interfaces={d.get('interfaces', 0)}"
        )
        if not name.startswith(NAME_PREFIX):
            problems.append(f"{name}: not a synthetic hostname (must start with {NAME_PREFIX})")
        if not ip:
            problems.append(f"{name}: no primary IP")
            continue
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            problems.append(f"{name}: primary IP {ip!r} is not an address")
            continue
        if addr not in LAB_NET:
            problems.append(f"{name}: primary IP {ip} is outside {LAB_NET} (synthetic data only)")
        if ip in seen:
            problems.append(f"{name}: primary IP {ip} duplicates {seen[ip]}")
        seen[ip] = name
        if not d.get("interfaces"):
            problems.append(f"{name}: no interfaces")
    return report, problems
