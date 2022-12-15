# Doesn't run out of the box in [DeepStream 6.0.1](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Overview.html)
# See the comments below for fixing

import onnx
from onnx.helper import make_tensor, make_node, make_tensor_value_info, printable_graph



if '__main__' == __name__:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('input', nargs='?', default='onnx_model_repo/tiny-yolov3/1/model0.onnx')
    p.add_argument('output', nargs='?', default='onnx_model_repo/tiny-yolov3/1/model0.onnx')
    args = p.parse_args()

    model0 = onnx.load(args.input)

    #The model requires two inputs `input_1`(image data) and `image_shape` ((416, 416) for the model), while DeepStream 6.0.1 only supports image data without a [custom plugin](https://docs.nvidia.com/metropolis/deepstream/4.0/dev-guide/DeepStream_Development_Guide/baggage/nvdsinfer__custom__impl_8h.html). 
    # Pop `image_shape` from the input and replace it by an initializer of the same name

    image_shape_old = model0.graph.input.pop(1)
    image_shape = make_tensor('image_shape', data_type=1, dims = (1,2), vals=(416,416))
    model0.graph.initializer.append(image_shape)

    # This model also expects the image data in NCHW formats. Pop `input_1` and created a new one `input_0` with NHWC
    input_1 = model0.graph.input.pop(0)
    input_0 = make_tensor_value_info('input_0', elem_type=1, shape=('unk__3000', 416, 416, 3))
    model0.graph.input.append(input_0)

    # Add a layer to convert from NHWC to NCHW
    Transpose0 = make_node(op_type='Transpose', inputs=([input_0.name]), outputs=([input_1.name]), name='Transpose0', perm=(0,3,1,2))
    model0.graph.node.insert(0, Transpose0)

    # nvinfer crashes in [NonMaxSuppression](https://github.com/onnx/onnx/blob/main/docs/Operators.md#NonMaxSuppression).  Skip it and implement in python
    output_2 = model0.graph.output.pop(2)
    onnx.save(model0, 'onnx_model_repo/tiny-yolov3/1/model.onnx')
