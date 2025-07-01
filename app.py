from flask import Flask, request, render_template
from youtube_data_extractor import get_channel_data
from database import save_video_data

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    data = {}
    error = None

    if request.method == 'POST':
        channel_id = request.form['channel_id'].strip()
        result = get_channel_data(channel_id)

        if 'error' in result:
            error = result['error']
        else:
            data = result
            # Salvar cada vídeo individualmente
            for video in result['videos']:
                save_video_data(video['video_id'], video)

    return render_template('index.html', data=data, error=error)

if __name__ == '__main__':
    app.run(debug=True)
