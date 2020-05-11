import keras
from TDNN_layer import TDNN
from keras.layers import Dense, Lambda, Concatenate, BatchNormalization
from keras import losses
import keras.backend as K

import tensorflow as tf

def get_multichannel_tdnn_model(feat_size, num_classes, num_channels, hidden_layer_config, get_embedding = False):
    inputs = keras.Input(shape=(num_channels, None, feat_size))
    def split_channels(x):
        channel_data = tf.split(x, num_channels, axis=1)
        for i in range(len(channel_data)):
            channel_data[i] = tf.squeeze(channel_data[i], [1, ])
        return channel_data

    tdnn_layer1 = TDNN(int(hidden_layer_config[0]), (0,), padding='same', activation="sigmoid", name="TDNN1")
    tdnn_layer2 = TDNN(int(hidden_layer_config[1]), input_context=(0,), padding='same', activation="sigmoid", name="TDNN2")
    average = Lambda(lambda xin: K.mean(xin, axis=1), output_shape=(int(hidden_layer_config[1]),))
    variance = Lambda(lambda xin: K.std(xin, axis=1), output_shape=(int(hidden_layer_config[1]),))

    splitted_channels = Lambda(split_channels)(inputs)

    means = []
    vars = []
    for channel in splitted_channels:
        t1 = tdnn_layer1(channel)
        t2 = tdnn_layer2(t1)
        means.append(average(t2))
        vars.append(variance(t2))

    mv = Concatenate()(means)
    vv = Concatenate()(vars)
    k1 = Concatenate()([mv, vv])
    d1 = Dense(int(hidden_layer_config[2]), activation='sigmoid', name='x_vector')(mv)
    #d2 = Dense(int(hidden_layer_config[3]), activation='sigmoid', name='x_vector_2')(d1)
    output = Dense(num_classes, activation='softmax', name='dense_2')(d1)
    if get_embedding:
        model = keras.Model(inputs=inputs, outputs=d1)
    else:
        model = keras.Model(inputs=inputs, outputs=output)
    return model