//**_
Here are informations found for the project
_**//

# SOURCES

https://kraken.re/main/training.html#training
https://kraken.re/main/ketos.html

##### produce models

https://digitalorientalist.com/2019/11/05/using-kraken-to-train-your-own-ocr-models/
https://digitalintellectuals.hypotheses.org/3702
https://github.com/cmroughan/kraken_generated-data/blob/master/examples/example.ipynb

> General cases
> https://medium.com/@corymaklin/fine-tuning-machine-learning-models-a37c13f76eb5

##### escriptorium

https://gitlab.com/scripta/escriptorium/-/wikis/docker-install

Pre-conditions using Kraken HTR

-avoid binary image (it loses too much information)
-Scans shuld be lossless or at least slightly compressed JPEG, no PDF

- cases of Splittings scans into pages, pre-processing, ...

- better to have large coverage of typographic features that is exhaustive
- for one specific material, 100~ samples, general is 1000~
- May be required to retrain model

## Kraken specifics

Both segmentation and recognition are trainable in kraken. The segmentation model finds baselines and regions on a page image. Recognition models convert text image lines found by the segmenter into digital text.

## Annotation and transcription

> escriptorium integrates kraken
> Aletheia desktop application ( Paid product )

## Train model

> Training data = collection of PAGE XML documents with annotation and transcription

keros train output_dir/\*.png
--report --savefreq --preload
-v -vv (verbose)
--load to continue training an existing model

rough guide is that accuracy seldom improves after 50 epochs reached between 8 and 24 hours of training.

ketos test -m syriac_best.mlmodel lines/\*.png

## Tips on ML

early stopping to avoid overfitting
After training is finished the best model is saved as model_name_best.mlmodel. It is highly recommended to also archive the training log and data for later reference.
Depending on the error source, correction most often involves adding more training data and fixing transcriptions. Sometimes it may even be advisable to remove unrepresentative data from the training set.

> tips numerical
> pinpoint weaknesses in the training data, e.g. above average error rates for numerals indicate either a lack of representation of numerals in the training data or erroneous transcription in the first place.

SLICING
Refining on mismatched alphabets has its limits. If the alphabets are highly different the modification of the final linear layer to add/remove character will destroy the inference capabilities of the network. In those cases it is faster to slice off the last few layers of the network and only train those instead of a complete network from scratch.

## Kraken Recognition training

ketos -o model --load old_model.mlmodel
-F --savefreq
-q --quit >> default set to early stopping
-N nb epoch
--min-epochs (when early stopping)
--lag (nb epoch to stop training without improvement for early stopping)
-d device to use
--optimizer Adam, SGD, RMSprop
-t --lrate learning rate
-w weight-decay
-p ratio train/validation set
-c load codec JSON (when no existing model)
-t additional training files
--augment / --no-augment Data augmentation
-e evaluation files ( override -p)
-f format type

--resize ??
-n == reorder ?
--workers
-s network see network description language can be found on the VGSL page.

Sometimes the early stopping default parameters might produce suboptimal results such as stopping training too soon. Adjusting the minimum delta an/or lag can be useful:

ketos train --lag 10 --min-delta 0.001 syr/\*.png

A better configuration for large and complicated datasets such as handwritten texts:

ketos train --augment --workers 4 -d cuda -f binary --min-epochs 20 -w 0 -s '[1,120,0,1 Cr3,13,32 Do0.1,2 Mp2,2 Cr3,13,32 Do0.1,2 Mp2,2 Cr3,9,64 Do0.1,2 Mp2,2 Cr3,9,64 Do0.1,2 S1(1x0)1,3 Lbx200 Do0.1,2 Lbx200 Do.1,2 Lbx200 Do]' -r 0.0001 dataset_large.arrow

This configuration is slower to train and often requires a couple of epochs to output any sensible text at all. Therefore we tell ketos to train for at least 20 epochs so the early stopping algorithm doesn’t prematurely interrupt the training process.

ketos -v train --resize union -i model_5.mlmodel syr/\*.png

## Testing command

```


Binarize img (deprecated)
kraken -i input.jpg bw.png binarize

ketos train -i base.mlmodel datas2/*.jpg -f path
```
