import numpy as np
import pyrender
import trimesh

# render with gl camera
def render_glcam(model_in, # model name or trimesh
                 K = None,
                 Rt = None,
                 scale=1.0,
                 rend_size=(512, 512),
                 flat_shading=False):
    
    # Mesh creation
    if isinstance(model_in, str) is True:
        mesh = trimesh.load(model_in, process=False)
    else:
        mesh = model_in.copy()
    pr_mesh = pyrender.Mesh.from_trimesh(mesh)

    # Scene creation
    scene = pyrender.Scene()

    # Adding objects to the scene
    face_node = scene.add(pr_mesh)

    # Caculate fx fy cx cy from K
    fx, fy = K[0][0] * scale, K[1][1] * scale
    cx, cy = K[0][2] * scale, K[1][2] * scale

    # Camera Creation
    cam = pyrender.IntrinsicsCamera(fx, fy, cx, cy, 
                                    znear=0.1, zfar=100000)
    cam_pose = np.eye(4)
    cam_pose[:3, :3] = Rt[:3, :3].T
    cam_pose[:3, 3] = -Rt[:3, :3].T.dot(Rt[:, 3])
    scene.add(cam, pose=cam_pose)

    # Set up the light
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=10.0)
    light_pose = cam_pose.copy()
    light_pose[0:3, :] += np.array([[0], [100], [0]])
    scene.add(light, pose=light_pose)

    # Rendering offscreen from that camera
    r = pyrender.OffscreenRenderer(viewport_width=rend_size[1],
                                   viewport_height=rend_size[0],
                                   point_size=1.0)
    if flat_shading is True:
        color, depth = r.render(scene, flags=pyrender.constants.RenderFlags.FLAT)
    else:
        color, depth = r.render(scene)

    # rgb to bgr for cv2
    color = color[:, :, [2, 1, 0]]

    return depth, color


# render with cv camera
def render_cvcam(model_in, # model name or trimesh
                 K = None,
                 Rt = None,
                 scale=1.0,
                 rend_size=(512, 512),
                 flat_shading=False):
    
    if np.array(K).all() == None:
        K = np.array([[2000, 0, 256],
                      [0, 2000, 256],
                      [0, 0, 1]], dtype=np.float64)
    if np.array(Rt).all() == None:
        Rt = np.array([[1, 0, 0, 0],
                       [0, -1, 0, 0],
                       [0, 0, -1, 1200]], dtype=np.float64)
        
    # define R to transform from cvcam to glcam
    R_cv2gl = np.array([[1, 0, 0],
                        [0, -1, 0],
                        [0, 0, -1]])
    Rt_cv = R_cv2gl.dot(Rt)
    
    return render_glcam(model_in, K, Rt_cv, scale, rend_size, flat_shading)

