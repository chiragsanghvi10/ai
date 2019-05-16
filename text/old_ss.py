from flask import request
from flask import jsonify
from app import SentenceSimilarity
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import time

app = Flask(__name__)


#def init():
print("Init called -----``````~~~~~~")
global embed,g,session,messages,output
module_url = "https://tfhub.dev/google/universal-sentence-encoder-large/3"
embed = hub.Module(module_url)
g = tf.get_default_graph()
session = tf.Session(graph=g)
session.run([tf.global_variables_initializer(), tf.tables_initializer()])
messages = tf.placeholder(dtype=tf.string, shape=[None])
output = embed(messages)

@app.route("/", methods=['GET', 'POST'])
def hello():
    start = time.time()
    sentence1 = request.form['sentence1']
    sentence2 = request.form['sentence2']
    print(sentence1)
    print(sentence2)
    print('Parsing done after: '+str(time.time()-start))
    with g.as_default():
        message_embeddings = session.run(output, feed_dict={messages:  [sentence1, sentence2]})
    print('Embedding done after: '+str(time.time()-start))
    sentence1Embeddings = np.array(message_embeddings)[0]
    sentence2Embeddings = np.array(message_embeddings)[1]
    print('Inner product done after: '+str(time.time()-start))
    similarity12 = np.inner(sentence1Embeddings, sentence2Embeddings)
    return jsonify(sentence1=sentence1, sentence2=sentence2, similarityScore=str(similarity12))

if __name__ == '__main__':
#    init()
    app.run(debug=True, threaded=True, host='0.0.0.0', port='5010')