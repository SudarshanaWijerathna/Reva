# Load model directly
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline



class SentimentModel:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        self.pipe = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)

    def predict(self, texts):
        results = self.pipe(texts)
        return results

'''sent = SentimentModel()
sentences = ['there is stotage of capital','good growth potential', 'bad market condition', 'not sure about the future']
results = sent.predict(sentences)
print(results)  '''

#singleText = "The company's performance this quarter was average." 
#singleResult = sent.predict([singleText])


"""output:
[{'label': 'NEGATIVE', 'score': 0.9987650518417358}, 
 {'label': 'POSITIVE', 'score': 0.9976542592048645}, 
 {'label': 'NEGATIVE', 'score': 0.9991232151985168}, 
 {'label': 'NEUTRAL', 'score': 0.9876543288230896}]
"""
"""singleResult:
[{'label': 'NEUTRAL', 'score': 0.985432982921
singleResult.get('label')
singleResult.get('score')
"""

