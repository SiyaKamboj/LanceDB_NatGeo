from pathlib import Path
import tempfile

import bioacoustics_model_zoo as bmz
import lancedb
import librosa
import numpy as np
import pyarrow as pa
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

TABLE_NAME = "music_embeddings"
MUSIC_EMBEDDINGS_SCHEMA = pa.schema(
    [
        pa.field("FilePath", pa.string()),
        pa.field("start_second", pa.int32()),
        pa.field("duration_seconds", pa.int32()),
        pa.field("vector_embedding", pa.list_(pa.float32(), list_size=1280)),
    ]
)
REQUIRED_TABLE_COLUMNS = {"FilePath", "start_second", "duration_seconds", "vector_embedding"}

SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".wave",
    ".mp3",
    ".flac",
    ".m4a",
    ".aac",
    ".ogg",
    ".oga",
    ".opus",
    ".wma",
    ".aiff",
    ".aif",
    ".aifc",
    ".alac",
    ".amr",
    ".au",
    ".snd",
    ".caf",
    ".mp2",
}


class DbInitRequest(BaseModel):
    db_path: str


class AudioDirectoryRequest(BaseModel):
    audio_dir: str


class IngestRequest(BaseModel):
    db_path: str
    audio_dir: str


class QueryRequest(BaseModel):
    db_path: str
    query_audio_dir: str
    top_k: int = Field(..., ge=1, le=100)


app = FastAPI(title="LanceDB Audio Setup API")
perch_model = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_perch_model():
    global perch_model
    if perch_model is None:
        perch_model = bmz.Perch()
    return perch_model


def pad_short_clip(audio_path: str):
    target_duration_sec = 5
    samplerate = sf.info(audio_path).samplerate
    target_len = samplerate * target_duration_sec
    y, _ = librosa.load(audio_path, sr=samplerate)
    if len(y) < target_len:
        reps = int(np.ceil(target_len / len(y)))
        y = np.tile(y, reps)[:target_len]
    return np.asarray(y, dtype=np.float32), samplerate


def generate_embedding(audio_path: str):
    model = get_perch_model()
    info = sf.info(audio_path)
    duration = info.frames / info.samplerate
    if duration < 5:
        formatted_wav, sample_rate = pad_short_clip(audio_path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            sf.write(tmp.name, formatted_wav, sample_rate)
            embedding = model.embed(tmp.name)
    else:
        embedding = model.embed(audio_path)
    return np.array(embedding)


def list_audio_files(audio_dir: Path):
    return sorted(
        str(path.resolve())
        for path in audio_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )


def get_or_create_embeddings_table(db):
    table_names = db.table_names()
    if TABLE_NAME in table_names:
        table = db.open_table(TABLE_NAME)
        schema_names = set(table.schema.names)
        if not REQUIRED_TABLE_COLUMNS.issubset(schema_names):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Existing music_embeddings table has an older schema. "
                    "Please drop/recreate the table so it includes: "
                    "FilePath, start_second, duration_seconds, vector_embedding."
                ),
            )
        return table, "existing"
    return db.create_table(TABLE_NAME, schema=MUSIC_EMBEDDINGS_SCHEMA), "created"


