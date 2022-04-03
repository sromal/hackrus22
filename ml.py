import numpy as np

def load_model():
    model = {}
    with open("glove.6B.50d.txt", "r", encoding="utf-8") as file:
        for line in file.readlines():
            parts = line.split(' ')
            model[parts[0]] = np.array([float(x) for x in parts[1:]])

    return model


def cosine_similarity(model, word1, word2):
    vec1 = model[word1]
    vec2 = model[word2]
    return vec1.dot(vec2) / (np.linalg.norm(vec1, 2) * np.linalg.norm(vec2, 2))

