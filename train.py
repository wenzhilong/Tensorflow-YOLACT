import os
import datetime
import contextlib
import tensorflow as tf

# it s recommanded to use absl for tf 2.0
from absl import app
from absl import flags
from absl import logging

from yolact import Yolact
from loss import loss_yolact
from utils import learning_rate_schedule
from data.coco_dataset import ObjectDetectionDataset

from eval import evaluate

import config as cfg

FLAGS = flags.FLAGS

flags.DEFINE_string('name', 'coco',
                    'name of dataset')
flags.DEFINE_string('tfrecord_dir', 'data',
                    'directory of tfrecord')
flags.DEFINE_string('config', './config/config_coco.json',
                    'path of config file')
flags.DEFINE_string('weights', 'weights',
                    'path to store weights')
flags.DEFINE_integer('train_iter', 10000,
                     'iteraitons')
flags.DEFINE_integer('batch_size', 3,
                     'batch size')
flags.DEFINE_float('momentum', 0.9,
                   'momentum')
flags.DEFINE_float('weight_decay', 5 * 1e-4,
                   'weight_decay')
flags.DEFINE_float('print_interval', 10,
                   'number of iteration between printing loss')
flags.DEFINE_float('save_interval', 1000,
                   'number of iteration between saving model(checkpoint)')
flags.DEFINE_float('valid_iter', 1000,
                   'number of iteration between saving validation weights')


@tf.function
def train_step(model,
               loss_fn,
               metrics,
               optimizer,
               image,
               labels):
    # training using tensorflow gradient tape
    with tf.GradientTape() as tape:
        output = model(image, training=True)
        # Todo consider if using other dataset (make it general)
        loc_loss, conf_loss, mask_loss, seg_loss, total_loss = loss_fn(output, labels, len(cfg.COCO_CLASSES) + 1)
    grads = tape.gradient(total_loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))
    metrics.update_state(total_loss)
    return loc_loss, conf_loss, mask_loss, seg_loss


