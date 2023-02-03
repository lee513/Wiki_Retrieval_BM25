from flask import Flask, render_template, request
import realtime_retrieve_5_4
app = Flask(__name__)
 
@app.route('/')
def student():
   return render_template('index.html')
 
@app.route('/index2',methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      a= {}
      val = request.form.get('질문')
      team5 = realtime_retrieve_5_4.RetrieveSystem()
      team5.working(val)
      anwser = team5.matching()
      request_text = team5.sending(anwser, val)
      a = {"내용" :anwser}
      a.update({val :request_text })
      return render_template("index2.html",result = a) 
 
if __name__ == '__main__':
   app.run(debug = True)
