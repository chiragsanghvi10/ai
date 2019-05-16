#!/usr/bin/env python
# coding: utf-8

# In[32]:


import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import time
import psycopg2
import json


# In[33]:


"""The semantic search engine crawls through all the conversations that have happened in the past and finds
similar conversation scenarios. The searching is not keyword driven like lucene does but is semantically
driven, meaning that a higher level representation is first obtained and then comparisions are done based
on that representation rather than the text itself."""


# In[34]:


tasks = []
embed = g = session = messages = output = None
class Snippet:
    """This class represents a snippet"""
    def __init__(self, from_time, to_time, text, index):
        self.from_time = from_time
        self.to_time = to_time
        self.text = text
        self.index = index

    def set_embedding(self, embedding):
        self.embedding = embedding

    def set_score(self, score):
        self.score = score

class Task:
    """This class represents a call"""
    def __init__(self, id, snips):
        self.id = id
        self.snips = snips


# In[35]:


def fetch_snips_analysis(analysis):
    """Parse the json containing snips and return a new list"""
    snips = []
    parsed_analysis = json.loads(analysis)
    i = 1
    for conversation in parsed_analysis["conversation"]:
        snip = Snippet(conversation["from"], conversation["to"], conversation["text"], i)
        i+=1
        snips.append(snip)
    return snips


# In[36]:


def embed_task(task):
    sentences = []
    for snip in task.snips:
        sentences.append(snip.text)
    global embed,g,session,messages,output
    if g == None:
        module_url = "https://tfhub.dev/google/universal-sentence-encoder-large/3"
        embed = hub.Module(module_url)
        g = tf.get_default_graph()
        session = tf.Session(graph=g)
        session.run([tf.global_variables_initializer(), tf.tables_initializer()])
        messages = tf.placeholder(dtype=tf.string, shape=[None])
        output = embed(messages)
    with g.as_default():
        message_embeddings = session.run(output, feed_dict={messages:  sentences})
    embeddings = np.array(message_embeddings)
    for idx, snip in enumerate(task.snips):
        x = embeddings[idx]
        #print(x)
        snip.set_embedding(x)


# In[37]:


# Let's index the sentence embeddings of all the snippets, that way we can quickly perform comparisions
def gather_data_org(organization_id = 67):
    """Will go through all the calls done in this organization and return the calls as collection of <Task>"""
    global tasks
    gstart = time.time()
    print('Gathering all calls for organization --> '+str(organization_id))
    sql = 'select * from task where actor in (select org_user.userid from org_user where org_user.organizationid = '+str(organization_id)+') '
    try:
        conn = psycopg2.connect("dbname='sales' user='postgres' host='db.talentify.in' password='cx6ac54nmgGtLD1y'")
        print("Database Connection established successsfully after: "+str(time.time()-gstart))
    except:
        print('Establishing connection with db failed')
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except:
        print("Query fetch failed")
        raise
    rows = cur.fetchall()
    print("Fetched "+str(len(rows))+" chunks from database after: "+str(time.time()-gstart))
    for idx, row in enumerate(rows):
        try:
            start = time.time()
            task_id = row[0]
            print(str((time.time() - start))+" pocessing task -->"+str(task_id))
            analysis = row[26]
            snips = fetch_snips_analysis(analysis)
            print(str((time.time() - start))+"task -->"+str(task_id)+" had "+str(len(snips))+" snippets")
            if len(snips)>1:
                t = Task(task_id, snips)
                print(str((time.time() - start))+"embedding task --> snippets ")
                embed_task(t)
                tasks.append(t)
            if idx % 100 == 0:
                print("\n\n\n\n\n\n\n\n\n\n\n\n\n")
                print('Processed total of '+str(idx)+' calls')
                print('Digested total of '+str(len(tasks))+' calls')
                print("\n\n\n\n\n\n\n\n\n\n\n\n\n")
        except Exception as e:
            print(e)


# In[ ]:


#gather_data_org()
#print(tasks)
#for task in tasks:
#    for idx, snip in enumerate(task.snips):
#        print(str(task.id)+"->"+str(snip.index)+"-->"+snip.text)


# In[30]:


# Let's first define the match method
def match(taskid1, idx1, taskid2, idx2):
    task1 = task2 = None
    for task in tasks:
        if task.id == taskid1:
            task1 = task
        if task.id == taskid2:
            task2 = task
    similarity12 = np.inner(task1.snips[idx1].embedding, task2.snips[idx2].embedding)
    print("Comparing -->"+task1.snips[idx1].text+" ||| against ||| "+task2.snips[idx2].text+"--->"+str(similarity12))


# In[31]:


#match(17958783, 44, 17958783, 45)
def find_task(taskid, ts = None):
    if ts == None:
        global tasks
        ts = tasks
    for task in tasks:
        if task.id == taskid:
            return task

def match(embedding):
    global tasks
    for task in tasks:
        print('Comparing against '+str(len(task.snips))+' snippets in task: '+str(task.id))
        for snip in task.snips:
            score = 0
            try:
                score = np.inner(snip.embedding, embedding)
            except Exception as e:
                print(e)
            snip.set_score(score)
            if score > 0.9:
                print(str(score)+'<<--->>'+snip.text)

def match_snip(taskid, idx):
    """For a given conversation snippet at a task, snippet index print all the similar snippets across the whole calls"""
    t = find_task(taskid)
    print('Comparing -->'+str(t.snips[idx].text))
    matches = []
    match(t.snips[idx].embedding)

def match_text(sentences):
    with g.as_default():
        message_embeddings = session.run(output, feed_dict={messages:  sentences})
    embeddings = np.array(message_embeddings)
    match(embeddings[0])

def print_top_results(taskz = None):
    if taskz == None:
        global tasks
        taskz = tasks


def test():
    gather_data_org()
    print('Comparing --> '+str(find_task(17946502).snips[3].text))
    match_snip(17946502, 3)
