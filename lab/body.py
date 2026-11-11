#!/usr/bin/env blender --background --python
"""A member's body, built from parameters. Run with Blender, not with python3.

    /Applications/Blender.app/Contents/MacOS/Blender --background --python lab/body.py -- \
        --name dmitri --height 1.88 --build 0.95 --kit 3f5f6f --skin 8d5a3b --out games/tennis/bodies

Why a mannequin, and not a person. The members are not people; the engine's footwork is a formula, not
biomechanics. An artist's lay figure is the honest shape for that — a body for studying motion,
ball-jointed and faceless, with no claim to a face the record does not contain. It is also the look that
survives being built by code: faceted, deliberate, and not trying to be a photograph of anyone.

Everything here is ours: no generator, no vendor, no key. The description the user types becomes these
parameters, and the parameters become geometry.

Every number in PROPORTIONS was measured off `games/tennis/bodies/reference/woman-*.jpg` with
`lab/reference.py` and is expressed as a fraction of the figure's own height, so it survives being applied
to a member of any height. The first build guessed these and got the legs half as wide as a real woman's
and the neck a third too thick; guessing proportions is how a mannequin becomes a cartoon.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


# Blender's factory scene ships a cube at the origin, which stands exactly where the figure stands and
# hides its legs. The first render was a photograph of that cube.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures):
    for item in list(block):
        if item.users == 0:
            block.remove(item)


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


NAME = arg("--name", "member")
HEIGHT = float(arg("--height", "1.80"))          # metres, top of head
BUILD = float(arg("--build", "1.0"))            # 0.85 slight .. 1.25 heavy; girth, not height
KIT = arg("--kit", "3f6f7f")
SKIN = arg("--skin", "8d5a3b")
HAIR = arg("--hair", "2b2119")
OUT = arg("--out", ".")
POSE = arg("--pose", "stance")        # "rest" = neutral standing pose, for measuring against a reference
RACQUET = arg("--racquet", "1") == "1"
LOWER = arg("--lower", "skirt")       # skirt | shorts | none — the kit below the waist
RENDER = arg("--render", "hero")      # "measure" = orthographic, flat light, no floor, no shadow
VIEW = arg("--view", "front")         # "side" turns the measuring camera 90 degrees to read depths


def hex_rgb(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def material(name, colour, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(colour)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = hex_rgb(colour)      # the Workbench preview reads this, not the node tree
    return m


MAT_SKIN = material("skin", SKIN, 0.62)
MAT_KIT = material("kit", KIT, 0.72)
MAT_HAIR = material("hair", HAIR, 0.85)
MAT_GRIP = material("grip", "22262a", 0.65)
MAT_FRAME = material("racquet", "d9d3c4", 0.35, 0.15)

# ---- proportions, measured ------------------------------------------------------------------------
# Source: woman-front-open-1 (widths, arms clear of the body), woman-side-armsdown-1 (depths),
# woman-front-closed-1 (legs together), all read with lab/reference.py. Widths are full widths divided by
# the figure's height; the code wants half-widths, so they are halved here.
h = HEIGHT
girth = BUILD ** 0.7              # a heavy build is thicker, not wider across the shoulders
head_h = h / 7.6                  # kept for the head's own proportions; see NOTE at the bottom

PROPORTIONS = {
    "head_rx": 0.0510,            # 0.102 wide, measured
    "head_ry": 0.0535,            # 0.107 deep (side view, ponytail excluded)
    "head_rz": 0.0710,
    "head_c":  0.9250,            # centre of the head sphere; crown lands at ~1.00 h
    "neck_r":  0.0325,            # 0.065 wide, measured — was 0.043, a third too thick
    "neck_top": 0.8800,
    "neck_bot": 0.8050,
    "shoulder_x": 0.0965,         # shoulder line 0.245 total with the arm's radius on top
    "shoulder_z": 0.8150,
    "deltoid_r": 0.0270,
    "arm_r0": 0.0280,             # upper arm at the shoulder — 0.050 wide is what the biceps measures
    "arm_r1": 0.0230,             # at the elbow
    "fore_r0": 0.0220,
    "fore_r1": 0.0140,            # at the wrist
    "elbow_z": 0.6340,            # measured: the elbow sits at 0.634 h, the wrist just below the hip line
    "wrist_z": 0.4880,
    "chest_x": 0.0790, "chest_y": 0.0645, "chest_z": 0.7200,
    "waist_x": 0.0780, "waist_y": 0.0620, "waist_z": 0.6000,
    "pelvis_x": 0.0930, "pelvis_y": 0.0700, "pelvis_z": 0.5200,
    "hip_x": 0.0450,              # leg centres: 0.090 apart at the hip joint
    "knee_x": 0.0785,             # 0.157 apart at the knee, measured
    "ankle_x": 0.0905,            # 0.181 apart at the ankle, measured — the legs splay, they do not run parallel
    "knee_z": 0.2600,             # measured, not the textbook 0.28
    "thigh_r0": 0.0530, "thigh_r1": 0.0390, "thigh_r2": 0.0305,
    "shin_r0": 0.0305, "calf_r": 0.0310, "calf_z": 0.2100, "ankle_r": 0.0190,
    "foot_len": 0.1450, "foot_w": 0.0450, "foot_h": 0.0380,
}
P = {k: (v * h if isinstance(v, float) else v) for k, v in PROPORTIONS.items()}
P["hip_x"] *= BUILD ** 0.35       # a heavier build stands a little wider, a slighter one narrower
P["knee_x"] = P["knee_x"] * BUILD ** 0.35
P["ankle_x"] = P["ankle_x"] * BUILD ** 0.35

PARTS = []            # (object, bone) — every piece knows which bone owns it. No name-matching heuristics.


def add(obj, mat, name, bone):
    obj.name = name
    obj.data.materials.append(mat)
    PARTS.append((obj, bone))
    return obj


def sphere(loc, scale, mat, name, bone, segments=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=loc)
    o = bpy.context.object
    o.scale = scale
    return add(o, mat, name, bone)


def cone(a, b, r0, r1, mat, name, bone, segments=16):
    """A limb segment as a taper: radius r0 at a, r1 at b. A capsule would make every limb a tube, and a
    thigh that does not taper is a leg drawn by someone who has not looked at one."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=segments, radius1=r0, radius2=r1, depth=d.length,
                                    location=(a + b) / 2)
    o = bpy.context.object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return add(o, mat, name, bone)


