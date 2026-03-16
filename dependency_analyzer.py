"""
Dependency analysis for local shared libraries.

Uses pyelftools when available and falls back to readelf for DT_NEEDED/SONAME
extraction, so the CLI can stay lightweight while still allowing better parsing.
"""

import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from os.path import join, normpath

try:
    from elftools.elf.elffile import ELFFile
except ImportError:  # pragma: no cover - optional dependency
    ELFFile = None


def is_shared_object(filename):
    lowered = filename.lower()
    return ".so" in filename or lowered.endswith(".dll") or lowered.endswith(".lib")


def collect_shared_objects(roots, recursive=True):
    files = []
    for root in roots:
        if recursive:
            for dirpath, _, filenames in os.walk(root):
                for name in filenames:
                    if is_shared_object(name):
                        full = join(dirpath, name)
                        if os.path.isfile(full):
                            files.append(full)
        else:
            for name in os.listdir(root):
                full = join(root, name)
                if os.path.isfile(full) and is_shared_object(name):
                    files.append(full)
    return sorted(set(files))


def parse_needed_and_soname_with_pyelftools(path):
    if ELFFile is None:
        return None
    try:
        with open(path, "rb") as fh:
            elf = ELFFile(fh)
            dynamic = elf.get_section_by_name(".dynamic")
            if dynamic is None:
                return [], None

            needed = []
            soname = None
            for tag in dynamic.iter_tags():
                if tag.entry.d_tag == "DT_NEEDED":
                    needed.append(tag.needed)
                elif tag.entry.d_tag == "DT_SONAME":
                    soname = tag.soname
            return needed, soname
    except Exception:
        return None


def run_readelf(path):
    try:
        return subprocess.check_output(
            ["readelf", "-d", path], stderr=subprocess.DEVNULL, text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def parse_needed_and_soname_with_readelf(path):
    out = run_readelf(path)
    needed = re.findall(r"\(NEEDED\).*?\[(.+?)\]", out)
    soname_match = re.search(r"\(SONAME\).*?\[(.+?)\]", out)
    soname = soname_match.group(1) if soname_match else None
    return needed, soname


def parse_needed_and_soname(path):
    parsed = parse_needed_and_soname_with_pyelftools(path)
    if parsed is not None:
        return parsed
    return parse_needed_and_soname_with_readelf(path)


def resolve_name(name, name_map, prefer_dir=None):
    candidates = name_map.get(name, [])
    if not candidates:
        return None
    if prefer_dir:
        for candidate in candidates:
            if os.path.dirname(candidate) == prefer_dir:
                return candidate
    return candidates[0]


def strongly_connected_components(nodes, graph):
    index = {}
    low = {}
    stack = []
    onstack = set()
    idx = 0
    components = []

    sys.setrecursionlimit(max(10000, len(nodes) + 50))

    def strongconnect(node):
        nonlocal idx
        index[node] = idx
        low[node] = idx
        idx += 1
        stack.append(node)
        onstack.add(node)

        for dep in graph.get(node, ()):
            if dep not in index:
                strongconnect(dep)
                low[node] = min(low[node], low[dep])
            elif dep in onstack:
                low[node] = min(low[node], index[dep])

        if low[node] == index[node]:
            component = []
            while True:
                dep = stack.pop()
                onstack.remove(dep)
                component.append(dep)
                if dep == node:
                    break
            components.append(component)

    for node in nodes:
        if node not in index:
            strongconnect(node)

    return components


def topological_sort(nodes, reverse_graph):
    indegree = {node: 0 for node in nodes}
    for _, users in reverse_graph.items():
        for user in users:
            indegree[user] += 1

    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for user in sorted(reverse_graph.get(node, [])):
            indegree[user] -= 1
            if indegree[user] == 0:
                queue.append(user)
    return order


def build_dependency_graph(files):
    meta = {}
    name_map = defaultdict(list)

    for path in files:
        basename = os.path.basename(path)
        needed, soname = parse_needed_and_soname(path)
        meta[path] = {"basename": basename, "soname": soname, "needed": needed}
        name_map[basename].append(path)
        if soname:
            name_map[soname].append(path)

    for key in name_map:
        name_map[key] = sorted(name_map[key])

    nodes = set(files)
    depends_on = {node: set() for node in nodes}
    reverse = {node: set() for node in nodes}
    unresolved = defaultdict(list)

    for path in files:
        prefer_dir = os.path.dirname(path)
        for need in meta[path]["needed"]:
            dep = resolve_name(need, name_map, prefer_dir=prefer_dir)
            if dep and dep in nodes and dep != path:
                depends_on[path].add(dep)
                reverse[dep].add(path)
            else:
                unresolved[path].append(need)

    return meta, depends_on, reverse, unresolved


def build_report_data(base_dir, roots, files, meta, depends_on, reverse, order, components, unresolved):
    def rel(path):
        return os.path.relpath(path, base_dir)

    nodes = {}
    lookup = {}
    for path in files:
        rel_path = rel(path)
        basename = meta[path]["basename"]
        soname = meta[path]["soname"]
        dependency_paths = sorted(rel(dep) for dep in depends_on[path])
        dependent_paths = sorted(rel(user) for user in reverse[path])
        unresolved_needed = sorted(unresolved.get(path, []))

        nodes[rel_path] = {
            "path": rel_path,
            "basename": basename,
            "soname": soname,
            "needed": meta[path]["needed"],
            "dependencies": dependency_paths,
            "dependents": dependent_paths,
            "unresolved_needed": unresolved_needed,
        }
        lookup.setdefault(rel_path, rel_path)
        lookup.setdefault(basename, rel_path)
        if soname:
            lookup.setdefault(soname, rel_path)

    cycles = []
    for component in components:
        if len(component) > 1:
            cycles.append(sorted(rel(path) for path in component))
        elif len(component) == 1:
            node = component[0]
            if node in depends_on.get(node, set()):
                cycles.append([rel(node)])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "roots": [normpath(root) for root in roots],
        "base_dir": normpath(base_dir),
        "nodes": nodes,
        "lookup": lookup,
        "libraries": sorted(nodes.keys()),
        "load_order": [rel(path) for path in order],
        "cycles": cycles,
        "parser_backend": "pyelftools" if ELFFile is not None else "readelf",
    }


def analyze_dependencies(roots, recursive=True):
    files = collect_shared_objects(roots, recursive=recursive)
    if not files:
        return None

    meta, depends_on, reverse, unresolved = build_dependency_graph(files)
    order = topological_sort(files, reverse)
    components = strongly_connected_components(set(files), depends_on)
    base_dir = os.path.commonpath(roots) if len(roots) > 1 else roots[0]
    return build_report_data(
        base_dir,
        roots,
        files,
        meta,
        depends_on,
        reverse,
        order,
        components,
        unresolved,
    )
