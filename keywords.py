import spacy

nlp_pl = spacy.load('pl_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')

# def extract_keywords(query):
#     doc = nlp_pl(query)
#     keywords = [token.lemma_.lower() for token in doc 
#                 if not token.is_stop and not token.is_punct and token.is_alpha]
    
#     if not keywords:
#         doc = nlp_en(query)
#         keywords = [token.lemma_.lower() for token in doc 
#                     if not token.is_stop and not token.is_punct and token.is_alpha]
    
#     return keywords

def extract_keywords(query):
    doc = nlp_pl(query)
    for token in doc:
        print(f"{token.text} -> POS: {token.pos_}, lemma: {token.lemma_}, stop: {token.is_stop}")
    
    keywords = [token.lemma_.lower() for token in doc 
                if not token.is_stop and not token.is_punct and token.is_alpha]
    return keywords