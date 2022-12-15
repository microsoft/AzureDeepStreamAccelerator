from .base_custom_parser import BaseCustomParser
from .pose import pose_decode, pose_plot, get_bboxes_and_lines
import pyds

class BodyPoseParser2D(BaseCustomParser):
    def __init__(self) -> None:
        super().__init__(model_type=BaseCustomParser.CUSTOM_MODEL, name="bodypose2d")

    def parse_custom_model(config, raw_outputs: dict):
        try:
            heatmaps = raw_outputs["heatmap_out/BiasAdd:0"]
            pafs =  raw_outputs["conv2d_transpose_1/BiasAdd:0"]
        except:
            print("BodyPose2DParser. Error: some layers missing in output tensors")
            return None, None

        person_to_joint_assoc, joint_list = pose_decode(heatmaps, pafs, 
                                                        refine_center=True, 
                                                        gaussian_filt=True)
        dets =  get_bboxes_and_lines(joint_list=joint_list, person_to_joint_assoc=person_to_joint_assoc, outsize=config.image_size)                                                               
        return dets, None

    def add_custom_to_meta(config, outputs, batch_meta, frame_meta):

        UNTRACKED_OBJECT_ID = 0xffffffffffffffff
        all_lines = []
        # Add bboxes 
        for d in outputs:
            box, lines = d
            all_lines+=lines

            obj_meta = pyds.nvds_acquire_obj_meta_from_pool(batch_meta)
            # Set bbox properties. These are in input resolution.
            rect_params = obj_meta.rect_params
            rect_params.left   = box[0]
            rect_params.top    = box[1]
            rect_params.width  = box[2]
            rect_params.height = box[3]

            # Set object info including class, detection confidence, etc.
            obj_meta.confidence = 1.0
            obj_meta.class_id = 1
   
            # There is no tracking ID upon detection. The tracker will assign an ID.
            obj_meta.object_id = UNTRACKED_OBJECT_ID
            obj_meta.obj_label = "person"


            ### Customize how show the bbox    #
            # Semi-transparent yellow backgroud
            rect_params.has_bg_color = 0
            rect_params.bg_color.set(1, 1, 0, 0.4)
    
            # Red border of width 3
            rect_params.border_width = 3
            rect_params.border_color.set(1, 0, 0, 1)
    
            # Set display text for the object.
            txt_params = obj_meta.text_params
            if txt_params.display_text:
                pyds.free_buffer(txt_params.display_text)
    
            txt_params.x_offset = int(rect_params.left)
            txt_params.y_offset = max(0, int(rect_params.top) - 10)
            txt_params.display_text = obj_meta.obj_label 

            # Font , font-color and font-size
            txt_params.font_params.font_name = "Serif"
            txt_params.font_params.font_size = 10
            # set(red, green, blue, alpha); set to White
            txt_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

            # Text background color
            txt_params.set_bg_clr = 1
            # set(red, green, blue, alpha); set to Black
            txt_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
    
            ### Finally, add metadata of the detected object 
            pyds.nvds_add_obj_meta_to_frame(frame_meta, obj_meta, None)            

        # draw lines 
        ND = len(all_lines)//16
        lineIndex=0
        for i in range(ND):
            display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            for j in range(16):
                pt1, pt2 = all_lines[lineIndex]
                lineIndex += 1
                lp = display_meta.line_params[j]
                lp.x1, lp.y1 = pt1
                lp.x2, lp.y2 = pt2
                lp.line_width = 4
                lp.line_color.set(0.0,0.0,0.0,1.0)
            display_meta.num_lines=16                
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        n = len(all_lines)-16*ND
        if n>0:            
            display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            for j in range(n):
                pt1, pt2 = all_lines[lineIndex]
                lineIndex += 1
                lp = display_meta.line_params[j]
                lp.x1, lp.y1 = pt1
                lp.x2, lp.y2 = pt2
                lp.line_width = 4
                lp.line_color.set(0.0,0.0,0.0,1.0)
            display_meta.num_lines=n                
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

if '__main__' == __name__:
    pass
