import keras
from TDNN_layer import TDNN
from keras.layers import Dense, Lambda, Concatenate, BatchNormalization, Multiply, Add, Dropout, LSTM
from keras.activations import sigmoid
from keras import losses
import keras.backend as K

import tensorflow as tf

def get_multichannel_tdnn_model_new(feat_size, num_classes, num_channels, hidden_layer_config, get_embedding = False):
    inputs = keras.Input(shape=(num_channels, None, feat_size))
    def split_channels(x):
        channel_data = tf.split(x, num_channels, axis=1)
        for i in range(len(channel_data)):
            channel_data[i] = tf.squeeze(channel_data[i], [1, ])
        return channel_data
    def split_for_sum_pool(combined_vect):
        return  tf.split(combined_vect,num_or_size_splits=4, axis=1)

    tdnn_layer1 = TDNN(int(hidden_layer_config[0]), (-2,0,2), padding='same', activation="sigmoid", name="TDNN1")
    tdnn_layer2 = TDNN(int(hidden_layer_config[1]), input_context=(-2,0,2), padding='same', activation="sigmoid", name="TDNN2")
    average = Lambda(lambda xin: K.mean(xin, axis=1), output_shape=(int(hidden_layer_config[1]),))
    variance = Lambda(lambda xin: K.std(xin, axis=1), output_shape=(int(hidden_layer_config[1]),))

    splitted_channels = Lambda(split_channels)(inputs)

    means = []
    vars = []
    for ch_id,channel in enumerate(splitted_channels):
        t1 = tdnn_layer1(channel)
        t2 = tdnn_layer2(t1)
        mean = average(t2)
        mean_transformed = Dense(hidden_layer_config[2], activation='linear', name='mean_tranformation_'+str(ch_id))(mean)
        means.append(mean_transformed)

    combined_rep=Multiply()(means)

    k_split = Lambda(split_for_sum_pool, name="split_for_sum_pool")(combined_rep)
    sum_pool = Add()(k_split)
    power_norm = Lambda(lambda xin: K.sign(xin)*K.sqrt(K.abs(xin)), name="power_norm")(sum_pool)
    l2_norm = Lambda(lambda xin: K.l2_normalize(xin,axis=1) , name="l2_norm")(power_norm)

    #mv = Concatenate()(means)
    #vv = Concatenate()(vars)
    #k1 = Concatenate()([mv, vv])
    d1 = Dense(int(hidden_layer_config[3]), activation='sigmoid', name='x_vector')(l2_norm)
    d2 = Dense(hidden_layer_config[4], activation='sigmoid', name='x_vector_2')(d1)
    output = Dense(num_classes, activation='softmax', name='dense_2')(d2)
    if get_embedding:
        model = keras.Model(inputs=inputs, outputs=d1)
    else:
        model = keras.Model(inputs=inputs, outputs=output)
    return model

def get_multichannel_tdnn_model(feat_size, num_classes, num_channels, hidden_layer_config, get_embedding = False):
    inputs = keras.Input(shape=(num_channels, None, feat_size))
    def split_channels(x):
        channel_data = tf.split(x, num_channels, axis=1)
        for i in range(len(channel_data)):
            channel_data[i] = tf.squeeze(channel_data[i], [1, ])
        return channel_data    

    tdnn_layer1 = TDNN(int(hidden_layer_config[0]),
                    input_context=(-2,0,2), padding='same',
                     activation="sigmoid",
                      name="TDNN1")
    tdnn_layer2 = TDNN(int(hidden_layer_config[1]),
                    input_context=(-2,0,+2), padding='same',
                     activation="sigmoid", name="TDNN2")
    tdnn_layer3 = TDNN(int(hidden_layer_config[2]),
                    input_context=(0,), padding='same',
                    activation="sigmoid", name="TDNN3")
    average = Lambda(lambda xin: K.mean(xin, axis=1), output_shape=(int(hidden_layer_config[1]),))
    variance = Lambda(lambda xin: K.std(xin, axis=1), output_shape=(int(hidden_layer_config[2]),))

    splitted_channels = Lambda(split_channels)(inputs)

    means = []
    vars = []
    for id, channel in enumerate(splitted_channels):
        t1 = tdnn_layer1(channel)
        t2 = tdnn_layer2(t1)
        t3 = tdnn_layer3(t2)
        means.append(average(t2))
        vars.append(variance(t3))
    mv = Concatenate()(means)
    vv = Concatenate()(vars)
    #k1 = Concatenate()([mv, vv])
    d1 = Dense(hidden_layer_config[3], activation='sigmoid', name='x_vector')(mv)
    dd1 = Dropout(0.2)(d1)
    d2 = Dense(hidden_layer_config[4], activation='sigmoid', name='x_vector_2')(dd1)
    output = Dense(num_classes, activation='softmax', name='dense_2')(d2)
    if get_embedding:
        model = keras.Model(inputs=inputs, outputs=d1)
    else:
        model = keras.Model(inputs=inputs, outputs=output)
    return model



def get_multichannel_tdnn_lstm_model(feat_size, num_classes, num_channels, hidden_layer_config, get_embedding = False):
    inputs = keras.Input(shape=(num_channels, None, feat_size))
    def split_channels(x):
        channel_data = tf.split(x, num_channels, axis=1)
        for i in range(len(channel_data)):
            channel_data[i] = tf.squeeze(channel_data[i], [1, ])
        return channel_data
    def exp_dims(x):
        x = tf.expand_dims(x,axis=1)   
        return x     

    tdnn_layer1 = TDNN(int(hidden_layer_config[0]),
                    input_context=(-2,0,2), padding='same',
                     activation="sigmoid",
                      name="TDNN1")
    tdnn_layer2 = TDNN(int(hidden_layer_config[1]),
                    input_context=(-4,-2,0,+2,+4), padding='same',
                     activation="sigmoid", name="TDNN2")
    tdnn_layer3 = TDNN(int(hidden_layer_config[2]),
                    input_context=(0,), padding='same',
                    activation="sigmoid", name="TDNN3")
    average = Lambda(lambda xin: K.mean(xin, axis=1), output_shape=(int(hidden_layer_config[2]),))
    variance = Lambda(lambda xin: K.std(xin, axis=1), output_shape=(int(hidden_layer_config[2]),))

    splitted_channels = Lambda(split_channels)(inputs)

    means = []
    vars = []
    for id, channel in enumerate(splitted_channels):
        t1 = tdnn_layer1(channel)
        t2 = tdnn_layer2(t1)
        t3 = tdnn_layer3(t2)
        mean = average(t3)
        mean_e = Lambda(exp_dims)(mean)
        means.append(mean_e)
        vars.append(variance(t3))
    mv = Concatenate(axis=1)(means)
    combined_rep = LSTM(hidden_layer_config[3],name="LSTM_Layer")(mv)   
   
    vv = Concatenate()(vars)
    #k1 = Concatenate()([mv, vv])
    d1 = Dense(hidden_layer_config[3], activation='sigmoid', name='x_vector')(combined_rep)
    dd1 = Dropout(0.2)(d1)
    d2 = Dense(hidden_layer_config[4], activation='sigmoid', name='x_vector_2')(dd1)
    output = Dense(num_classes, activation='softmax', name='dense_2')(d2)
    if get_embedding:
        model = keras.Model(inputs=inputs, outputs=d1)
    else:
        model = keras.Model(inputs=inputs, outputs=output)
    return model