def loft(sections, mat, name, bone, segments=24, caps=True):
    """A torso, as the thing a torso actually is: rings at a series of heights, skinned. Three spheres
    stacked where a trunk goes was the first version, and it read as three spheres stacked where a trunk
    goes. Each section is bound to its own bone, so the waist can still bend."""
    me = bpy.data.meshes.new(name + ".mesh")
    bm = bmesh.new()
    rings = []
    for z, rx, ry in sections:
        rings.append([bm.verts.new((rx * math.cos(2 * math.pi * i / segments),
                                    ry * math.sin(2 * math.pi * i / segments), z))
                      for i in range(segments)])
    for lo, hi in zip(rings, rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    if caps:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return add(o, mat, name, bone)


def box(loc, size, mat, name, bone, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.object
    o.scale = size
    o.rotation_euler = rot
    return add(o, mat, name, bone)


# ---- the body -------------------------------------------------------------------------------------
# Head and hair. The hair is a skullcap, not a wig: it must not hang past the jaw, because the first build's
# hair reached the shoulders and made the neck unmeasurable in its own silhouette.
sphere((0, 0, P["head_c"]), (P["head_rx"], P["head_ry"], P["head_rz"]), MAT_SKIN, "head", "head")
sphere((0, -0.004 * h, P["head_c"] + 0.030 * h),
       (P["head_rx"] * 1.02, P["head_ry"] * 1.02, P["head_rz"] * 0.62), MAT_HAIR, "hair", "head")

cone((0, 0, P["neck_bot"]), (0, 0, P["neck_top"]), P["neck_r"] * 1.12, P["neck_r"], MAT_SKIN, "neck", "neck")

# The trunk, in three sections that share their boundary rings, so the silhouette is continuous but the
# waist and chest are still separate bones.
# The trunk ends at the crotch, 0.465 h, not at 0.43: sinking it lower made a dress, and the first render of
# this build wore one.
LOFT_HIPS = [(0.465 * h, 0.050 * h, 0.036 * h), (0.478 * h, 0.078 * h, 0.056 * h),
             (0.500 * h, 0.090 * h, 0.064 * h), (0.520 * h, P["pelvis_x"], P["pelvis_y"]),
             (0.560 * h, 0.090 * h, 0.063 * h), (0.600 * h, P["waist_x"], P["waist_y"])]
LOFT_SPINE = [(0.600 * h, P["waist_x"], P["waist_y"]), (0.640 * h, 0.0770 * h, 0.0570 * h),
              (0.680 * h, 0.0775 * h, 0.0580 * h), (0.720 * h, P["chest_x"], P["chest_y"])]
# The shoulder line is 0.245 wide including the deltoid, so the ribcage tops out at 0.184 and the deltoid
# supplies the rest. Tapering the last ring to a point made a slope-shouldered figure with its arms hanging
# from somewhere below its shoulders.
# The collar ends at 0.818, below the jaw at 0.854, so the neck is visible in profile. Pushed up to 0.852 it
# swallowed the neck entirely and the side view was a head resting on a trunk.
LOFT_CHEST = [(0.720 * h, P["chest_x"], P["chest_y"]), (0.760 * h, 0.0870 * h, 0.0610 * h),
              (0.795 * h, 0.0900 * h, 0.0560 * h), (0.808 * h, 0.0700 * h, 0.0460 * h),
              (0.818 * h, 0.0480 * h, 0.0380 * h)]
loft(LOFT_HIPS, MAT_KIT, "hips_loft", "hips")
loft(LOFT_SPINE, MAT_KIT, "spine_loft", "spine")
loft(LOFT_CHEST, MAT_KIT, "chest_loft", "chest")

# The waist down. A skirt, because the reference figure wears one and because the hip width I measured is a
# skirt's width — the alternative was to build a hip to match a skirt measurement, which is how a model stops
# describing a body. Shorts instead for a member dressed in shorts; either way it is the same parameter the
# user's appearance description fills in.
if LOWER == "skirt":
    # Elliptical, because a skirt hangs from hips that are wider than they are deep: measured, 0.209 wide
    # against 0.136 deep at 0.50 h. A circular cone made a bell that was 50 % too deep in profile.
    loft([(0.435 * h, 0.1180 * h, 0.0760 * h), (0.470 * h, 0.1130 * h, 0.0730 * h),
          (0.500 * h, 0.1045 * h, 0.0680 * h), (0.530 * h, 0.0930 * h, 0.0625 * h),
          (0.552 * h, 0.0900 * h, 0.0620 * h)], MAT_KIT, "skirt", "hips", caps=False)
elif LOWER == "shorts":
    for side, sx in (("L", 1), ("R", -1)):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.0600 * h, radius2=0.0660 * h,
                                        depth=0.0850 * h, location=(sx * 0.050 * h, 0, 0.5075 * h),
                                        end_fill_type="NGON")
        add(bpy.context.object, MAT_KIT, f"shorts.{side}", f"thigh.{side}")

for side, sx in (("L", 1), ("R", -1)):
    sh = (sx * P["shoulder_x"], 0, P["shoulder_z"])
    el = (sx * (P["shoulder_x"] + 0.004 * h), 0.005 * h, P["elbow_z"])
    wr = (sx * (P["shoulder_x"] - 0.001 * h), 0.020 * h, P["wrist_z"])
    # a deltoid, because an arm that begins as a cylinder where the shoulder is reads as a broom handle
    # bare skin, because the top is sleeveless: a kit-coloured deltoid read as an epaulette
    sphere((sx * (P["shoulder_x"] + 0.001 * h), 0, P["shoulder_z"] - 0.006 * h),
           (P["deltoid_r"] * girth,) * 3, MAT_SKIN, f"deltoid.{side}", f"upperarm.{side}")
    cone(sh, el, P["arm_r0"] * girth, P["arm_r1"] * girth, MAT_SKIN, f"upperarm.{side}", f"upperarm.{side}")
    sphere(el, (P["arm_r1"] * girth * 1.06,) * 3, MAT_SKIN, f"elbow.{side}", f"forearm.{side}", 14, 8)
    cone(el, wr, P["fore_r0"] * girth, P["fore_r1"] * girth, MAT_SKIN, f"forearm.{side}", f"forearm.{side}")
    sphere(wr, (P["fore_r1"] * girth * 1.25, P["fore_r1"] * girth * 1.0, P["fore_r1"] * girth * 1.6),
           MAT_SKIN, f"hand.{side}", f"hand.{side}")

    hp = (sx * P["hip_x"], 0, P["pelvis_z"])
    mid = (sx * (P["hip_x"] + P["knee_x"]) / 2, 0, 0.390 * h)
    kn = (sx * P["knee_x"], 0, P["knee_z"])
    ca = (sx * P["knee_x"], 0, P["calf_z"])
    an = (sx * P["ankle_x"], 0, 0.045 * h)
    cone(hp, mid, P["thigh_r0"] * girth, P["thigh_r1"] * girth, MAT_SKIN, f"thigh_hi.{side}", f"thigh.{side}")
    cone(mid, kn, P["thigh_r1"] * girth, P["thigh_r2"] * girth, MAT_SKIN, f"thigh_lo.{side}", f"thigh.{side}")
    sphere(kn, (P["thigh_r2"] * girth,) * 3, MAT_SKIN, f"knee.{side}", f"shin.{side}", 16, 10)
    cone(kn, an, P["shin_r0"] * girth, P["ankle_r"] * girth, MAT_SKIN, f"shin.{side}", f"shin.{side}")
    sphere(ca, (P["calf_r"] * girth, P["calf_r"] * girth * 1.10, 0.040 * h), MAT_SKIN,
           f"calf.{side}", f"shin.{side}")
    sphere(an, (P["ankle_r"] * girth * 1.1,) * 3, MAT_SKIN, f"ankle.{side}", f"foot.{side}", 14, 8)
    # A foot has a long flat sole and a short high heel, so it is two boxes, and it points forward: the figure
    # faces -Y. The first build put the toes behind the ankles, which no front view could show.
    box((an[0], -0.038 * h, 0.011 * h), (P["foot_w"], P["foot_len"], 0.022 * h), MAT_KIT,
        f"sole.{side}", f"foot.{side}", rot=(0, 0, math.radians(-6 * sx)))
    box((an[0], -0.008 * h, 0.034 * h), (P["foot_w"] * 0.94, 0.078 * h, 0.028 * h), MAT_KIT,
        f"shoe.{side}", f"foot.{side}", rot=(0, 0, math.radians(-6 * sx)))

# ---- the racquet, in the right hand ----------------------------------------------------------------
if RACQUET:
    hand = Vector((-P["shoulder_x"] + 0.001 * h, 0.020 * h, P["wrist_z"]))
    up = Vector((0, 0.10, 1)).normalized()
    grip_len, shaft = 0.13 * h, 0.12 * h
    grip_end = hand + up * grip_len
    frame_c = grip_end + up * (shaft + 0.008 * h)
    cone(hand, grip_end, 0.011 * h, 0.011 * h, MAT_GRIP, "grip", "hand.R")
    cone(grip_end, frame_c, 0.009 * h, 0.009 * h, MAT_FRAME, "shaft", "hand.R")
    bpy.ops.mesh.primitive_torus_add(location=frame_c, major_radius=0.115 * h, minor_radius=0.013 * h,
                                     major_segments=32, minor_segments=8,
                                     rotation=(math.radians(90), 0, 0))
    o = bpy.context.object
    o.scale = (1.0, 0.80, 1.0)             # an oval head, taller than it is wide, in the plane of the swing
    add(o, MAT_FRAME, "racquet_head", "hand.R")

# ---- one mesh, then a skeleton ---------------------------------------------------------------------
# ---- rigid binding, one part to one bone -----------------------------------------------------------
# Automatic weights on a body made of loose primitives put the hair on the chest and the racquet on the
# hips: the render showed a head that came apart from its own hair. A ball-jointed mannequin should be
# rigidly bound anyway — each piece belongs to exactly one bone, weight 1.0, and nothing smears.
for obj, bone_name in PARTS:
    vg = obj.vertex_groups.new(name=bone_name)
    vg.add(range(len(obj.data.vertices)), 1.0, "REPLACE")

bpy.ops.object.select_all(action="DESELECT")
for obj, _ in PARTS:
    obj.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0][0]
