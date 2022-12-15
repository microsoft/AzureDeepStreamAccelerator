from tao_pipeline import TAOPipeline, layer2array

from pose import pose_decode, pose_plot
import pyds

class BodyPose2D_Parser(TAOPipeline):
    def parser(self, layers_info):
        heatmaps = layer2array(layers_info[0])
        pafs = layer2array(layers_info[1])
        if (heatmaps is None) or (pafs is None):
            return []
        else:
            person_to_joint_assoc, joint_list = pose_decode(heatmaps, pafs)
            #print('person_to_joint_assoc', person_to_joint_assoc)
            return person_to_joint_assoc, joint_list

    def add_meta_to_frame(self, frame_meta, outputs):
        frame_number = frame_meta.frame_num
        if 2 > len(outputs) :
            print('frame', frame_number, 'is empty')
        else:
            person_to_joint_assoc, joint_list = outputs
            display_meta=pyds.nvds_acquire_display_meta_from_pool(self.batch_meta)
            pose_plot(display_meta, joint_list, person_to_joint_assoc,
                      outsize=(self.image_width, self.image_height))
            print(f'display_meta.num_lines[{frame_number}]', display_meta.num_lines)
            #print('display_meta.num_lines', display_meta.num_lines)
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

if '__main__' == __name__:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--input', nargs='?', default='sample_720p-4.h264')
    p.add_argument('--output', nargs='?', default='bodypose2d_out.mp4')
    p.add_argument('--config', default='bodypose2d_pgie_config.txt')
    args = p.parse_args()

    pipeline = BodyPose2D_Parser(config=args.config)

    pipeline.run(args.input, args.output)
