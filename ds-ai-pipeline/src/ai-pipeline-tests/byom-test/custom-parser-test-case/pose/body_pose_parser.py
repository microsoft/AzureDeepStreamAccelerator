import pyds
from pose import pose_decode, pose_plot


model_type   = 1  
name         = "BodyPoseCustomParser"

def parse_custom_model(config, raw_outputs: dict):
    try:
        heatmaps = raw_outputs["heatmap_out/BiasAdd:0"]
        pafs =  raw_outputs["conv2d_transpose_1/BiasAdd:0"]
    except:
        print("BodyPoseCustomParser. Error: some layers missing in output tensors")
        return None, None

    person_to_joint_assoc, joint_list = pose_decode(heatmaps, pafs)
    return (person_to_joint_assoc, joint_list), None

def add_custom_to_meta(config, data, batch_meta, frame_meta):
    person_to_joint_assoc, joint_list = data
    display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
    pose_plot(display_meta, joint_list, person_to_joint_assoc, outsize=config.image_size)
    pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)    