import tensorflow as tf


# TODO: make baseclass
# TODO: use maxpool as 2nd layer

class ConvInput(tf.layers.Layer):
    def __init__(self, filters, kernel_initializer, kernel_regularizer, name='conv_input'):
        super().__init__(name=name)

        self._filters = filters
        self._kernel_initializer = kernel_initializer
        self._kernel_regularizer = kernel_regularizer

    def build(self, input_shape):
        self._conv = tf.layers.Conv2D(
            self._filters,
            7,
            strides=2,
            padding='same',
            use_bias=False,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer)
        self._bn = tf.layers.BatchNormalization(fused=True)

        super().build(input_shape)

    def call(self, input, training):
        input = self._conv(input)
        input = self._bn(input, training=training)
        input = tf.nn.relu(input)

        return input


class Bottleneck(tf.layers.Layer):
    def __init__(self, filters, kernel_initiializer, kernel_regularizer, name='bottleneck'):
        super().__init__(name=name)

        self._filters = filters
        self._kernel_initializer = kernel_initiializer
        self._kernel_regularizer = kernel_regularizer

    def build(self, input_shape):
        self._conv_1 = tf.layers.Conv2D(
            self._filters // 4,
            1,
            use_bias=False,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer)
        self._bn_1 = tf.layers.BatchNormalization(fused=True)

        self._conv_2 = tf.layers.Conv2D(
            self._filters // 4,
            3,
            padding='same',
            use_bias=False,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer)
        self._bn_2 = tf.layers.BatchNormalization(fused=True)

        self._conv_3 = tf.layers.Conv2D(
            self._filters,
            1,
            use_bias=False,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer)
        self._bn_3 = tf.layers.BatchNormalization(fused=True)

        super().build(input_shape)

    def call(self, input, training):
        identity = input

        input = self._conv_1(input)
        input = self._bn_1(input, training=training)
        input = tf.nn.relu(input)

        input = self._conv_2(input)
        input = self._bn_2(input, training=training)
        input = tf.nn.relu(input)

        input = self._conv_3(input)
        input = self._bn_3(input, training=training)
        input = input + identity
        input = tf.nn.relu(input)

        return input


class BottleneckDown(tf.layers.Layer):
    def __init__(self, filters, kernel_initiializer, kernel_regularizer, name='bottleneck_down'):
        super().__init__(name=name)

        self._filters = filters
        self._kernel_initializer = kernel_initiializer
        self._kernel_regularizer = kernel_regularizer

    def build(self, input_shape):
        self._conv_identity = tf.layers.Conv2D(
            self._filters,
            3,
            strides=2,
            padding='same',
            use_bias=False,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer)
        self._bn_identity = tf.layers.BatchNormalization(fused=True)

        self._conv_1 = tf.layers.Conv2D(
            self._filters // 4,
            1,
            use_bias=False,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer)
        self._bn_1 = tf.layers.BatchNormalization(fused=True)

        self._conv_2 = tf.layers.Conv2D(
            self._filters // 4,
            3,
            strides=2,
            padding='same',
            use_bias=False,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer)
        self._bn_2 = tf.layers.BatchNormalization(fused=True)

        self._conv_3 = tf.layers.Conv2D(
            self._filters,
            1,
            use_bias=False,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer)
        self._bn_3 = tf.layers.BatchNormalization(fused=True)

        super().build(input_shape)

    def call(self, input, training):
        identity = input
        identity = self._conv_identity(identity)
        identity = self._bn_identity(identity, training=training)

        input = self._conv_1(input)
        input = self._bn_1(input, training=training)
        input = tf.nn.relu(input)

        input = self._conv_2(input)
        input = self._bn_2(input, training=training)
        input = tf.nn.relu(input)

        input = self._conv_3(input)
        input = self._bn_3(input, training=training)
        input = input + identity
        input = tf.nn.relu(input)

        return input


class ResBlock(tf.layers.Layer):
    def __init__(self, filters, depth, kernel_initializer, kernel_regularizer, name='res_block'):
        super().__init__(name=name)

        assert filters % 4 == 0
        assert filters // 4 >= 64

        self._filters = filters
        self._depth = depth
        self._kernel_initializer = kernel_initializer
        self._kernel_regularizer = kernel_regularizer

    def build(self, input_shape):
        bottlenecks = []

        for i in range(self._depth):
            if i == 0:
                bottlenecks.append(BottleneckDown(
                    self._filters, kernel_initiializer=self._kernel_initializer,
                    kernel_regularizer=self._kernel_regularizer))
            else:
                bottlenecks.append(Bottleneck(
                    self._filters, kernel_initiializer=self._kernel_initializer,
                    kernel_regularizer=self._kernel_regularizer))

        self._bottlenecks = bottlenecks

        super().build(input_shape)

    def call(self, input, training):
        for f in self._bottlenecks:
            input = f(input, training=training)

        return input


class ResNet(tf.layers.Layer):
    def __init__(self, kernel_initializer, kernel_regularizer, name='resnet'):
        super().__init__(name=name)

        self._kernel_initializer = kernel_initializer
        self._kernel_regularizer = kernel_regularizer

    def call(self, input, training):
        input = self._conv_input(input, training=training)
        C1 = input
        input = self._res_block_1(input, training=training)
        C2 = input
        input = self._res_block_2(input, training=training)
        C3 = input
        input = self._res_block_3(input, training=training)
        C4 = input
        input = self._res_block_4(input, training=training)
        C5 = input

        return {'C1': C1, 'C2': C2, 'C3': C3, 'C4': C4, 'C5': C5}


class ResNet_50(ResNet):
    def __init__(self, kernel_initializer=None, kernel_regularizer=None, name='resnet_50'):
        if kernel_initializer is None:
            kernel_initializer = tf.contrib.layers.variance_scaling_initializer(
                factor=2.0, mode='FAN_IN', uniform=False)

        if kernel_regularizer is None:
            kernel_regularizer = tf.contrib.layers.l2_regularizer(scale=1e-4)

        super().__init__(kernel_initializer=kernel_initializer, kernel_regularizer=kernel_regularizer, name=name)

    def build(self, input_shape):
        self._conv_input = ConvInput(
            64, kernel_initializer=self._kernel_initializer, kernel_regularizer=self._kernel_regularizer)
        self._res_block_1 = ResBlock(
            256, depth=3, kernel_initializer=self._kernel_initializer, kernel_regularizer=self._kernel_regularizer)
        self._res_block_2 = ResBlock(
            512, depth=4, kernel_initializer=self._kernel_initializer, kernel_regularizer=self._kernel_regularizer)
        self._res_block_3 = ResBlock(
            1024, depth=6, kernel_initializer=self._kernel_initializer, kernel_regularizer=self._kernel_regularizer)
        self._res_block_4 = ResBlock(
            2048, depth=3, kernel_initializer=self._kernel_initializer, kernel_regularizer=self._kernel_regularizer)

        super().build(input_shape)


def main():
    image = tf.zeros((8, 224, 224, 3))

    net = ResNet_50()
    output = net(image, training=True)

    for k in output:
        shape = output[k].shape
        assert shape[1] == shape[2] == 224 // 2**int(k[1:]), 'invalid shape {} for layer {}'.format(shape, k)
        print(output[k])


if __name__ == '__main__':
    main()
