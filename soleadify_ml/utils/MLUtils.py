import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.feature_extraction import text
from django.conf import settings

"""
take info from the database and train a model to predict category for new text
"""


def prepare(categories):
    x_train, x_test, y_train, y_test, indices_train, indices_test = train_test_split(categories['page_text'],
                                                                                     categories.category_id,
                                                                                     categories.index,
                                                                                     test_size=0.3)
    x_train_counts = count_vect.fit_transform(x_train)
    tfidf_transformer = TfidfTransformer()
    x_train_tfidf = tfidf_transformer.fit_transform(x_train_counts)
    model.fit(x_train_tfidf, y_train)


def predict_category(website_text):
    website_text = [website_text]
    # categories = dict(zip(
    #     self.model.classes_.tolist(),
    #     self.model.predict_proba(self.count_vect.transform(website_text)).tolist()[0]
    # ))

    # category_counter = Counter(categories)
    # categories = category_counter.most_common(5)

    categories = model.predict(count_vect.transform(website_text)).tolist()

    return categories


def stop_words():
    """
    get custom stop words joined with the default english stop words
    :return:
    """
    extra_stop_words = pd.read_csv(settings.STOP_WORDS_FILE)
    my_stop_words = text.ENGLISH_STOP_WORDS.union(extra_stop_words.word.str.lower().tolist())
    return my_stop_words


def sort_coo(coo_matrix):
    tuples = zip(coo_matrix.col, coo_matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)


def extract_topn_from_vector(feature_names, sorted_items, topn=100):
    """get the feature names and tf-idf score of top n items"""

    # use only topn items from vector
    sorted_items = sorted_items[:topn]

    score_vals = []
    feature_vals = []

    # word index and corresponding tf-idf score
    for idx, score in sorted_items:
        # keep track of feature name and its corresponding score
        score_vals.append(round(score, 3))
        feature_vals.append(feature_names[idx])

    # create a tuples of feature,score
    # results = zip(feature_vals,score_vals)
    results = {}
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]] = score_vals[idx]

    return results


def convert_dataturks_to_spacy(dataturks_json_filepath):
    try:
        training_data = []
        with open(dataturks_json_filepath, 'r') as f:
            lines = f.readlines()

        for line in lines:
            data = json.loads(line)
            text = data['content']
            entities = []
            if data['annotation']:
                for annotation in data['annotation']:
                    # only a single point in text annotation.
                    point = annotation['points'][0]
                    labels = annotation['label']
                    # handle both list of labels or a single label.
                    if not isinstance(labels, list):
                        labels = [labels]

                    for label in labels:
                        # dataturks indices are both inclusive [start, end] but spacy is not [start, end)
                        entities.append((point['start'], point['end'] + 1, label))

            training_data.append((text, {"entities": entities}))

        return training_data
    except Exception as e:
        return None


model = LinearSVC(penalty='l2', dual=False)
count_vect = CountVectorizer(max_df=0.6, min_df=5, ngram_range=(1, 2), stop_words=stop_words())
