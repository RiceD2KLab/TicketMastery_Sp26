from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import WordCloud
import Utils  

app = FastAPI(title="WordCloud API", version="0.1.0")

# Allow JS frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later for production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/wordcloud")
def generate_wordcloud(assets_csv, tickets_csv, space_csv, group=None):
    """
    Calls Utils on Data
    """
    df = Utils.process_data(tickets_csv, assets_csv, space_csv)
    return WordCloud.word_frequency(df, group)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)