@app.post("/api/db/init")
def init_db(payload: DbInitRequest):
    path = Path(payload.db_path).expanduser()
    existed_before = path.exists()

    try:
        db = lancedb.connect(str(path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to open LanceDB: {exc}") from exc

    _, table_status = get_or_create_embeddings_table(db)
    table_names = db.table_names()

    return {
        "db_path": str(path),
        "status": "connected" if existed_before else "created",
        "table_name": TABLE_NAME,
        "table_status": table_status,
        "table_names": table_names,
    }


@app.post("/api/audio-directory")
def set_audio_directory(payload: AudioDirectoryRequest):
    directory = Path(payload.audio_dir).expanduser()
    if not directory.exists() or not directory.is_dir():
        raise HTTPException(status_code=400, detail="Audio directory does not exist or is not a directory.")

    audio_file_count = len(list_audio_files(directory))
    return {
        "audio_dir": str(directory),
        "audio_file_count": audio_file_count,
        "supported_extensions": sorted(SUPPORTED_AUDIO_EXTENSIONS),
    }


@app.post("/api/ingest")
def ingest_audio_embeddings(payload: IngestRequest):
    db_path = Path(payload.db_path).expanduser()
    audio_dir = Path(payload.audio_dir).expanduser()

    if not audio_dir.exists() or not audio_dir.is_dir():
        raise HTTPException(status_code=400, detail="Audio directory does not exist or is not a directory.")

    try:
        db = lancedb.connect(str(db_path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to open LanceDB: {exc}") from exc

    table, _ = get_or_create_embeddings_table(db)
    audio_files = list_audio_files(audio_dir)

    existing_paths = set()
    if table.count_rows() > 0:
        df = table.to_pandas()
        if "FilePath" in df.columns:
            existing_paths = set(df["FilePath"].dropna().astype(str).tolist())

    files_to_embed = [path for path in audio_files if path not in existing_paths]

    inserted_files = 0
    skipped_existing = len(audio_files) - len(files_to_embed)
    inserted_embeddings = 0
    failed_files = []
    batch = []
    batch_size = 100

    for file_path in files_to_embed:
        try:
            embedding = generate_embedding(file_path)
        except Exception as exc:
            failed_files.append({"file_path": file_path, "error": str(exc)})
            continue

        for i in range(embedding.shape[0]):
            start_second = i * 5
            duration_seconds = 5
            batch.append(
                {
                    "FilePath": file_path,
                    "start_second": start_second,
                    "duration_seconds": duration_seconds,
                    "vector_embedding": embedding[i].tolist(),
                }
            )
            inserted_embeddings += 1
            if len(batch) >= batch_size:
                table.add(batch)
                batch.clear()

        inserted_files += 1

    if batch:
        table.add(batch)

    return {
        "db_path": str(db_path),
        "audio_dir": str(audio_dir),
        "audio_files_found": len(audio_files),
        "files_inserted": inserted_files,
        "files_skipped_existing": skipped_existing,
        "embedding_rows_inserted": inserted_embeddings,
        "failed_files_count": len(failed_files),
        "failed_files": failed_files[:25],
    }


@app.post("/api/query")
def query_audio_directory(payload: QueryRequest):
    db_path = Path(payload.db_path).expanduser()
    query_audio_dir = Path(payload.query_audio_dir).expanduser()
    top_k = payload.top_k

    if not query_audio_dir.exists() or not query_audio_dir.is_dir():
        raise HTTPException(status_code=400, detail="Query audio directory does not exist or is not a directory.")

    try:
        db = lancedb.connect(str(db_path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to open LanceDB: {exc}") from exc

    table_names = db.table_names()
    if TABLE_NAME not in table_names:
        raise HTTPException(status_code=400, detail="music_embeddings table does not exist in this database.")

    table = db.open_table(TABLE_NAME)
    if table.count_rows() == 0:
        raise HTTPException(status_code=400, detail="music_embeddings table is empty. Ingest audio first.")

    query_files = list_audio_files(query_audio_dir)
    result_table = []
    failed_files = []

    for query_file_path in query_files:
        try:
            embedding = generate_embedding(query_file_path)
        except Exception as exc:
            failed_files.append({"query_file_path": query_file_path, "error": str(exc)})
            continue

        for i in range(embedding.shape[0]):
            query_vector = embedding[i].tolist()
            df = table.search(query_vector).limit(top_k).to_pandas()

            matched_file_paths = []
            matched_start_seconds = []
            matched_duration_seconds = []
            matched_distances = []
            for _, row in df.iterrows():
                distance = row.get("_distance")
                matched_file_paths.append(str(row["FilePath"]))
                matched_start_seconds.append(
                    int(row["start_second"]) if row.get("start_second") is not None else None
                )
                matched_duration_seconds.append(
                    int(row["duration_seconds"]) if row.get("duration_seconds") is not None else None
                )
                matched_distances.append(float(distance) if distance is not None else None)

            result_table.append(
                {
                    "query_file_path": query_file_path,
                    "query_chunk_index": i,
                    "matched_file_paths": matched_file_paths,
                    "matched_start_seconds": matched_start_seconds,
                    "matched_duration_seconds": matched_duration_seconds,
                    "matched_distances": matched_distances,
                    "matches_returned": len(matched_file_paths),
                }
            )

    return {
        "db_path": str(db_path),
        "query_audio_dir": str(query_audio_dir),
        "query_files_found": len(query_files),
        "top_k": top_k,
        "result_table": result_table,
        "failed_files_count": len(failed_files),
        "failed_files": failed_files[:25],
    }
