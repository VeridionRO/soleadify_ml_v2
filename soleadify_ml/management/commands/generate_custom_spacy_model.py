from __future__ import unicode_literals, print_function
from django.core.management.base import BaseCommand
import random
from django.conf import settings
from pathlib import Path
import spacy

from soleadify_ml.utils.MLUtils import convert_dataturks_to_spacy


class Command(BaseCommand):
    help = 'Recreate custom spacy model'
    description = 'This command will recreate your spacy_customn_model using the SPACY_NEW_ENTITIES_FILE ' \
                  'that contains annotations of the new labels'
    custom_labels = ['TITLE', 'ORG', 'PERSON', 'EMAIL', 'PHONE', 'LAW_CAT']

    def add_arguments(self, parser):
        parser.add_argument('-i', '--iteration', type=str, help='Number of iterations')
        parser.add_argument('-m', '--model', type=str, help='Number of iterations')

    def handle(self, *args, **options):
        n_iter = options['iteration'] or 10
        model = options['model'] or 'en_core_web_lg'
        output_dir = settings.SPACY_CUSTOMN_MODEL_FOLDER
        train_data = convert_dataturks_to_spacy(settings.SPACY_NEW_ENTITIES_FILE)

        # if the model exists, then load it
        if model:
            nlp = spacy.load(model)
        else:
            # if no model is added then
            nlp = spacy.blank('en')

        if 'ner' not in nlp.pipe_names:
            ner = nlp.create_pipe('ner')
            nlp.add_pipe(ner)
        else:
            # otherwise, get it, so we can add labels to it
            ner = nlp.get_pipe('ner')

        for label in self.custom_labels:
            ner.add_label(label)

        # get names of other pipes to disable them during training
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
        with nlp.disable_pipes(*other_pipes):  # only train NER
            if model:
                optimizer = nlp.entity.create_optimizer()
            else:
                optimizer = nlp.begin_training()
            for itn in range(n_iter):
                print("Starting iteration " + str(itn))
                random.shuffle(train_data)
                losses = {}
                for text, annotations in train_data:
                    # print(text)
                    try:
                        nlp.update(
                            [text],  # batch of texts
                            [annotations],  # batch of annotations
                            drop=0.2,  # dropout - make it harder to memorise data
                            sgd=optimizer,  # callable to update weights
                            losses=losses)
                    except Exception:
                        print('error')
                        print(text)
                        continue
                print(losses)

        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
