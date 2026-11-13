#!/usr/bin/env python3
"""Check CloudFormation templates against the Quiverstone template standard.

Usage: check-cfn-standards.py [--repo armory|arsenal] [paths...]
With no paths, every *.yaml under a templates/ or _archive/ directory is checked.
Exit code 1 when any violation is found.

Requires cfn-lint (pip install cfn-lint) for template decoding and resource schemas.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

from cfnlint.decode import decode
from cfnlint.schema import PROVIDER_SCHEMA_MANAGER

ORDER = [
    "AWSTemplateFormatVersion",
    "Description",
    "Metadata",
    "Transform",
    "Parameters",
    "Mappings",
    "Conditions",
    "Rules",
    "Resources",
    "Outputs",
]
PREFIXES = {"Parameters": "p", "Resources": "r", "Conditions": "c", "Outputs": "o", "Mappings": "m"}
CRITICAL = {
    "AWS::S3::Bucket",
    "AWS::KMS::Key",
    "AWS::DynamoDB::Table",
    "AWS::RDS::DBInstance",
    "AWS::RDS::DBCluster",
    "AWS::ElastiCache::ReplicationGroup",
    "AWS::ECR::Repository",
}
TEMPLATE_DIRS = re.compile(r"(^|/)(templates|_archive)/")


def taggable(resource_type: str) -> str | None:
    """Return 'list' or 'map' when the resource type supports Tags, else None."""
    try:
        schema = PROVIDER_SCHEMA_MANAGER.get_resource_schema("us-east-1", resource_type).schema
    except Exception:  # unknown/custom resource types are not taggable here
        return None
    tags = schema.get("properties", {}).get("Tags")
    if not tags:
        return None
    return "map" if tags.get("type") == "object" else "list"


def has_github_tag(tags, expected: str) -> bool:
    if isinstance(tags, dict):
        return tags.get("GitHub") == expected
    if isinstance(tags, list):
        return any(isinstance(t, dict) and t.get("Key") == "GitHub" and t.get("Value") == expected for t in tags)
    return False


def check(path: pathlib.Path, repo: str) -> list[str]:
    errors: list[str] = []
    if path.suffix != ".yaml":
        errors.append("file extension must be .yaml")
    template, matches = decode(str(path))
    if matches or not isinstance(template, dict):
        return errors + [f"cannot parse: {m.message}" for m in matches]

    keys = [k for k in template if k in ORDER]
    if keys != sorted(keys, key=ORDER.index):
        errors.append(f"sections out of order: {keys}")
    for required in ("AWSTemplateFormatVersion", "Description", "Parameters", "Resources"):
        if required not in template:
            errors.append(f"missing section {required}")

    for section, prefix in PREFIXES.items():
        for name in template.get(section) or {}:
            if not re.match(rf"^{prefix}[A-Z0-9][A-Za-z0-9]*$", name):
                errors.append(f"{section}.{name}: name must be {prefix}<PascalCase>")
    for name in template.get("Metadata") or {}:
        if not (name.startswith("meta") or name.startswith("AWS::") or name == "cfn-lint"):
            errors.append(f"Metadata.{name}: name must start with meta")

    for name, param in (template.get("Parameters") or {}).items():
        if "Description" not in param:
            errors.append(f"Parameters.{name}: missing Description")
        if ("AllowedValues" in param or "AllowedPattern" in param) and "ConstraintDescription" not in param:
            errors.append(f"Parameters.{name}: constrained parameter needs ConstraintDescription")

    expected_tag = f"quiverstone/{repo}"
    for name, res in (template.get("Resources") or {}).items():
        rtype = res.get("Type", "")
        props = res.get("Properties") or {}
        if taggable(rtype) and not has_github_tag(props.get("Tags"), expected_tag):
            errors.append(f"Resources.{name}: missing tag GitHub={expected_tag}")
        if rtype in CRITICAL and ("DeletionPolicy" not in res or "UpdateReplacePolicy" not in res):
            errors.append(f"Resources.{name}: {rtype} needs DeletionPolicy and UpdateReplacePolicy")
        if rtype == "AWS::IAM::Role" and props.get("Policies"):
            errors.append(f"Resources.{name}: inline Policies not allowed, use AWS::IAM::ManagedPolicy")
        if rtype == "AWS::IAM::Policy":
            errors.append(f"Resources.{name}: AWS::IAM::Policy is inline, use AWS::IAM::ManagedPolicy")

    for name, out in (template.get("Outputs") or {}).items():
        if "Description" not in out:
            errors.append(f"Outputs.{name}: missing Description")
        if "Export" not in out and "nonce" not in name.lower():
            errors.append(f"Outputs.{name}: missing Export")
    return errors


def default_paths() -> list[pathlib.Path]:
    files = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"], capture_output=True, text=True, check=True
    ).stdout.split()
    return [
        pathlib.Path(f)
        for f in files
        if TEMPLATE_DIRS.search(f) and f.endswith((".yaml", ".yml", ".template", ".json"))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=pathlib.Path.cwd().name, help="repository name used for the GitHub tag value")
    parser.add_argument("paths", nargs="*", type=pathlib.Path)
    args = parser.parse_args()

    failed = 0
    for path in args.paths or default_paths():
        for err in check(path, args.repo):
            print(f"{path}: {err}")
            failed += 1
    print(f"{failed} standards violation(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
