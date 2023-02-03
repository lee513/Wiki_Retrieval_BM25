import wikipediaapi
import re
import numpy as np
import BM25
from konlpy.tag import Okt
import sys
import string
import requests
import json

class RetrieveSystem:
    
    
    def remove_stop_words(self, q_tok, doc_li):
        file_path = str(sys.argv[0])
        a = file_path.rfind("\\")
        file_path = file_path[:a]
   
        #stopwords 경로 설정
        stop_words_f = file_path + "\\stopwords.txt"
        print(stop_words_f)
        with open(stop_words_f, "r", encoding='utf-8') as f:
             stop_words = f.readlines()
        stop_words = [stop_word.strip() for stop_word in stop_words]
        q_result = [word for word in q_tok if not word in stop_words]
        
        doc_li_result = []
        for doc in doc_li:
            result = []
            for w in doc:
                if w not in stop_words:
                    result.append(w)
            doc_li_result.append(result)
            
        return q_result, doc_li_result   
    
    def working(self, query):
        def doc_search(q_tok):
            search_doc_li = []
            for i in range(len(q_tok)):
                wiki = wikipediaapi.Wikipedia(language='ko',
                                              extract_format=wikipediaapi.ExtractFormat.WIKI)
                doc_wiki = wiki.page(q_tok[i])
                one_doc = doc_wiki.text
                doc = one_doc
                search_doc_li.append(doc)
            return search_doc_li
        
        
        def preprocessing(pre_doc):
            for i in range(len(pre_doc)):
                pre_doc[i] = re.sub('\《.*\》|\s-\s.*', '', pre_doc[i])
                pre_doc[i] = re.sub('\(.*\)|\s-\s.*', '', pre_doc[i])
                #필드의 태그를 모두 제거
                pre_doc[i] = re.sub('(<([^>]+)>)', '', pre_doc[i])
                # 개행문자 제거
                pre_doc[i] = re.sub('\\\\n', ' ', pre_doc[i])
                #한글 숫자만 제외 모두 제
                pre_doc[i] = re.sub('[^가-힣ㄱ-ㅎㅏ-ㅣ0-9]', ' ', pre_doc[i])
                pre_doc[i] = ' '.join(pre_doc[i].split())
            return pre_doc
        
        
        def tokenizing(docs):
            doc_tokens = [self.okt.morphs(row) for row in docs]
            return doc_tokens
        
        
        def q_preprocessing(q):
            #한글, 숫자만 남기고 모두 제거
            q = re.sub('[^가-힣ㄱ-ㅎㅏ-ㅣ0-9]', ' ', q)
            #토큰화
            return self.okt.morphs(q)
        
        self.okt = Okt()
        
        query = str(query)
        
        #명사기반(예시)
        #noun_tok_query = self.okt.nouns(query)
        
        #어절기반(예시)
        phrase_tok_query = self.okt.phrases(query)
        
        #문서 긁어오기
        searched_doc = doc_search(phrase_tok_query)
        
        #전처리
        refined_docs = preprocessing(searched_doc)
        
        #토큰화
        tok_docs = tokenizing(refined_docs)
           
        #query 토큰화
        all_tok_query = q_preprocessing(query)
        
        stopword_q, stopword_doc_li = self.remove_stop_words(all_tok_query, tok_docs)
        
        ###---bm25---
        bm25 = BM25.BM25()
        bm25.fit(stopword_doc_li)
        scores = bm25.search(stopword_q)
        
        #질문에 대한 문서들의 top문서와 질의에 대한 키워드 매칭
        #query에 대한 핵심 keyword
        keyword = phrase_tok_query[scores.index((max(scores)))]
        
        #query에 대한 핵심 keyword의 wiki검색 모든 text
        keyword_all_text = refined_docs[scores.index((max(scores)))]
        
        self.all_tok_query = all_tok_query
        self.stopword_q = stopword_q
        self.keyword = keyword
    
    def matching(self):
        
        #키워드를 wikiapi를 활용하여 문서를 쪼갠다.
        wiki = wikipediaapi.Wikipedia(language='ko')
        key_doc = wiki.page(self.keyword)
        key_summary = key_doc.summary[:]
        key_sections = key_doc.sections[:-1]
        
        #section 리스트를 문자열 리스트로 변환
        str_key_sections = []
        for i in range(len(key_sections)):
            str_key_sections.append(str(key_sections[i]))
            
        #각 section을 전부 분해 한다.
        str_key_sections = ''.join(str_key_sections)
        div_key_li = str_key_sections.split('Section: ')
            
        #summary리스트에 section리스트를 결합
        key_li = [key_summary]
        for i in range(len(div_key_li)):
            key_li.append(div_key_li[i])
        
        #빈 요소, 너무 짧은 문자열은 제거
        div_key_li = []
        for i in range(len(key_li)):
            if len(key_li[i]) > 5:
                div_key_li.append(key_li[i])
    
        #--------------------------------
        #key의 기본 전처리 
        pre_key_li = []
        for doc in range(len(div_key_li)):
            pre_key_li.append(re.sub('Section: |Subsections |\n|', '', div_key_li[doc]))
        len(pre_key_li)
        pre_key_li
        #--------------------------------

        #BM25를 사용하기위한 전처리
        all_pre_key_li = []
        for doc in range(len(pre_key_li)):
            all_pre_key_li.append(re.sub('[^가-힣ㄱ-ㅎㅏ-ㅣ0-9]', ' ', pre_key_li[doc]))
        for doc in range(len(pre_key_li)):
            all_pre_key_li[doc] = ' '.join(all_pre_key_li[doc].split())
            all_pre_key_li[doc] = re.sub('  +[0-9]+  ', '', all_pre_key_li[doc])
        
        #key_li_tok토큰화
        tok_key_li = [self.okt.morphs(row) for row in all_pre_key_li]
        
        #토큰들 정제
        #토큰화된 문서들을 솎아내기
        #토큰안에 한 숫자만 있는것은 지운다.
        removal_tok = ['0','1','2','3','4','5','6','7','8','9']
        refined_tok_key_li = []
        for doc in tok_key_li:
            result = []
            for tok in doc:
                if tok not in removal_tok:
                    result.append(tok)
            refined_tok_key_li.append(result)
            
        #또한 각 문서 마다 토큰 숫자가 3개 미만은 remove_tok_li, remove_tok_idx에 저장
        remove_tok_li = []
        remove_tok_idx = []
        for i in range(len(refined_tok_key_li)):
            if len(refined_tok_key_li[i]) < 3:
                remove_tok_li.append(refined_tok_key_li[i])
                remove_tok_idx.append(i)
        
        #저장된 remove_tok_li에서 하나씩 뽑아 제거
        if len(remove_tok_li) >= 1:
            for i in remove_tok_li:
                refined_tok_key_li.remove(i)    

        #중요!!!!!!        
        #pre_key_li에도 똑같이 적용 시킨다.
        if len(remove_tok_idx) >= 1:
            remove_elements = []
            for idx in remove_tok_idx:
                remove_elements.append(pre_key_li[idx])
            for element in remove_elements:
                pre_key_li.remove(element)

        ## refined_tok_key_li 와 all_tok_query
        key_stopword_q, stopword_key_docs = self.remove_stop_words(self.all_tok_query, refined_tok_key_li)

        bm25 = BM25.BM25()
        bm25.fit(stopword_key_docs)
        scores = bm25.search(key_stopword_q)
        scores
        #top문서 index 
        scores.index((max(scores)))
        result_doc = pre_key_li[scores.index((max(scores)))]
        self.result_doc = result_doc
        #query, result_doc

        #for score, doc in zip(scores, pre_key_li):
        #    score = round(score, 3)
        #    print(str(score) + '\t' + doc)
        #질문하신 주요한 키워드는 'keyword'입니다.
        print("질문하신 주요한 키워드는 '{0}' 입니다.".format(self.keyword))
        #print("질문에 대한 문서 검색 결과: {0}".format(self.result_doc))
        #for score, doc in zip(scores, pre_key_li):
        #    score = round(score, 3)
        #    print(str(score) + '\t' + doc)
        return self.result_doc
        

    def sending(self, anwser, query):
        request_text = []
        question = [{"question": query}]
        request_text.append({'context': anwser, 'questionInfoList': question}) 
        URL = 'http://211.39.140.116:8080/mrc' 
        headers={
            'Content-type':'application/json', 
            'Accept':'application/json'
        }
        response = requests.post(URL + '/predict/documents', data=json.dumps(request_text), headers=headers)
        a = response.text
        return a
        
        
    
if __name__=='__main__':
    query = '....'
    team5 = RetrieveSystem()
    team5.working(query)
    anwser =team5.matching()
    request_text = team5.sending(anwser, query)  

#연평도 포격전의 사망자 수는?
#이순신의 첫 승전은?
    
    
    
    
    
    
    
    
    
    
    