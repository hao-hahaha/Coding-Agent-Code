
from flask import Flask, jsonify, render_template, request

from backend.memory import Memory
app=Flask(__name__,template_folder='templates',static_folder='static')
mem=Memory()
@app.route('/')
def index(): return render_template('index.html')
@app.route('/api/logs')
def logs():
    limit=int(request.args.get('limit',100))
    return jsonify(mem.query(limit))
if __name__=='__main__':
    app.run(port=3000,host='0.0.0.0')
