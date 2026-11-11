"""Reusable independent STL audit helpers and public P2 verification entry point.
Never imports the CAD generator. Run this file to audit the current three-piece kit.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import math
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'mechanical/stl/print'


def audit_mesh(path):
    mesh = trimesh.load_mesh(path, process=True)
    edges = np.vstack([mesh.faces[:, [0, 1]], mesh.faces[:, [1, 2]], mesh.faces[:, [2, 0]]])
    counts = Counter(map(tuple, np.sort(edges, axis=1)))
    directed = Counter(map(tuple, edges))
    adjacency = defaultdict(set)
    for a, b in counts:
        adjacency[a].add(b); adjacency[b].add(a)
    unseen = set(adjacency); shells = 0
    while unseen:
        stack = [unseen.pop()]; shells += 1
        while stack:
            neighbors = adjacency[stack.pop()] & unseen
            unseen.difference_update(neighbors); stack.extend(neighbors)
    report = dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  bounds_mm=mesh.bounds.tolist(), dimensions_mm=mesh.extents.tolist(),
                  volume_cm3=float(mesh.volume / 1000), watertight=bool(mesh.is_watertight),
                  consistent_winding=bool(mesh.is_winding_consistent), positive_signed_volume=bool(mesh.volume > 0),
                  bad_edges=sum(v != 2 for v in counts.values()),
                  duplicate_directed_edges=sum(v > 1 for v in directed.values()),
                  connected_shells=shells,
                  degenerate_faces=int(np.sum(mesh.area_faces < 1e-10)), faces=len(mesh.faces))
    report['pass'] = bool(report['watertight'] and report['consistent_winding'] and report['positive_signed_volume']
                          and report['bad_edges'] == report['duplicate_directed_edges'] == report['degenerate_faces'] == 0
                          and report['connected_shells'] == 1 and max(mesh.extents) <= 100)
    return mesh, report


def boundary_loops(mesh, face_mask):
    faces = mesh.faces[face_mask]
    edges = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    counts = Counter(map(tuple, np.sort(edges, axis=1)))
    remaining = {e for e, c in counts.items() if c == 1}
    adj = defaultdict(list)
    for a, b in remaining:
        adj[a].append(b); adj[b].append(a)
    assert all(len(v) == 2 for v in adj.values()), 'Plane boundary must consist of closed nonbranching loops'
    loops = []
    while remaining:
        a, b = next(iter(remaining)); loop = [a]; prev, cur = a, b
        remaining.remove(tuple(sorted((a, b))))
        while cur != a:
            loop.append(cur)
            nxt = next(v for v in adj[cur] if v != prev)
            remaining.remove(tuple(sorted((cur, nxt))))
            prev, cur = cur, nxt
        loops.append(mesh.vertices[loop])
    return loops


def polygon_area(points):
    return abs(np.sum(points[:, 0] * np.roll(points[:, 1], -1) - points[:, 1] * np.roll(points[:, 0], -1))) / 2


def point_segment_min(points, segments):
    a = segments; b = np.roll(segments, -1, axis=0); v = b - a
    w = points[:, None, :] - a[None, :, :]
    t = np.clip(np.sum(w * v[None, :, :], axis=2) / np.sum(v * v, axis=1), 0, 1)
    return float(np.linalg.norm(w - t[:, :, None] * v[None, :, :], axis=2).min())


def vertical_hits(mesh, x, y):
    tri = mesh.triangles; a = tri[:, 0]; v = tri[:, 1] - a; w = tri[:, 2] - a
    det = v[:, 0] * w[:, 1] - v[:, 1] * w[:, 0]
    safe = np.where(abs(det) < 1e-10, np.nan, det)
    dx = x - a[:, 0]; dy = y - a[:, 1]
    u = (dx * w[:, 1] - dy * w[:, 0]) / safe
    t = (v[:, 0] * dy - v[:, 1] * dx) / safe
    mask = (u >= -1e-7) & (t >= -1e-7) & (u + t <= 1 + 1e-7)
    return np.unique(np.round((a[:, 2] + u * v[:, 2] + t * w[:, 2])[mask], 6)).tolist()


if __name__ == '__main__':
    from verify_smartfan_p2_assembly import main
    main()