def main(argv):
    # set fixed random seed
    tf.random.set_seed(cfg.RANDOM_SEED)

    # set up Grappler for graph optimization
    # Ref: https://www.tensorflow.org/guide/graph_optimization
    @contextlib.contextmanager
    def options(opts):
        old_opts = tf.config.optimizer.get_experimental_options()
        tf.config.optimizer.set_experimental_options(opts)
        try:
            yield
        finally:
            tf.config.optimizer.set_experimental_options(old_opts)

    # -----------------------------------------------------------------
    # Creating the instance of the model specified.
    logging.info("Creating the model instance of YOLACT")
    model = Yolact(**cfg.model_parmas)

    # add weight decay
    for layer in model.layers:
        if isinstance(layer, tf.keras.layers.Conv2D) or isinstance(layer, tf.keras.layers.Dense):
            layer.add_loss(lambda: tf.keras.regularizers.l2(FLAGS.weight_decay)(layer.kernel))
        if hasattr(layer, 'bias_regularizer') and layer.use_bias:
            layer.add_loss(lambda: tf.keras.regularizers.l2(FLAGS.weight_decay)(layer.bias))

    # -----------------------------------------------------------------
    # Creating dataloaders for training and validation
    logging.info("Creating the dataloader from: %s..." % FLAGS.tfrecord_dir)
    dateset = ObjectDetectionDataset(dataset_name=FLAGS.name,
                                     tfrecord_dir=os.path.join(FLAGS.tfrecord_dir, FLAGS.name),
                                     anchor_instance=model.anchor_instance,
                                     **cfg.parser_params)
    train_dataset = dateset.get_dataloader(subset='train', batch_size=FLAGS.batch_size)
    valid_dataset = dateset.get_dataloader(subset='val', batch_size=FLAGS.batch_size)

    # count number of valid data for progress bar
    # Todo any better way to do it?
    num_val = 4953
    # for _ in valid_dataset:
    #     num_val += 1
    logging.info("Number of Valid data", num_val * FLAGS.batch_size)

    # -----------------------------------------------------------------
    # Choose the Optimizor, Loss Function, and Metrics, learning rate schedule
    # Todo add config to lr schedule
    lr_schedule = learning_rate_schedule.Yolact_LearningRateSchedule(**cfg.lrs_chedule_params)
    logging.info("Initiate the Optimizer and Loss function...")
    optimizer = tf.keras.optimizers.SGD(learning_rate=lr_schedule, momentum=FLAGS.momentum)
    criterion = loss_yolact.YOLACTLoss(**cfg.loss_params)
    train_loss = tf.keras.metrics.Mean('train_loss', dtype=tf.float32)
    loc = tf.keras.metrics.Mean('loc_loss', dtype=tf.float32)
    conf = tf.keras.metrics.Mean('conf_loss', dtype=tf.float32)
    mask = tf.keras.metrics.Mean('mask_loss', dtype=tf.float32)
    seg = tf.keras.metrics.Mean('seg_loss', dtype=tf.float32)

    # Todo adding to tensorboard
    # v_bboxes_map = ...
    # v_masks_map = ...
    # -----------------------------------------------------------------

    # Setup the TensorBoard for better visualization
    # Ref: https://www.tensorflow.org/tensorboard/get_started
    logging.info("Setup the TensorBoard...")
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    train_log_dir = './logs/gradient_tape/' + current_time + '/train'
    test_log_dir = './logs/gradient_tape/' + current_time + '/test'
    train_summary_writer = tf.summary.create_file_writer(train_log_dir)
    test_summary_writer = tf.summary.create_file_writer(test_log_dir)

    # -----------------------------------------------------------------
    # Start the Training and Validation Process
    logging.info("Start the training process...")

    # setup checkpoints manager
    checkpoint = tf.train.Checkpoint(step=tf.Variable(1), optimizer=optimizer, model=model)
    manager = tf.train.CheckpointManager(
        checkpoint, directory="./checkpoints", max_to_keep=5
    )
    # restore from latest checkpoint and iteration
    status = checkpoint.restore(manager.latest_checkpoint)
    if manager.latest_checkpoint:
        logging.info("Restored from {}".format(manager.latest_checkpoint))
    else:
        logging.info("Initializing from scratch.")

    best_masks_map = 0.
    iterations = checkpoint.step.numpy()

    for image, labels in train_dataset:
        # check iteration and change the learning rate
        if iterations > FLAGS.train_iter:
            break

        checkpoint.step.assign_add(1)
        iterations += 1
        with options({'constant_folding': True,
                      'layout_optimize': True,
                      'loop_optimization': True,
                      'arithmetic_optimization': True,
                      'remapping': True}):
            loc_loss, conf_loss, mask_loss, seg_loss = train_step(model, criterion, train_loss, optimizer, image,
                                                                  labels)
        loc.update_state(loc_loss)
        conf.update_state(conf_loss)
        mask.update_state(mask_loss)
        seg.update_state(seg_loss)
        with train_summary_writer.as_default():
            tf.summary.scalar('Total loss', train_loss.result(), step=iterations)
            tf.summary.scalar('Loc loss', loc.result(), step=iterations)
            tf.summary.scalar('Conf loss', conf.result(), step=iterations)
            tf.summary.scalar('Mask loss', mask.result(), step=iterations)
            tf.summary.scalar('Seg loss', seg.result(), step=iterations)

        if iterations and iterations % FLAGS.print_interval == 0:
            tf.print("Iteration {}, LR: {}, Total Loss: {}, B: {},  C: {}, M: {}, S:{} ".format(
                iterations,
                optimizer._decayed_lr(var_dtype=tf.float32),
                train_loss.result(),
                loc.result(),
                conf.result(),
                mask.result(),
                seg.result()
            ))

        if iterations and iterations % FLAGS.save_interval == 0:
            # save checkpoint
            save_path = manager.save()
            logging.info("Saved checkpoint for step {}: {}".format(int(checkpoint.step), save_path))

            # validation and print mAP table
            # Todo make evaluation faster, and return bboxes mAP / masks mAP
            all_map = evaluate(model, valid_dataset, num_val)
            bboxes_map, masks_map = ...

            with test_summary_writer.as_default():
                # Todo write mAP in tensorboard
                ...

            # Todo save the best mAP
            if masks_map < best_masks_map:
                # Saving the weights:
                best_masks_map = masks_map
                model.save_weights('./weights/weights_' + str(best_masks_map) + '.h5')

            # reset the metrics
            train_loss.reset_states()
            loc.reset_states()
            conf.reset_states()
            mask.reset_states()
            seg.reset_states()
            # todo reset bbox ap, mask ap


if __name__ == '__main__':
    app.run(main)
