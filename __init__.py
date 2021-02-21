import bpy
import bpy_extras

bl_info = {
    "name": "PartiCam",
    "description": "Constrains particle generation to camera view bounds",
    "author": "Frank Louw",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "location": "View3D>Object",
    "warning": "This addon is still in development.",
    "wiki_url": "",
    "category": "Object",
}


def main(context, margin, max_dist_ratio, min_dist_ratio, is_gradient):
    scene = bpy.context.scene
    max_dist = 0
    min_dist = 0
    for obj in bpy.context.selected_objects:
        if obj.type == "MESH" and len(obj.particle_systems) > 0:
            cameras = [ob for ob in bpy.context.selected_objects if ob.type == "CAMERA"]
            cam_group_name = "_".join([cam.name for cam in cameras])

            cam_vert_group = None

            for vert_group in obj.vertex_groups:
                if vert_group.name == cam_group_name:
                    cam_vert_group = vert_group
            if cam_vert_group is None:
                cam_vert_group = obj.vertex_groups.new(name=cam_group_name)

            for vert in obj.data.vertices:
                cam_vert_group.add([vert.index], 0.0, "REPLACE")
                for camera in cameras:
                    cam_ndc = bpy_extras.object_utils.world_to_camera_view(
                        scene, camera, obj.matrix_world @ vert.co
                    )
                    if cam_ndc[2] > max_dist:
                        max_dist = cam_ndc[2]
                    elif cam_ndc[2] < min_dist:
                        min_dist = cam_ndc[2]

    for obj in bpy.context.selected_objects:

        if obj.type == "MESH" and len(obj.particle_systems) > 0:
            cameras = [ob for ob in bpy.context.selected_objects if ob.type == "CAMERA"]
            cam_group_name = "_".join([cam.name for cam in cameras])

            cam_vert_group = None

            for vert_group in obj.vertex_groups:
                if vert_group.name == cam_group_name:
                    cam_vert_group = vert_group
            if cam_vert_group is None:
                cam_vert_group = obj.vertex_groups.new(name=cam_group_name)

            for vert in obj.data.vertices:
                for camera in cameras:
                    cam_ndc = bpy_extras.object_utils.world_to_camera_view(
                        scene, camera, obj.matrix_world @ vert.co
                    )
                    if (
                        cam_ndc[0] > 0 - margin / 100
                        and cam_ndc[0] < 1 + margin / 100
                        and cam_ndc[1] > 0 - margin / 100
                        and cam_ndc[1] < 1 + margin / 100
                        and cam_ndc[2] > max_dist * min_dist_ratio
                        and cam_ndc[2] < max_dist * max_dist_ratio
                    ):
                        if is_gradient:
                            cam_vert_group.add(
                                [vert.index],
                                1
                                - (
                                    (cam_ndc[2] - (max_dist * min_dist_ratio))
                                    / (max_dist * max_dist_ratio)
                                ),
                                "ADD",
                            )
                        else:
                            cam_vert_group.add([vert.index], 1.0, "ADD")

            for particle_sys in obj.particle_systems:
                particle_sys.vertex_group_density = cam_group_name


class OBJECT_OT_PartiCam(bpy.types.Operator):
    """PartiCam"""

    bl_idname = "object.parti_cam"
    bl_label = "PartiCam"
    bl_options = {"REGISTER", "UNDO"}

    margin: bpy.props.IntProperty(
        name="Margin",
        description="Adds padding around camera area.",
        default=10,
        soft_min=0,
        soft_max=100,
    )
    max_dist_ratio: bpy.props.FloatProperty(
        name="Maximum Distance",
        description="Maximum distance that particles will added",
        default=1,
        subtype="FACTOR",
        min=0,
        soft_max=1,
    )
    min_dist_ratio: bpy.props.FloatProperty(
        name="Minimum Distance",
        description="Minimum distance that particles will added",
        default=0,
        subtype="FACTOR",
        min=0,
        max=1,
    )
    is_gradient: bpy.props.BoolProperty(
        name="Gradient",
        description="Enables gradient weighting",
    )

    def execute(self, context):
        main(
            context,
            self.margin,
            self.max_dist_ratio,
            self.min_dist_ratio,
            self.is_gradient,
        )
        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_PartiCam.bl_idname)


def register():
    bpy.utils.register_class(OBJECT_OT_PartiCam)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_PartiCam)