bpy.ops.object.join()
body = bpy.context.object
body.name = NAME
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.object.shade_flat()

bpy.ops.object.armature_add(location=(0, 0, 0))
arm = bpy.context.object
arm.name = NAME + "_rig"
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
eb.remove(eb[0])


def bone(name, head, tail, parent=None, connect=False):
    b = eb.new(name)
    b.head, b.tail = Vector(head), Vector(tail)
    if parent:
        b.parent = eb[parent]
        b.use_connect = connect
    return b


hip_y, waist_y, chest_y, shoulder_y = P["pelvis_z"], P["waist_z"], P["chest_z"], P["shoulder_z"]
bone("hips", (0, 0, hip_y), (0, 0, waist_y))
bone("spine", (0, 0, waist_y), (0, 0, chest_y), "hips")
bone("chest", (0, 0, chest_y), (0, 0, shoulder_y), "spine")
bone("neck", (0, 0, shoulder_y), (0, 0, P["neck_top"]), "chest")
bone("head", (0, 0, P["neck_top"]), (0, 0, P["head_c"] + P["head_rz"]), "neck")
for side, sx in (("L", 1), ("R", -1)):
    bone(f"shoulder.{side}", (0, 0, shoulder_y - 0.02 * h), (sx * P["shoulder_x"], 0, shoulder_y), "chest")
    bone(f"upperarm.{side}", (sx * P["shoulder_x"], 0, shoulder_y),
         (sx * (P["shoulder_x"] + 0.004 * h), 0.005 * h, P["elbow_z"]), f"shoulder.{side}")
    bone(f"forearm.{side}", (sx * (P["shoulder_x"] + 0.004 * h), 0.005 * h, P["elbow_z"]),
         (sx * (P["shoulder_x"] - 0.001 * h), 0.020 * h, P["wrist_z"]), f"upperarm.{side}")
    bone(f"hand.{side}", (sx * (P["shoulder_x"] - 0.001 * h), 0.020 * h, P["wrist_z"]),
         (sx * (P["shoulder_x"] - 0.001 * h), 0.085 * h, P["wrist_z"] - 0.018 * h), f"forearm.{side}")
    bone(f"thigh.{side}", (sx * P["hip_x"], 0, hip_y), (sx * P["knee_x"], 0, P["knee_z"]), "hips")
    bone(f"shin.{side}", (sx * P["knee_x"], 0, P["knee_z"]), (sx * P["ankle_x"], 0, 0.045 * h),
         f"thigh.{side}")
    bone(f"foot.{side}", (sx * P["ankle_x"], 0, 0.045 * h), (sx * P["ankle_x"], -0.11 * h, 0.018 * h),
         f"shin.{side}")
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE")

