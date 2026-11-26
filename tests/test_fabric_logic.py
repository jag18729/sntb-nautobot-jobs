"""Mutation tests for the fabric rules. Every rule has a bad input that must produce a problem."""

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

# load the pure module directly: importing the `jobs` package would need Nautobot
_p = Path(__file__).resolve().parents[1] / "jobs" / "fabric_logic.py"
_spec = importlib.util.spec_from_file_location("fabric_logic", _p)
fl = importlib.util.module_from_spec(_spec)
sys.modules["fabric_logic"] = fl
_spec.loader.exec_module(fl)

GOOD = [
    {"name": "syn-spine-01", "role": "syn-spine", "location": "syn-site-a", "primary_ip": "10.99.0.11", "interfaces": 5},
    {"name": "syn-leaf-01", "role": "syn-leaf", "location": "syn-site-a", "primary_ip": "10.99.0.21", "interfaces": 4},
]


def run(mutate):
    d = copy.deepcopy(GOOD)
    mutate(d)
    return fl.check_fabric(d)


def test_healthy_fabric_has_no_problems():
    report, problems = fl.check_fabric(GOOD)
    assert problems == [] and len(report) == 2


MUTANTS = {
    "empty answer": (lambda d: d.clear(), "no devices"),
    "real-looking hostname": (lambda d: d[0].update(name="pi2"), "not a synthetic hostname"),
    "no primary ip": (lambda d: d[0].update(primary_ip=None), "no primary IP"),
    "real lan address": (lambda d: d[0].update(primary_ip="192.0.2.50"), "outside"),
    "other 10.x": (lambda d: d[0].update(primary_ip="10.98.0.1"), "outside"),
    "garbage address": (lambda d: d[0].update(primary_ip="nope"), "not an address"),
    "duplicate ip": (lambda d: d[1].update(primary_ip="10.99.0.11"), "duplicates"),
    "no interfaces": (lambda d: d[1].update(interfaces=0), "no interfaces"),
}


@pytest.mark.parametrize("name", MUTANTS)
def test_every_rule_goes_red(name):
    fn, needle = MUTANTS[name]
    _, problems = run(fn)
    assert any(needle in p for p in problems), f"mutant survived: {name} -> {problems}"


def test_meta_check_widening_the_net_lets_a_real_address_through(monkeypatch):
    """Disable the address rule: the bad input must now pass, proving the rule is what fires."""
    bad = lambda d: d[0].update(primary_ip="192.0.2.50")  # noqa: E731
    assert run(bad)[1]
    import ipaddress

    monkeypatch.setattr(fl, "LAB_NET", ipaddress.ip_network("0.0.0.0/0"))
    assert run(bad)[1] == []


def test_no_real_addresses_in_the_repo():
    """The repo is public. Only 10.99.x may appear as a literal address, plus the test mutants."""
    import re

    root = Path(__file__).resolve().parents[1]
    allowed = ("10.99.", "10.98.0.1", "192.0.2.50", "0.0.0.0")
    bad = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".md", ".yml"} and ".git" not in p.parts:
            for m in re.finditer(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", p.read_text()):
                if not m.group(0).startswith(allowed):
                    bad.append((str(p.relative_to(root)), m.group(0)))
    assert bad == []
