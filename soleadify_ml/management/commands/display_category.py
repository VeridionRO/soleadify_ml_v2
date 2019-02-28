from sklearn.feature_extraction import text
import matplotlib.pyplot as plt
from sklearn.decomposition import TruncatedSVD
import numpy as np
import hdbscan
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
import pandas as pd
from django.core.management.base import BaseCommand
import json
from soleadify_ml import settings
from soleadify_ml.models.category import Category
from soleadify_ml.models.category_website_text import CategoryWebsiteText


class Command(BaseCommand):
    help = 'Plot category / categories'
    description = 'This command will recreate your spacy_customn_model using the SPACY_NEW_ENTITIES_FILE ' \
                  'that contains annotations of the new labels'

    def add_arguments(self, parser):
        parser.add_argument('-c', '--categories', metavar='N', type=int, nargs='+',
                            default=[10511],
                            help='Categories to display')

    def handle(self, *args, **options):
        category_ids = options['categories']
        extra_stop_words = pd.read_csv(settings.STOP_WORDS_FILE)
        my_stop_words = text.ENGLISH_STOP_WORDS.union(extra_stop_words.word.str.lower().tolist())

        tf_idf_vector = TfidfVectorizer(
            max_features=10000,
            # max_df=0.8,
            min_df=5,
            stop_words=my_stop_words,
            ngram_range=(1, 2)
        )

        categories = Category.objects. \
            values_list('id', 'name'). \
            filter(id__in=category_ids).all()

        for category in categories:
            categories_websites = {}
            category_id = category[0]
            category_name = category[1]
            plt.figure(str(category_id) + ' - ' + category_name)
            plt.title(str(category_id) + ' - ' + category_name)

            category_texts = CategoryWebsiteText.objects. \
                filter(category_id=category_id). \
                values_list('category_id', 'website_id', 'page_text').all()

            df = pd.DataFrame(list(category_texts.values()), columns=['category_id', 'website_id', 'page_text'])

            data = tf_idf_vector.fit_transform(df['page_text']).toarray()
            terms = np.array(tf_idf_vector.get_feature_names())

            x_reduced = TruncatedSVD(n_components=400).fit_transform(data)
            data_2d = TSNE(n_components=2).fit_transform(x_reduced)

            hdb = hdbscan.HDBSCAN(min_cluster_size=20, min_samples=1, core_dist_n_jobs=8).fit(data_2d)
            labels = hdb.labels_
            core_samples_mask = labels != -1

            X = pd.DataFrame(data, columns=terms)  # columns argument is optional
            X['Cluster'] = labels  # Add column corresponding to cluster number
            word_frequencies_by_cluster = X.groupby('Cluster').sum()

            unique_labels = set(labels)
            colors = [plt.cm.Spectral(each)
                      for each in np.linspace(0, 1, len(unique_labels))]
            for k, col in zip(unique_labels, colors):

                if k == -1:
                    # Black used for noise.
                    col = [0, 0, 0, 1]

                class_member_mask = (labels == k)

                xy = data_2d[class_member_mask & core_samples_mask]
                plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
                         markeredgecolor='k', markersize=14)

                plt.text(np.mean(xy[:, 0]), np.mean(xy[:, 1]), str(k), size=10,
                         ha="center", va="center",
                         bbox=dict(boxstyle="circle")
                         )

                words = word_frequencies_by_cluster.loc[k].sort_values(ascending=False)
                string_key = ', '.join(
                    [str(round(a, 2)) + '-' + b for a, b in zip(words[:20].tolist(), words.index[:20].tolist())])
                print("Cluster " + str(k) + " has " + str(np.count_nonzero(labels == k)) + ":" + string_key)
                cluster_key = "cluster_key " + str(k) + ": " + string_key

                categories_websites[cluster_key] = df.loc[np.where(labels == k)[0].tolist()]['website_id'].tolist()

                xy = data_2d[class_member_mask & ~core_samples_mask]
                plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
                         markeredgecolor='k', markersize=6)

            with open(settings.PROJECT_DIR + '/extra_files/' + str(category_id) + '.json', 'w') as outfile:
                json.dump(categories_websites, outfile)

        plt.show()
        time.sleep(10000)
