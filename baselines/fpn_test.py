from baselines.resnet import ResNet_50
from baselines.fpn import FeaturePyramidNetwork
import tensorflow as tf
import pytest


@pytest.mark.skip
def test_output_shape():
    image = tf.zeros((8, 224, 224, 3))

    net = ResNet_50()
    fpn = FeaturePyramidNetwork()
    output = net(image, training=True)
    output = fpn(output, training=True)

    for k in output:
        shape = output[k].shape
        assert shape[1] == shape[2] == 224 // 2**int(k[1:]), 'invalid shape {} for layer {}'.format(shape, k)
