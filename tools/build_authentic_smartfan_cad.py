"""P2 concept geometry. Independent STL verification is required before printing.
Panel z=31-tan(25)*(y-55); actual key cap model is not available.
"""
from pathlib import Path
import argparse
import math
import shutil
import zipfile
import trimesh
from manifold3d import Manifold
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / 'mechanical' / 'stl' / 'print'
ANGLE = 25.0
PCB_THICKNESS = 1.6  # Assembly requirement; verify against fabricated board.
MODULE_BOTTOM_Z = 8.1  # Required mounting datum, NOT a measured module placement.
BUTTON_HEIGHT = 15.0  # User supplied: module PCB bottom to button top.
BUTTON_PROTRUSION = 1.35  # Vertical convention, conditional on MODULE_BOTTOM_Z.
SPLIT_Z = 9.0
BOSSES = [(7, 7), (92, 7), (7, 92), (92, 92)]


def panel_z(y):
    return 31.0 - math.tan(math.radians(ANGLE)) * (y - 55.0)


def panel_above(normal_offset=0):
    return (Manifold.cube([140, 180, 100], center=True)
            .translate([0, 0, 50 + normal_offset])
            .rotate([-ANGLE, 0, 0]).translate([49.5, 55, 31]))


def panel_hole(x, y, diameter):
    return (Manifold.cylinder(12, diameter / 2, diameter / 2, circular_segments=96)
            .translate([0, 0, -6]).rotate([-ANGLE, 0, 0])
            .translate([x, y, panel_z(y)]))


def export_part(filename, solid):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = solid.to_mesh()
    mesh = trimesh.Trimesh(vertices=raw.vert_properties[:, :3], faces=raw.tri_verts, process=True)
    path = OUTPUT_DIR / filename
    mesh.export(path)
    print(f'{filename}: {mesh.extents.tolist()} mm, {mesh.volume / 1000:.6f} cm3')
    return path


def build_detailed_base_piece1():
    outer = Manifold.cube([99, 99, 32]) - panel_above()
    # 28mm high inner cavity z2..30; actual top deck z30..32.
    inner = Manifold.cube([95.8, 95.8, 28]).translate([1.6, 1.6, 2]) - panel_above(-2)
    base = outer - inner
    for x, y in BOSSES:
        boss = Manifold.cylinder(4.5, 3.2, 3.2, circular_segments=48).translate([x, y, 2])
        # 2.1mm pilot for a separately tapped M2.5 thread; test print required.
        bore = Manifold.cylinder(6, 1.05, 1.05, circular_segments=48).translate([x, y, 1.5])
        base = base + boss - bore
    oled = (Manifold.cube([28, 16.5, 12], center=True).rotate([-ANGLE, 0, 0])
            .translate([80.5, 64, panel_z(64)]))
    base -= oled
    # XY identifies actual outer surface centre, not an arbitrary axis point.
    for x, y, d in [(18, 76, 10), (73, 88, 9), (92, 88, 2.5)]:
        base -= panel_hole(x, y, d)
    button_z = MODULE_BOTTOM_Z + BUTTON_HEIGHT - BUTTON_PROTRUSION
    for x in [36, 51.5]:
        # 25-degree local top, shifted vertically; bore is vertical for the
        # explicit vertical-button assumption (surface outline is elliptical).
        crown = Manifold.cylinder(18, 6, 6, circular_segments=96).translate([x, 86, 8])
        crown -= panel_above().translate([0, 0, button_z - panel_z(86)])
        crown = crown - (crown - panel_above(-2))
        base += crown
        base -= Manifold.cylinder(30, 3.5, 3.5, circular_segments=96).translate([x, 86, 2])
    dc = (Manifold.cylinder(15, 4.1, 4.1, circular_segments=64)
          .translate([0, 0, -7.5]).rotate([90, 0, 0]).translate([17, 1, 10]))
    usb = Manifold.cube([11, 15, 6.5], center=True).translate([49.5, 1, 8])
    base = base - dc - usb
    servo = Manifold.cube([23.2, 12.6, 12], center=True).translate([49.5, 35, 30])
    # Connected wire passage.
    wire = Manifold.cube([10, 6.3, 12], center=True).translate([49.5, 25.85, 30])
    base = base - servo - wire
    for x in [35.5, 63.5]:
        base -= Manifold.cylinder(12, 1.3, 1.3, circular_segments=48).translate([x, 35, 24])
    lid, lower = base.split_by_plane([0, 0, 1], SPLIT_Z)
    for x, y in BOSSES:
        seat_z = 32.0 if y == 7 else panel_z(y - 2.5)
        spacer = Manifold.cylinder(seat_z - 8.1, 2.5, 2.5, circular_segments=64).translate([x, y, 8.1])
        lid += spacer
        lid -= Manifold.cylinder(40, 1.4, 1.4, circular_segments=64).translate([x, y, 0])
    return [export_part('SmartFan_Piece1_Base_Enclosure.stl', lower),
            export_part('SmartFan_Piece3_Removable_Lid.stl', lid)]


def build_detailed_gimbal_piece2():
    saddle = Manifold.cube([84, 30, 3])
    housing = Manifold.cube([26, 22, 21]).translate([29, 4, 3])
    cavity = Manifold.cube([20.4, 15.4, 25], center=True).translate([42, 15, 15])
    axle = Manifold.cylinder(12, 1.5, 1.5, circular_segments=48).rotate([90, 0, 0]).translate([42, 27, 15])
    gimbal = saddle + (housing - cavity - axle)
    for x in [2, 58]:
        # Non-load-rated decorative wings: 2mm walls, 11mm height.
        wing = Manifold.cube([24, 26, 11]).translate([x, 2, 3])
        air = Manifold.cube([20, 22, 13]).translate([x + 2, 4, 2])
        gimbal += wing - air
    for size in [[18, 4.8, 2.5], [4.8, 18, 2.5]]:
        gimbal -= Manifold.cube(size, center=True).translate([42, 15, 1.25])
    gimbal -= Manifold.cylinder(5, 1.4, 1.4, circular_segments=48).translate([42, 15, 0])
    return export_part('SmartFan_Piece2_Fan_Gimbal_Bracket.stl', gimbal)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sync-download', type=Path, help='Opt-in destination; default is project only')
    args = parser.parse_args()
    paths = build_detailed_base_piece1() + [build_detailed_gimbal_piece2()]
    archive = OUTPUT_DIR / 'SmartFan_P2_Print_Kit.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in paths:
            z.write(path, path.name)
    if args.sync_download:
        args.sync_download.mkdir(parents=True, exist_ok=True)
        for path in paths + [archive]:
            shutil.copyfile(path, args.sync_download / path.name)
    print('Exported; independent mechanical verification required.')


if __name__ == '__main__':
    main()
