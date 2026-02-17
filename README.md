## Setup Instructions for LanceDB_NatGeo

### 1. Install `uv` (Python package manager)

Open your terminal and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository
If you have Git installed, go to the directory in which you want the github repo & run:

```bash
git clone https://github.com/SiyaKamboj/LanceDB_NatGeo.git
```
If you do not have Git installed, you can download the directory as a ZIP file and unzip it manually.

<!-- ### 3. Open the Project in Visual Studio Code
Open the LanceDB_NatGeo folder using Visual Studio Code.

### 4. Sync the environment
Open your terminal in the project root (inside LanceDB_NatGeo) and type:

```bash
uv sync
```
This will install all the necessary dependencies.

### 5. Move your audio files
Move your audio files into the LanceDB_NatGeo directory. These will be used by the notebook to populate LanceDB.

### 6. Launch the Notebook
Open insert_mus_into_LanceDB.ipynb in VS Code. This is called a Jupyter Notebook. 

When prompted to select a kernel on the top right, choose the one from this venv. It should be called "uv-venv-music"

### 7. Run the Code
You can now execute each code block by clicking the ▶️ play button in the top-left corner of each cell.

In each cell, I have placed some comments describing what the code is doing, but I have also placed some comments, starting with "#NOTE To Muha:" containing important information that should be read before executing the code block.  -->

## React + API setup (step 1 and step 2)

- `backend/app.py` (FastAPI API for LanceDB path and audio-directory validation)
- `frontend/` (React app for the 2-step setup flow)

### Run backend

From project root:

```bash
uv sync
uv run uvicorn backend.app:app --reload
```

Backend runs at `http://localhost:8000`, though you don't need to open this up. 

### Run frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` & u should open up this link in the browser. 

<!-- ### Current UI behavior

1. Database path and audio-directory inputs are both visible immediately.
2. Database submit: if path exists, connect; otherwise create/connect new DB there.
3. During database submit, ensure `music_embeddings` table exists using the notebook schema (create if missing).
4. Audio directory submit: validate path and count audio files recursively (case-insensitive extensions like wav/WAV, mp3, flac, m4a, aac, ogg, opus, etc.).
5. Generate + Insert: recursively embed all supported audio files and batch insert into LanceDB.
6. Dedup rule: if `FilePath` already exists in `music_embeddings`, that file is skipped and not re-inserted.
7. Query: provide a query-audio directory (recursive scan) and `top_k` to retrieve nearest matches from LanceDB for each query file chunk.
10. Query UI renders a table where each row is a query chunk, and matched fields are returned as parallel `k`-length lists (file paths, start seconds, durations).
8. Short clips (<5s) are looped to 5s before Perch embedding for both ingest and query.
9. Each inserted embedding row stores chunk metadata: `start_second` and `duration_seconds`. -->