# ---- a ready stance, because a T-pose says nothing about tennis ---------------------------------
bpy.ops.object.mode_set(mode="POSE")
pb = arm.pose.bones


def turn(name, x=0, y=0, z=0):
    if name in pb:
        pb[name].rotation_mode = "XYZ"
        pb[name].rotation_euler = (math.radians(x), math.radians(y), math.radians(z))


if POSE != "rest":
    turn("hips", x=6)
    turn("spine", x=-4)
    turn("thigh.L", x=-14, z=-7)
    turn("thigh.R", x=-10, z=7)
    turn("shin.L", x=26)
    turn("shin.R", x=20)
    turn("shoulder.L", z=-6)
    turn("spine", z=6)
    turn("upperarm.L", x=-6, z=-9)
    turn("forearm.L", x=-12)
    turn("upperarm.R", x=-14, z=8)
    turn("forearm.R", x=-72)   # elbow up, so the racquet is in front of the body and not behind it
bpy.ops.object.mode_set(mode="OBJECT")

# ---- save, export, and a picture to look at -----------------------------------------------------
os.makedirs(OUT, exist_ok=True)
blend = os.path.join(OUT, f"{NAME}.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
glb = os.path.join(OUT, f"{NAME}.glb")
if RENDER != "measure":           # a measuring build must not overwrite the body the game loads
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    arm.select_set(True)
    bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True,
                              export_apply=False, export_animations=False)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
# In measure mode the shading is flat, because a measurement of a silhouette must not depend on a light. The
# first attempt to measure this body lost 40 % of the trunk: studio shading darkened the torso's edges until
# they were the same grey as the backdrop, and the instrument honestly reported a narrow body.
if RENDER == "measure":
    scene.display.shading.light = "FLAT"
    scene.display.shading.show_shadows = False
    scene.display.shading.show_cavity = False
    scene.world.color = (0.80, 0.80, 0.80)
else:
    scene.display.shading.light = "STUDIO"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
scene.render.resolution_x, scene.render.resolution_y = (900, 1300) if RENDER == "hero" else (760, 1150)
scene.render.film_transparent = False

bpy.ops.object.empty_add(location=(0, 0, 0.53 * h))
aim = bpy.context.object
if RENDER == "measure":
    # Orthographic and square on, because a measurement taken through a perspective is a measurement of the
    # camera as much as of the body.
    bpy.ops.object.camera_add(location=(6.0 * h if VIEW == "side" else 0, 0 if VIEW == "side" else -6.0 * h,
                                        0.53 * h))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 1.12 * h
else:
    bpy.ops.object.camera_add(location=(2.0, -3.9, 1.05))
    cam = bpy.context.object
    cam.data.lens = 55
c = cam.constraints.new("TRACK_TO")
c.target = aim
c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam

if RENDER != "measure":
    # a floor, so the figure is standing on something rather than floating over a void. Not in measure mode:
    # a floor is a cast shadow, and a cast shadow was half of what made the first measurements nonsense.
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0))
    floor = bpy.context.object
    floor.data.materials.append(material("floor", "2a2f35", 0.9))

scene.render.filepath = os.path.join(OUT, f"{NAME}.png" if RENDER == "hero" else f"{NAME}-measure-{VIEW}.png")
bpy.ops.render.render(write_still=True)
print(f"BUILT {NAME}: height {HEIGHT} build {BUILD} pose {POSE} -> {glb}")
